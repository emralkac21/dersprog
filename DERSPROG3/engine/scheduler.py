import database as db
import random
from database import (
    get_connection, get_class_subjects, get_classrooms,
    get_availability, clear_timetable, insert_timetable_entry
)

import schedule_config as _sc

def _get_days():
    return _sc.get_active_days()

def _get_hours():
    return _sc.get_hours_list()

# Geriye dönük uyumluluk için sabit değerler (scheduler başlatılınca güncellenir)
DAYS  = [0, 1, 2, 3, 4]
HOURS = list(range(1, 9))

from schedule_config import ALL_DAY_NAMES as _ALL_NAMES
DAY_NAMES = _ALL_NAMES


def parse_pattern(pattern_str: str, weekly_hours: int) -> list:
    """
    '2+2+1' -> [2, 2, 1]
    Geçersizse haftayı 2'li bloklara böler.
    """
    pattern_str = (pattern_str or '').strip()
    if pattern_str:
        try:
            parts = [int(x) for x in pattern_str.split('+')]
            if all(p >= 1 for p in parts) and sum(parts) == weekly_hours:
                return parts
        except (ValueError, AttributeError):
            pass
    blocks = []
    remaining = weekly_hours
    while remaining > 0:
        b = min(2, remaining)
        blocks.append(b)
        remaining -= b
    return blocks


def _teacher_available(teacher_id, day, hour, avail_cache):
    if not teacher_id:
        return True
    return avail_cache.get(('teacher', teacher_id), {}).get((day, hour), 'available') == 'available'


def _classroom_available(classroom_id, day, hour, avail_cache):
    if not classroom_id:
        return True
    return avail_cache.get(('classroom', classroom_id), {}).get((day, hour), 'available') == 'available'


def _class_available(class_id, day, hour, avail_cache):
    """Sınıfın o gün/saatte müsait olup olmadığını kontrol eder."""
    if not class_id:
        return True
    return avail_cache.get(('class', class_id), {}).get((day, hour), 'available') == 'available'


def _slot_free(placed, class_id, teacher_id, classroom_id, day, hour):
    if (day, hour) in placed.get(class_id, {}):
        return False
    if teacher_id:
        for slots in placed.values():
            info = slots.get((day, hour))
            if info and info.get('teacher_id') == teacher_id:
                return False
    if classroom_id:
        for slots in placed.values():
            info = slots.get((day, hour))
            if info and info.get('classroom_id') == classroom_id:
                return False
    return True


def _find_free_classroom(placed, classroom_ids, day, hour):
    shuffled = list(classroom_ids)
    random.shuffle(shuffled)
    for cr_id in shuffled:
        busy = any(
            slots.get((day, hour), {}).get('classroom_id') == cr_id
            for slots in placed.values()
        )
        if not busy:
            return cr_id
    return None


def _daily_count(placed, class_id, subject_id, day):
    return sum(
        1 for (d, h), info in placed.get(class_id, {}).items()
        if d == day and info.get('subject_id') == subject_id
    )


def _soft_score(difficulty, day, start_h, placed, class_id):
    score = 0
    if difficulty >= 4 and start_h <= 3:
        score += 10
    if difficulty >= 4 and start_h > 5:
        score -= 6
    day_total = sum(1 for (d, _) in placed.get(class_id, {}) if d == day)
    score -= day_total * 2
    return score


