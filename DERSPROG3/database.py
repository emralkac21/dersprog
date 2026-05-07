import sqlite3
import os

# Aktif veritabanı yolu — set_active_db() ile değiştirilebilir
_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "timetable.db")

def set_active_db(path: str):
    """Aktif veritabanını değiştir."""
    global _DB_PATH
    _DB_PATH = path

def get_active_db() -> str:
    return _DB_PATH

def get_connection():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize_db():
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            surname TEXT NOT NULL,
            branch TEXT NOT NULL,
            max_hours INTEGER DEFAULT 30
        );
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            difficulty INTEGER DEFAULT 1,
            weekly_hours INTEGER DEFAULT 1,
            block_allowed INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            section TEXT NOT NULL,
            student_count INTEGER DEFAULT 30
        );
        CREATE TABLE IF NOT EXISTS classrooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            room_type TEXT DEFAULT 'Standart',
            capacity INTEGER DEFAULT 30
        );
        CREATE TABLE IF NOT EXISTS class_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            teacher_id INTEGER,
            weekly_hours INTEGER DEFAULT 1,
            block_pattern TEXT DEFAULT '',
            max_daily INTEGER DEFAULT 2,
            FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_type TEXT NOT NULL,
            resource_id INTEGER NOT NULL,
            day INTEGER NOT NULL,
            hour INTEGER NOT NULL,
            status TEXT DEFAULT 'available',
            UNIQUE(resource_type, resource_id, day, hour)
        );
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            teacher_id INTEGER,
            classroom_id INTEGER,
            day INTEGER NOT NULL,
            hour INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS pinned_slots (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id    INTEGER,          -- NULL = tüm sınıflar
            subject_id  INTEGER NOT NULL,
            teacher_id  INTEGER,
            classroom_id INTEGER,
            day         INTEGER NOT NULL,  -- 0=Pzt, 6=Paz
            hour        INTEGER NOT NULL,
            apply_all   INTEGER DEFAULT 0, -- 1 = tüm sınıflara uygula
            FOREIGN KEY (subject_id)   REFERENCES subjects(id)   ON DELETE CASCADE,
            FOREIGN KEY (teacher_id)   REFERENCES teachers(id)   ON DELETE SET NULL,
            FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE SET NULL,
            FOREIGN KEY (class_id)     REFERENCES classes(id)    ON DELETE CASCADE
        );
    """)
    conn.commit()
    # Migration: mevcut veritabanlarına yeni sütunları ekle
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS pinned_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER, subject_id INTEGER NOT NULL,
            teacher_id INTEGER, classroom_id INTEGER,
            day INTEGER NOT NULL, hour INTEGER NOT NULL,
            apply_all INTEGER DEFAULT 0)""")
        conn.commit()
    except Exception:
        pass
    for col, dflt in [("block_pattern", "''"), ("max_daily", "2")]:
        try:
            conn.execute(f"ALTER TABLE class_subjects ADD COLUMN {col} TEXT DEFAULT {dflt}")
            conn.commit()
        except Exception:
            pass  # Sütun zaten var
    # Varsayılan ayarlar
    defaults = [
        ("school_name",    ""),
        ("principal",      ""),
        ("vice_principal", ""),
        ("academic_year",  ""),
        ("active_days",    "0,1,2,3,4"),      # Pzt-Cuma
        ("daily_hours",    "8"),               # Günde 8 ders saati
        ("bell_schedule",  ""),                # JSON: {1:"08:00-08:40", ...}
        ("language",       "tr"),             # tr | en
    ]
    for key, val in defaults:
        conn.execute("INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)", (key, val))
    conn.commit()
    conn.close()

# ─────────────────────── SETTINGS ───────────────────────
def get_settings():
    with get_connection() as conn:
        rows = conn.execute("SELECT key,value FROM settings").fetchall()
    return {r['key']: r['value'] for r in rows}