class Scheduler:
    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self.log = []
        self.conflicts = []

    def _report(self, msg):
        self.log.append(msg)
        if self.progress_callback:
            self.progress_callback(msg)

    def _build_avail_cache(self):
        cache = {}
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT resource_type,resource_id,day,hour,status FROM availability"
            ).fetchall()
        for r in rows:
            key = (r['resource_type'], r['resource_id'])
            cache.setdefault(key, {})[(r['day'], r['hour'])] = r['status']
        return cache

    def _build_diff_map(self):
        with get_connection() as conn:
            return {r['id']: r['difficulty']
                    for r in conn.execute("SELECT id,difficulty FROM subjects").fetchall()}

    def _place_block(self, placed, class_id, subject_id, teacher_id,
                     classroom_ids, block_size, max_daily,
                     avail_cache, diff_map, used_days_for_subj,
                     active_days=None, active_hours=None,
                     teacher_hours_placed=None, teacher_max_hours=None):

        # Aktif gün/saatleri kullan; yoksa modül-düzeyindeki fallback
        days  = active_days  if active_days  is not None else DAYS
        hours = active_hours if active_hours is not None else HOURS

        # ── Öğretmen max saat kontrolü ──────────────────────────────────
        if teacher_id and teacher_max_hours and teacher_hours_placed is not None:
            current_placed = teacher_hours_placed.get(teacher_id, 0)
            max_h = teacher_max_hours.get(teacher_id)
            if max_h is not None and current_placed + block_size > max_h:
                return False, None, 'teacher_limit'

        difficulty = diff_map.get(subject_id, 1)

        # Gün sıralaması: kullanılmayan günler önce
        day_order = sorted(days, key=lambda d: (d in used_days_for_subj, random.random()))

        candidates = []

        for day in day_order:
            current = _daily_count(placed, class_id, subject_id, day)
            if current + block_size > max_daily:
                continue

            for start_h in hours:
                end_h = start_h + block_size - 1
                if end_h > hours[-1]:
                    break

                block_hours = list(range(start_h, start_h + block_size))

                # Uygun derslik bul (tüm blok boyunca aynı derslik)
                cr_id = None
                if classroom_ids:
                    for crid in list(classroom_ids):
                        ok = True
                        for h in block_hours:
                            if not _class_available(class_id, day, h, avail_cache):
                                ok = False
                                break
                            if not _slot_free(placed, class_id, teacher_id, crid, day, h):
                                ok = False
                                break
                            if not _teacher_available(teacher_id, day, h, avail_cache):
                                ok = False
                                break
                            if not _classroom_available(crid, day, h, avail_cache):
                                ok = False
                                break
                        if ok:
                            cr_id = crid
                            break
                    if cr_id is None:
                        continue
                else:
                    # Derslik yoksa sadece öğretmen ve sınıf çakışması kontrol et
                    ok = True
                    for h in block_hours:
                        if not _class_available(class_id, day, h, avail_cache):
                            ok = False
                            break
                        if not _slot_free(placed, class_id, teacher_id, None, day, h):
                            ok = False
                            break
                        if not _teacher_available(teacher_id, day, h, avail_cache):
                            ok = False
                            break
                    if not ok:
                        continue

                score = _soft_score(difficulty, day, start_h, placed, class_id)
                score += block_size * 2  # büyük bloklara bonus
                candidates.append((score, day, start_h, cr_id))

        if not candidates:
            return False, None, 'no_slot'

        candidates.sort(key=lambda x: -x[0])
        _, day, start_h, cr_id = random.choice(candidates[:3])
        block_hours = list(range(start_h, start_h + block_size))

        for h in block_hours:
            placed.setdefault(class_id, {})[(day, h)] = {
                'subject_id':   subject_id,
                'teacher_id':   teacher_id,
                'classroom_id': cr_id,
            }
            insert_timetable_entry(class_id, subject_id, teacher_id, cr_id, day, h)

        # Öğretmen saat sayacını güncelle
        if teacher_id and teacher_hours_placed is not None:
            teacher_hours_placed[teacher_id] = teacher_hours_placed.get(teacher_id, 0) + block_size

        return True, day, None

    def _build_teacher_max_map(self):
        """Her öğretmenin max_hours değerini döndürür."""
        with get_connection() as conn:
            return {r['id']: r['max_hours']
                    for r in conn.execute("SELECT id,max_hours FROM teachers").fetchall()
                    if r['max_hours'] is not None}

    def run(self):
        self.log = []
        self.conflicts = []
        self._report("⚙  Planlama başlatılıyor…")

        # ── Dinamik gün ve saat listesi ─────────────────────────────────
        active_days  = _get_days()
        active_hours = _get_hours()

        # ── BUG FIX 1: placed={} sabitlenmiş slotlardan ÖNCE tanımlanmalı
        placed = {}

        # ── 1. Sabitlenmiş slotları önce yerleştir ──────────────────────
        pinned = db.get_pinned_slots_expanded()
        if pinned:
            self._report(f"📌  {len(pinned)} sabitlenmiş slot yerleştiriliyor…")
        for p in pinned:
            cid  = p['class_id']
            sid  = p['subject_id']
            tid  = p['teacher_id']
            crid = p['classroom_id']
            day  = p['day']
            hour = p['hour']
            if day not in active_days or hour not in active_hours:
                self._report(f"⚠  Sabit slot ({day},{hour}) aktif takvim dışında, atlandı.")
                continue
            if not _class_available(cid, day, hour, avail_cache):
                self._report(f"⚠  Sabit slot sınıf müsait değil: sınıf#{cid} gün={day} saat={hour}, atlandı.")
                continue
            if not _slot_free(placed, cid, tid, crid, day, hour):
                self._report(f"⚠  Sabit slot çakışması: sınıf#{cid} gün={day} saat={hour}")
                continue
            placed.setdefault(cid, {})[(day, hour)] = {
                'subject_id': sid, 'teacher_id': tid, 'classroom_id': crid, 'pinned': True
            }
            from database import insert_timetable_entry
            insert_timetable_entry(cid, sid, tid, crid, day, hour)
        if pinned:
            self._report(f"📌  Sabitlenmiş slotlar tamamlandı.")

        assignments   = get_class_subjects()
        classrooms    = get_classrooms()
        classroom_ids = [r['id'] for r in classrooms] if classrooms else []

        avail_cache = self._build_avail_cache()
        diff_map    = self._build_diff_map()

        # ── BUG FIX 3: Öğretmen max_hours haritası ──────────────────────
        teacher_max_hours   = self._build_teacher_max_map()
        # Sabitlenmiş slotlardan gelen öğretmen saatlerini başlangıç sayacına ekle
        teacher_hours_placed = {}
        for cls_slots in placed.values():
            for info in cls_slots.values():
                tid = info.get('teacher_id')
                if tid:
                    teacher_hours_placed[tid] = teacher_hours_placed.get(tid, 0) + 1

        # Her atamayı bloklara dönüştür
        tasks = []
        for asgn in assignments:
            d = dict(asgn)
            blocks = parse_pattern(d.get('block_pattern', ''), d['weekly_hours'])
            for block_size in blocks:
                tasks.append((d, block_size))

        # Önce büyük bloklar, sonra zor dersler
        tasks.sort(key=lambda x: (-x[1], -diff_map.get(x[0]['subject_id'], 1)))

        expected_total = sum(a['weekly_hours'] for a in assignments)
        done = 0
        unplaced_count = 0
        used_days = {}  # (class_id, subject_id) -> set of days

        for i, (asgn_dict, block_size) in enumerate(tasks):
            class_id   = asgn_dict['class_id']
            subject_id = asgn_dict['subject_id']
            teacher_id = asgn_dict['teacher_id']
            max_daily  = int(asgn_dict.get('max_daily') or 2)

            key = (class_id, subject_id)
            used = used_days.get(key, set())

            # ── BUG FIX 2: active_days/active_hours _place_block'a iletiliyor
            success, placed_day, reason = self._place_block(
                placed, class_id, subject_id, teacher_id,
                classroom_ids, block_size, max_daily,
                avail_cache, diff_map, used,
                active_days=active_days,
                active_hours=active_hours,
                teacher_hours_placed=teacher_hours_placed,
                teacher_max_hours=teacher_max_hours)

            if success:
                done += block_size
                used_days.setdefault(key, set()).add(placed_day)
            else:
                unplaced_count += 1
                sname = asgn_dict.get('subject_name', f"Ders#{subject_id}")
                with get_connection() as conn:
                    cls = conn.execute(
                        "SELECT level,section FROM classes WHERE id=?",
                        (class_id,)).fetchone()
                cname = f"{cls['level']}-{cls['section']}" if cls else f"#{class_id}"

                # ── BUG FIX 3: Öğretmen max saat aşımını ayrıca belirt
                if reason == 'teacher_limit':
                    t_max = teacher_max_hours.get(teacher_id, '?')
                    t_placed = teacher_hours_placed.get(teacher_id, 0)
                    with get_connection() as conn2:
                        tr = conn2.execute(
                            "SELECT name,surname FROM teachers WHERE id=?",
                            (teacher_id,)).fetchone()
                    tname = f"{tr['name']} {tr['surname']}" if tr else f"Öğretmen#{teacher_id}"
                    msg = (f"⚠  Öğretmen saat limiti aşıldı: {tname} "
                           f"(max:{t_max}, yerleştirilen:{t_placed}) — "
                           f"{cname} – {sname} (blok:{block_size}) atlanamadı")
                else:
                    msg = f"⚠  Yerleştirilemedi: {cname} – {sname} (blok:{block_size})"
                self.conflicts.append(msg)
                self._report(msg)

            if self.progress_callback:
                pct = min(int((i + 1) / len(tasks) * 100), 99)
                self.progress_callback(f"__PROGRESS__{pct}")

        self.progress_callback and self.progress_callback("__PROGRESS__100")
        self._report(f"✅ Tamamlandı: {done}/{expected_total} ders saati yerleştirildi.")
        if unplaced_count:
            self._report(f"❌ {unplaced_count} blok yerleştirilemedi.")

        # ── Öğretmen saat özeti ──────────────────────────────────────────
        if teacher_hours_placed:
            self._report("─" * 40)
            self._report("📊 Öğretmen Saat Özeti:")
            with get_connection() as conn:
                teachers = {r['id']: f"{r['name']} {r['surname']}"
                            for r in conn.execute("SELECT id,name,surname FROM teachers").fetchall()}
            for tid, placed_h in sorted(teacher_hours_placed.items()):
                max_h = teacher_max_hours.get(tid)
                tname = teachers.get(tid, f"#{tid}")
                if max_h is not None:
                    status = "✅" if placed_h <= max_h else "❌ LİMİT AŞILDI"
                    self._report(f"   {tname}: {placed_h}/{max_h} saat {status}")
                else:
                    self._report(f"   {tname}: {placed_h} saat")

        return done, expected_total, self.conflicts


def validate_timetable():
    issues = []
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT t.id, t.class_id, t.subject_id, t.teacher_id,
                   t.classroom_id, t.day, t.hour,
                   cl.level||'-'||cl.section as class_name,
                   s.name as subject_name,
                   COALESCE(te.name||' '||te.surname,'—') as teacher_name,
                   COALESCE(cr.name,'—') as classroom_name
            FROM timetable t
            JOIN classes cl ON t.class_id=cl.id
            JOIN subjects s  ON t.subject_id=s.id
            LEFT JOIN teachers te  ON t.teacher_id=te.id
            LEFT JOIN classrooms cr ON t.classroom_id=cr.id
        """).fetchall()
    entries = [dict(r) for r in rows]

    for i, a in enumerate(entries):
        for j, b in enumerate(entries):
            if j <= i:
                continue
            if a['day'] != b['day'] or a['hour'] != b['hour']:
                continue
            if (a['teacher_id'] and b['teacher_id']
                    and a['teacher_id'] == b['teacher_id']):
                issues.append({'type': 'teacher',
                    'msg': (f"Öğretmen Çakışması: {a['teacher_name']} — "
                            f"{DAY_NAMES[a['day']]} {a['hour']}. saat → "
                            f"{a['class_name']} & {b['class_name']}")})
            if (a['classroom_id'] and b['classroom_id']
                    and a['classroom_id'] == b['classroom_id']):
                issues.append({'type': 'classroom',
                    'msg': (f"Derslik Çakışması: {a['classroom_name']} — "
                            f"{DAY_NAMES[a['day']]} {a['hour']}. saat → "
                            f"{a['class_name']} & {b['class_name']}")})
    return issues