def set_setting(key, value):
    with get_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)",
                     (key, value))
        conn.commit()

# ─────────────────────── TEACHERS ───────────────────────
def get_teachers():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM teachers ORDER BY surname COLLATE NOCASE, name COLLATE NOCASE").fetchall()

def add_teacher(name, surname, branch, max_hours):
    with get_connection() as conn:
        conn.execute("INSERT INTO teachers (name,surname,branch,max_hours) VALUES (?,?,?,?)",
                     (name, surname, branch, max_hours))
        conn.commit()

def update_teacher(id, name, surname, branch, max_hours):
    with get_connection() as conn:
        conn.execute("UPDATE teachers SET name=?,surname=?,branch=?,max_hours=? WHERE id=?",
                     (name, surname, branch, max_hours, id))
        conn.commit()

def delete_teacher(id):
    with get_connection() as conn:
        conn.execute("DELETE FROM teachers WHERE id=?", (id,))
        conn.commit()

# ─────────────────────── SUBJECTS ───────────────────────
def get_subjects():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM subjects ORDER BY name COLLATE NOCASE").fetchall()

def add_subject(name, difficulty, weekly_hours, block_allowed):
    with get_connection() as conn:
        conn.execute("INSERT INTO subjects (name,difficulty,weekly_hours,block_allowed) VALUES (?,?,?,?)",
                     (name, difficulty, weekly_hours, block_allowed))
        conn.commit()

def update_subject(id, name, difficulty, weekly_hours, block_allowed):
    with get_connection() as conn:
        conn.execute("UPDATE subjects SET name=?,difficulty=?,weekly_hours=?,block_allowed=? WHERE id=?",
                     (name, difficulty, weekly_hours, block_allowed, id))
        conn.commit()

def delete_subject(id):
    with get_connection() as conn:
        conn.execute("DELETE FROM subjects WHERE id=?", (id,))
        conn.commit()

# ─────────────────────── CLASSES ────────────────────────
def get_classes():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM classes").fetchall()
    # level sayısal, section alfabetik sıralanır (9 < 10 < 11)
    return sorted(rows, key=lambda c: (
        int(c['level']) if str(c['level']).isdigit() else c['level'],
        c['section'].upper()
    ))

def add_class(level, section, student_count):
    with get_connection() as conn:
        conn.execute("INSERT INTO classes (level,section,student_count) VALUES (?,?,?)",
                     (level, section, student_count))
        conn.commit()

def update_class(id, level, section, student_count):
    with get_connection() as conn:
        conn.execute("UPDATE classes SET level=?,section=?,student_count=? WHERE id=?",
                     (level, section, student_count, id))
        conn.commit()

def delete_class(id):
    with get_connection() as conn:
        conn.execute("DELETE FROM classes WHERE id=?", (id,))
        conn.commit()

# ─────────────────────── CLASSROOMS ─────────────────────
def get_classrooms():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM classrooms ORDER BY name COLLATE NOCASE").fetchall()

def add_classroom(name, room_type, capacity):
    with get_connection() as conn:
        conn.execute("INSERT INTO classrooms (name,room_type,capacity) VALUES (?,?,?)",
                     (name, room_type, capacity))
        conn.commit()

def update_classroom(id, name, room_type, capacity):
    with get_connection() as conn:
        conn.execute("UPDATE classrooms SET name=?,room_type=?,capacity=? WHERE id=?",
                     (name, room_type, capacity, id))
        conn.commit()

def delete_classroom(id):
    with get_connection() as conn:
        conn.execute("DELETE FROM classrooms WHERE id=?", (id,))
        conn.commit()

# ─────────────────────── CLASS-SUBJECTS ─────────────────
def get_class_subjects(class_id=None):
    with get_connection() as conn:
        if class_id:
            return conn.execute("""
                SELECT cs.*, s.name as subject_name,
                       COALESCE(t.name||' '||t.surname,'—') as teacher_name
                FROM class_subjects cs
                JOIN subjects s ON cs.subject_id=s.id
                LEFT JOIN teachers t ON cs.teacher_id=t.id
                WHERE cs.class_id=? ORDER BY s.name
            """, (class_id,)).fetchall()
        return conn.execute("""
            SELECT cs.*, s.name as subject_name,
                   cl.level||'-'||cl.section as class_name,
                   COALESCE(t.name||' '||t.surname,'—') as teacher_name
            FROM class_subjects cs
            JOIN subjects s ON cs.subject_id=s.id
            JOIN classes cl ON cs.class_id=cl.id
            LEFT JOIN teachers t ON cs.teacher_id=t.id
            ORDER BY cl.level COLLATE NOCASE, cl.section COLLATE NOCASE, s.name COLLATE NOCASE
        """).fetchall()

def add_class_subject(class_id, subject_id, teacher_id, weekly_hours,
                      block_pattern='', max_daily=2):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO class_subjects
               (class_id,subject_id,teacher_id,weekly_hours,block_pattern,max_daily)
               VALUES (?,?,?,?,?,?)""",
            (class_id, subject_id, teacher_id or None,
             weekly_hours, block_pattern, max_daily))
        conn.commit()

def update_class_subject(id, teacher_id, weekly_hours,
                         block_pattern='', max_daily=2):
    with get_connection() as conn:
        conn.execute(
            """UPDATE class_subjects
               SET teacher_id=?,weekly_hours=?,block_pattern=?,max_daily=?
               WHERE id=?""",
            (teacher_id or None, weekly_hours, block_pattern, max_daily, id))
        conn.commit()

def delete_class_subject(id):
    with get_connection() as conn:
        conn.execute("DELETE FROM class_subjects WHERE id=?", (id,))
        conn.commit()

# ─────────────────────── AVAILABILITY ───────────────────
def get_availability(resource_type, resource_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT day,hour,status FROM availability WHERE resource_type=? AND resource_id=?",
            (resource_type, resource_id)).fetchall()
        return {(r['day'], r['hour']): r['status'] for r in rows}

def set_availability(resource_type, resource_id, day, hour, status):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO availability (resource_type,resource_id,day,hour,status) VALUES (?,?,?,?,?)
            ON CONFLICT(resource_type,resource_id,day,hour) DO UPDATE SET status=excluded.status
        """, (resource_type, resource_id, day, hour, status))
        conn.commit()

# ─────────────────────── TIMETABLE ──────────────────────
def get_timetable(class_id=None):
    with get_connection() as conn:
        if class_id:
            return conn.execute("""
                SELECT t.*, s.name as subject_name,
                       COALESCE(te.name||' '||te.surname,'—') as teacher_name,
                       COALESCE(cr.name,'—') as classroom_name,
                       s.difficulty
                FROM timetable t
                JOIN subjects s ON t.subject_id=s.id
                LEFT JOIN teachers te ON t.teacher_id=te.id
                LEFT JOIN classrooms cr ON t.classroom_id=cr.id
                WHERE t.class_id=?
            """, (class_id,)).fetchall()
        return conn.execute("""
            SELECT t.*, s.name as subject_name,
                   cl.level||'-'||cl.section as class_name,
                   COALESCE(te.name||' '||te.surname,'—') as teacher_name,
                   COALESCE(cr.name,'—') as classroom_name
            FROM timetable t
            JOIN subjects s ON t.subject_id=s.id
            JOIN classes cl ON t.class_id=cl.id
            LEFT JOIN teachers te ON t.teacher_id=te.id
            LEFT JOIN classrooms cr ON t.classroom_id=cr.id
        """).fetchall()

def get_timetable_for_teacher(teacher_id):
    with get_connection() as conn:
        return conn.execute("""
            SELECT t.*, s.name as subject_name,
                   cl.level||'-'||cl.section as class_name,
                   COALESCE(cr.name,'—') as classroom_name
            FROM timetable t
            JOIN subjects s ON t.subject_id=s.id
            JOIN classes cl ON t.class_id=cl.id
            LEFT JOIN classrooms cr ON t.classroom_id=cr.id
            WHERE t.teacher_id=?
        """, (teacher_id,)).fetchall()

def clear_timetable():
    with get_connection() as conn:
        conn.execute("DELETE FROM timetable")
        conn.commit()

def insert_timetable_entry(class_id, subject_id, teacher_id, classroom_id, day, hour):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO timetable (class_id,subject_id,teacher_id,classroom_id,day,hour)
            VALUES (?,?,?,?,?,?)
        """, (class_id, subject_id, teacher_id, classroom_id, day, hour))
        conn.commit()

def delete_timetable_entry(entry_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM timetable WHERE id=?", (entry_id,))
        conn.commit()

# ─────────────────────── STATS ──────────────────────────
def get_stats():
    with get_connection() as conn:
        s = {}
        s['teachers']  = conn.execute("SELECT COUNT(*) FROM teachers").fetchone()[0]
        s['subjects']  = conn.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
        s['classes']   = conn.execute("SELECT COUNT(*) FROM classes").fetchone()[0]
        s['classrooms']= conn.execute("SELECT COUNT(*) FROM classrooms").fetchone()[0]
        s['assignments']= conn.execute("SELECT COUNT(*) FROM class_subjects").fetchone()[0]
        total  = conn.execute("SELECT COALESCE(SUM(weekly_hours),0) FROM class_subjects").fetchone()[0]
        placed = conn.execute("SELECT COUNT(*) FROM timetable").fetchone()[0]
        s['total_hours']  = total
        s['placed_hours'] = placed
        s['completion']   = round((placed/total*100) if total>0 else 0, 1)
        return s

# ─────────────────────── PINNED SLOTS ───────────────────────
def get_pinned_slots():
    with get_connection() as conn:
        return conn.execute("""
            SELECT ps.*,
                   s.name  as subject_name,
                   COALESCE(t.name||' '||t.surname,'—') as teacher_name,
                   COALESCE(cr.name,'—') as classroom_name,
                   COALESCE(cl.level||'-'||cl.section,'Tüm Sınıflar') as class_name
            FROM pinned_slots ps
            JOIN subjects s    ON ps.subject_id=s.id
            LEFT JOIN teachers   t  ON ps.teacher_id=t.id
            LEFT JOIN classrooms cr ON ps.classroom_id=cr.id
            LEFT JOIN classes    cl ON ps.class_id=cl.id
            ORDER BY ps.day, ps.hour, ps.subject_id
        """).fetchall()

def add_pinned_slot(class_id, subject_id, teacher_id, classroom_id,
                    day, hour, apply_all=0):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO pinned_slots
            (class_id,subject_id,teacher_id,classroom_id,day,hour,apply_all)
            VALUES (?,?,?,?,?,?,?)
        """, (class_id or None, subject_id, teacher_id or None,
              classroom_id or None, day, hour, apply_all))
        conn.commit()

def delete_pinned_slot(slot_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM pinned_slots WHERE id=?", (slot_id,))
        conn.commit()

def get_pinned_slots_expanded():
    """
    apply_all=1 olan slotları her sınıf için ayrı kayıt olarak döndürür.
    Planlayıcı bu fonksiyonu kullanır.
    Returns: list of dicts with class_id, subject_id, teacher_id, classroom_id, day, hour
    """
    with get_connection() as conn:
        slots = [dict(r) for r in conn.execute(
            "SELECT * FROM pinned_slots").fetchall()]
        classes = [r['id'] for r in conn.execute(
            "SELECT id FROM classes").fetchall()]

    expanded = []
    for s in slots:
        if s['apply_all'] and not s['class_id']:
            for cid in classes:
                expanded.append({**s, 'class_id': cid})
        else:
            expanded.append(s)
    return expanded
