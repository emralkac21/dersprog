"""
lang.py  —  Çok dilli destek (TR / EN)
Kullanım:
    from lang import t, set_lang, get_lang
    t("save")  →  "Kaydet" veya "Save"
"""
import database as db

_LANG = "tr"   # varsayılan

TRANSLATIONS = {
    # ── Genel ──────────────────────────────────────────────────────────────
    "save":           {"tr": "Kaydet",          "en": "Save"},
    "cancel":         {"tr": "İptal",           "en": "Cancel"},
    "delete":         {"tr": "Sil",             "en": "Delete"},
    "edit":           {"tr": "Düzenle",         "en": "Edit"},
    "add_new":        {"tr": "Yeni Ekle",       "en": "Add New"},
    "search":         {"tr": "Ara…",            "en": "Search…"},
    "yes_delete":     {"tr": "Evet, Sil",       "en": "Yes, Delete"},
    "confirm_delete": {"tr": "Bu kaydı silmek istediğinizden emin misiniz?",
                       "en": "Are you sure you want to delete this record?"},
    "quick_add":      {"tr": "Hızlı Ekle:",     "en": "Quick Add:"},
    "saved":          {"tr": "✓ Kaydedildi",    "en": "✓ Saved"},
    "not_found":      {"tr": "Kayıt bulunamadı.", "en": "No records found."},
    "update":         {"tr": "Güncelle",        "en": "Update"},
    "edit_record":    {"tr": "Kaydı Düzenle",   "en": "Edit Record"},

    # ── Navigasyon ─────────────────────────────────────────────────────────
    "nav_dashboard":    {"tr": "Gösterge Paneli",    "en": "Dashboard"},
    "nav_data_entry":   {"tr": "VERİ GİRİŞİ",        "en": "DATA ENTRY"},
    "nav_teachers":     {"tr": "Öğretmenler",         "en": "Teachers"},
    "nav_subjects":     {"tr": "Dersler",             "en": "Subjects"},
    "nav_classes":      {"tr": "Sınıflar",            "en": "Classes"},
    "nav_classrooms":   {"tr": "Derslikler",          "en": "Classrooms"},
    "nav_planning":     {"tr": "PLANLAMA",            "en": "PLANNING"},
    "nav_assignments":  {"tr": "Ders Atamaları",      "en": "Assignments"},
    "nav_availability": {"tr": "Uygunluk Takvimi",   "en": "Availability"},
    "nav_scheduler":    {"tr": "Otomatik Planlayıcı","en": "Auto Scheduler"},
    "nav_view":         {"tr": "GÖRÜNTÜLE",           "en": "VIEW"},
    "nav_timetable":    {"tr": "Ders Programı",       "en": "Timetable"},
    "nav_reports":      {"tr": "Raporlar",            "en": "Reports"},
    "nav_settings_hdr": {"tr": "AYARLAR",             "en": "SETTINGS"},
    "nav_settings":     {"tr": "Okul Ayarları",       "en": "School Settings"},
    "change_project":   {"tr": "📂 Proje Değiştir",  "en": "📂 Change Project"},

    # ── Dashboard ──────────────────────────────────────────────────────────
    "dashboard_title":    {"tr": "📊  Gösterge Paneli",  "en": "📊  Dashboard"},
    "dashboard_subtitle": {"tr": "Sisteme genel bakış ve istatistikler",
                           "en": "System overview and statistics"},
    "card_teacher":   {"tr": "Öğretmen",   "en": "Teacher"},
    "card_subject":   {"tr": "Ders",       "en": "Subject"},
    "card_class":     {"tr": "Sınıf",      "en": "Class"},
    "card_classroom": {"tr": "Derslik",    "en": "Classroom"},
    "card_assignment":{"tr": "Atama",      "en": "Assignment"},
    "placement_progress": {"tr": "Ders Yerleştirme İlerlemesi",
                           "en": "Lesson Placement Progress"},
    "hours_placed":   {"tr": "ders saati yerleştirildi",
                       "en": "lessons placed"},

    # ── Öğretmenler ────────────────────────────────────────────────────────
    "teachers_title":    {"tr": "👨‍🏫  Öğretmenler",    "en": "👨‍🏫  Teachers"},
    "teachers_subtitle": {"tr": "Öğretmen kayıtlarını yönetin — altta hızlıca ekleyin, ✏ ile düzenleyin",
                          "en": "Manage teacher records — quick add below, ✏ to edit"},
    "col_name":      {"tr": "Ad",           "en": "Name"},
    "col_surname":   {"tr": "Soyad",        "en": "Surname"},
    "col_branch":    {"tr": "Branş",        "en": "Branch"},
    "col_max_hours": {"tr": "Maks. Saat",   "en": "Max. Hours"},
    "lbl_name":      {"tr": "Ad",           "en": "First Name"},
    "lbl_surname":   {"tr": "Soyad",        "en": "Last Name"},
    "lbl_branch":    {"tr": "Branş",        "en": "Branch"},
    "lbl_max_hours": {"tr": "Haftalık Maks. Saat", "en": "Weekly Max. Hours"},

    # ── Dersler ────────────────────────────────────────────────────────────
    "subjects_title":    {"tr": "📚  Dersler",    "en": "📚  Subjects"},
    "subjects_subtitle": {"tr": "Ders kayıtlarını yönetin — altta hızlıca ekleyin, ✏ ile düzenleyin",
                          "en": "Manage subject records — quick add below, ✏ to edit"},
    "col_subject_name":  {"tr": "Ders Adı",        "en": "Subject Name"},
    "col_difficulty":    {"tr": "Zorluk",           "en": "Difficulty"},
    "col_weekly_hours":  {"tr": "Haftalık Saat",   "en": "Weekly Hours"},
    "col_block":         {"tr": "Blok",             "en": "Block"},
    "lbl_subject_name":  {"tr": "Ders Adı",        "en": "Subject Name"},
    "lbl_difficulty":    {"tr": "Zorluk Derecesi (1-5)", "en": "Difficulty (1-5)"},
    "lbl_weekly_hours":  {"tr": "Haftalık Saat",   "en": "Weekly Hours"},
    "lbl_block":         {"tr": "Blok Ders Uygunluğu", "en": "Block Lesson"},
    "yes":               {"tr": "Evet",             "en": "Yes"},
    "no":                {"tr": "Hayır",            "en": "No"},

    # ── Sınıflar ───────────────────────────────────────────────────────────
    "classes_title":    {"tr": "🏫  Sınıflar",    "en": "🏫  Classes"},
    "classes_subtitle": {"tr": "Sınıf kayıtlarını yönetin — altta hızlıca ekleyin, ✏ ile düzenleyin",
                         "en": "Manage class records — quick add below, ✏ to edit"},
    "col_level":    {"tr": "Seviye",         "en": "Grade"},
    "col_section":  {"tr": "Şube",           "en": "Section"},
    "col_students": {"tr": "Mevcudu",        "en": "Students"},
    "lbl_level":    {"tr": "Sınıf Seviyesi", "en": "Grade Level"},
    "lbl_section":  {"tr": "Şube",           "en": "Section"},
    "lbl_students": {"tr": "Öğrenci Mevcudu","en": "Student Count"},

    # ── Derslikler ─────────────────────────────────────────────────────────
    "classrooms_title":    {"tr": "🚪  Derslikler",   "en": "🚪  Classrooms"},
    "classrooms_subtitle": {"tr": "Derslik kayıtlarını yönetin — altta hızlıca ekleyin, ✏ ile düzenleyin",
                            "en": "Manage classroom records — quick add below, ✏ to edit"},
    "col_room_name": {"tr": "Derslik Adı",  "en": "Room Name"},
    "col_room_type": {"tr": "Tür",          "en": "Type"},
    "col_capacity":  {"tr": "Kapasite",     "en": "Capacity"},
    "room_standard": {"tr": "Standart",     "en": "Standard"},
    "room_lab":      {"tr": "Laboratuvar",  "en": "Laboratory"},
    "room_gym":      {"tr": "Spor Salonu",  "en": "Gymnasium"},
    "room_conf":     {"tr": "Konferans Salonu", "en": "Conference Room"},

    # ── Atamalar ───────────────────────────────────────────────────────────
    "assignments_title":    {"tr": "📋  Ders Atamaları", "en": "📋  Assignments"},
    "assignments_subtitle": {"tr": "Sınıflara ders, öğretmen, blok düzeni ve günlük saat sınırı tanımlayın",
                             "en": "Define subject, teacher, block pattern and daily limit per class"},
    "classes_label":    {"tr": "Sınıflar",           "en": "Classes"},
    "select_class":     {"tr": "← Bir sınıf seçin",  "en": "← Select a class"},
    "assign_subject":   {"tr": "+ Ders Ata",          "en": "+ Assign Subject"},
    "bulk_assign":      {"tr": "⚡ Toplu Ata",        "en": "⚡ Bulk Assign"},
    "col_teacher":      {"tr": "Öğretmen",            "en": "Teacher"},
    "col_hours":        {"tr": "Saat",                "en": "Hours"},
    "col_block_pattern":{"tr": "Blok Düzeni",         "en": "Block Pattern"},
    "col_max_daily":    {"tr": "Maks/Gün",            "en": "Max/Day"},
    "no_assignments":   {"tr": "Bu sınıfa henüz ders atanmadı.",
                         "en": "No subjects assigned to this class yet."},
    "no_classes":       {"tr": "Henüz sınıf eklenmemiş.", "en": "No classes added yet."},
    "select_subject":   {"tr": "-- Seçin --",         "en": "-- Select --"},
    "select_teacher":   {"tr": "-- Öğretmen Seçin --","en": "-- Select Teacher --"},
    "block_suggest":    {"tr": "Öner",                "en": "Suggest"},
    "daily_max_label":  {"tr": "Günlük Maks. Saat",   "en": "Daily Max Hours"},
    "bulk_title":       {"tr": "⚡  Toplu Ders Atama","en": "⚡  Bulk Assignment"},
    "bulk_subtitle":    {"tr": "Bir ders seçin, sınıfları işaretleyin — hepsine aynı anda atanır",
                         "en": "Select a subject, check classes — assigned to all at once"},
    "select_all":       {"tr": "✓ Tümünü Seç",       "en": "✓ Select All"},
    "deselect_all":     {"tr": "✗ Tümünü Kaldır",    "en": "✗ Deselect All"},
    "do_bulk_assign":   {"tr": "⚡  Seçili Sınıflara Ata", "en": "⚡  Assign to Selected"},

    # ── Uygunluk ───────────────────────────────────────────────────────────
    "avail_title":    {"tr": "📅  Uygunluk Takvimi",   "en": "📅  Availability Calendar"},
    "avail_subtitle": {"tr": "Öğretmen ve derslik için müsaitlik saatlerini tanımlayın",
                       "en": "Define available time slots for teachers and classrooms"},
    "resource_type":  {"tr": "Kaynak Türü:",           "en": "Resource Type:"},
    "resource_label": {"tr": "Kayıt:",                 "en": "Record:"},
    "res_teacher":    {"tr": "Öğretmen",               "en": "Teacher"},
    "res_classroom":  {"tr": "Derslik",                "en": "Classroom"},
    "res_class":      {"tr": "Sınıf",                  "en": "Class"},
    "all_available":  {"tr": "✓ Tümü Müsait",         "en": "✓ All Available"},
    "status_available":    {"tr": "Müsait",            "en": "Available"},
    "status_unavailable":  {"tr": "Müsait Değil",      "en": "Unavailable"},
    "status_preferred_not":{"tr": "Tercih Edilmez",    "en": "Not Preferred"},
    "click_to_toggle":     {"tr": "(Hücreye tıklayarak durum değiştirin)",
                            "en": "(Click a cell to toggle its status)"},
    "select_record":  {"tr": "Bir kayıt seçin",        "en": "Select a record"},

    # ── Planlayıcı ─────────────────────────────────────────────────────────
    "scheduler_title":    {"tr": "⚙  Otomatik Planlayıcı", "en": "⚙  Auto Scheduler"},
    "scheduler_subtitle": {"tr": "Kısıtlamaları dikkate alarak otomatik ders programı oluşturun",
                           "en": "Generate timetable automatically respecting all constraints"},
    "sched_settings":  {"tr": "Planlama Ayarları",     "en": "Scheduling Settings"},
    "sched_run":       {"tr": "▶  Programı Oluştur",  "en": "▶  Generate Timetable"},
    "sched_clear":     {"tr": "🗑  Programı Temizle", "en": "🗑  Clear Timetable"},
    "sched_running":   {"tr": "⌛ Çalışıyor…",        "en": "⌛ Running…"},
    "sched_waiting":   {"tr": "Bekliyor…",             "en": "Waiting…"},
    "data_summary":    {"tr": "Veri Özeti",            "en": "Data Summary"},
    "log_title":       {"tr": "İşlem Günlüğü",        "en": "Operation Log"},
    "no_assignments_warn": {"tr": "⚠ Henüz ders ataması yapılmamış.",
                            "en": "⚠ No assignments found."},

    # ── Timetable ──────────────────────────────────────────────────────────
    "timetable_title":   {"tr": "🗓  Ders Programı",   "en": "🗓  Timetable"},
    "select_class_lbl":  {"tr": "Sınıf:",              "en": "Class:"},
    "select_teacher_lbl":{"tr": "Öğretmen:",           "en": "Teacher:"},
    "class_select_ph":   {"tr": "— Sınıf Seçin —",    "en": "— Select Class —"},
    "teacher_select_ph": {"tr": "— Öğretmen Seçin —", "en": "— Select Teacher —"},
    "check_conflicts":   {"tr": "🔍 Çatışma Kontrol", "en": "🔍 Check Conflicts"},
    "conflict_report":   {"tr": "🔍  Çatışma Raporu", "en": "🔍  Conflict Report"},
    "no_conflicts":      {"tr": "✅  Hiçbir çatışma bulunamadı. Program geçerli!",
                          "en": "✅  No conflicts found. Timetable is valid!"},
    "close":             {"tr": "Kapat",               "en": "Close"},
    "select_to_view":    {"tr": "Yukarıdan bir sınıf veya öğretmen seçin",
                          "en": "Select a class or teacher above"},
    "period_label":      {"tr": ". Saat",              "en": ". Period"},
    "difficulty_easy":   {"tr": "Kolay",               "en": "Easy"},
    "difficulty_med":    {"tr": "Orta",                "en": "Medium"},
    "difficulty_hard":   {"tr": "Zor",                 "en": "Hard"},
    "difficulty_vhard":  {"tr": "Çok Zor",             "en": "Very Hard"},
    "difficulty_crit":   {"tr": "Kritik",              "en": "Critical"},
    "difficulty_label":  {"tr": "Zorluk:",             "en": "Difficulty:"},

    # ── Raporlar ───────────────────────────────────────────────────────────
    "reports_title":    {"tr": "📄  Raporlar",          "en": "📄  Reports"},
    "reports_subtitle": {"tr": "Ders programlarını PDF veya Excel formatında dışa aktarın",
                         "en": "Export timetables in PDF or Excel format"},
    "save_folder":      {"tr": "💾  Kayıt Klasörü",    "en": "💾  Save Folder"},
    "browse":           {"tr": "📂 Seç",               "en": "📂 Browse"},
    "class_based":      {"tr": "🏫  Sınıf Bazlı",     "en": "🏫  Class Based"},
    "teacher_based":    {"tr": "👨‍🏫  Öğretmen Bazlı", "en": "👨‍🏫  Teacher Based"},
    "all_classes":      {"tr": "Tüm Sınıflar",         "en": "All Classes"},
    "all_teachers":     {"tr": "Tüm Öğretmenler",      "en": "All Teachers"},
    "generating":       {"tr": "⌛  Oluşturuluyor…",  "en": "⌛  Generating…"},
    "no_classes_msg":   {"tr": "Henüz sınıf eklenmemiş.", "en": "No classes added yet."},
    "no_teachers_msg":  {"tr": "Henüz öğretmen eklenmemiş.", "en": "No teachers added yet."},
    "students_label":   {"tr": "öğrenci",              "en": "students"},

    # ── Ayarlar ────────────────────────────────────────────────────────────
    "settings_title":    {"tr": "Program Ayarları",    "en": "Program Settings"},
    "settings_subtitle": {"tr": "Okul bilgileri, çalışma günleri, ders saati sayısı ve zil saatleri",
                          "en": "School info, working days, periods per day, bell schedule"},
    "sec_school_info":   {"tr": "Okul Bilgileri",      "en": "School Information"},
    "sec_work_days":     {"tr": "Çalışma Günleri",     "en": "Working Days"},
    "sec_daily_hours":   {"tr": "Günlük Ders Saati Sayısı", "en": "Periods Per Day"},
    "sec_bell":          {"tr": "Zil Saatleri",        "en": "Bell Schedule"},
    "sec_language":      {"tr": "Dil / Language",      "en": "Language / Dil"},
    "school_name_lbl":   {"tr": "Okul Adı",            "en": "School Name"},
    "academic_year_lbl": {"tr": "Öğretim Yılı",        "en": "Academic Year"},
    "principal_lbl":     {"tr": "Okul Müdürü",         "en": "Principal"},
    "vice_principal_lbl":{"tr": "Müdür Yardımcısı",    "en": "Vice Principal"},
    "days_hint":         {"tr": "Ders yapılacak günleri seçin (hafta sonu kurslar için Cmt/Paz açılabilir)",
                          "en": "Select working days (enable Sat/Sun for weekend courses)"},
    "daily_hours_q":     {"tr": "Günde kaç ders saati?", "en": "How many periods per day?"},
    "daily_hours_hint":  {"tr": "(bazı liselerde 10 saat olabilir)", "en": "(some high schools have 10)"},
    "bell_hint":         {"tr": "Her ders saati için başlangıç ve bitiş zamanlarını girin — raporlarda görünür",
                          "en": "Enter start/end times for each period — shown in reports"},
    "bell_auto":         {"tr": "Otomatik Doldur  (08:00 başlangıç, 40dk ders + 10dk teneffüs)",
                          "en": "Auto Fill  (start 08:00, 40min lesson + 10min break)"},
    "bell_col_period":   {"tr": "Saat",               "en": "Period"},
    "bell_col_start":    {"tr": "Başlangıç",          "en": "Start"},
    "bell_col_end":      {"tr": "Bitiş",              "en": "End"},
    "bell_col_preview":  {"tr": "Önizleme",           "en": "Preview"},
    "save_all_settings": {"tr": "Tüm Ayarları Kaydet","en": "Save All Settings"},
    "settings_saved":    {"tr": "Kaydedildi",         "en": "Saved"},
    "lang_label":        {"tr": "Arayüz Dili",        "en": "Interface Language"},
    "lang_restart_note": {"tr": "Dil değişikliği hemen uygulanır",
                          "en": "Language change applies immediately"},

    # ── Proje Seçici ───────────────────────────────────────────────────────
    "proj_title":      {"tr": "Ders Programı Yönetim Sistemi",
                        "en": "Timetable Management System"},
    "proj_subtitle":   {"tr": "Çalışmak istediğiniz programı seçin veya yeni bir program oluşturun",
                        "en": "Select a program to work on or create a new one"},
    "proj_new":        {"tr": "➕  Yeni Program Oluştur", "en": "➕  New Program"},
    "proj_open":       {"tr": "📂  Mevcut Dosyayı Aç",   "en": "📂  Open Existing File"},
    "proj_recent":     {"tr": "Son Projeler",             "en": "Recent Projects"},
    "proj_no_recent":  {"tr": "Henüz açılmış proje yok.\nYeni bir program oluşturun veya mevcut bir dosyayı açın.",
                        "en": "No recently opened projects.\nCreate a new program or open an existing file."},
    "proj_open_btn":   {"tr": "Aç",                       "en": "Open"},
    "proj_new_name":   {"tr": "Yeni Program Adı",         "en": "New Program Name"},
    "proj_name_ph":    {"tr": "örn: 2024-2025 Güz Dönemi","en": "e.g. 2024-2025 Fall Term"},
    "proj_create":     {"tr": "Oluştur",                  "en": "Create"},
    "proj_name_empty": {"tr": "⚠ Program adı girin",     "en": "⚠ Enter a program name"},
    "proj_last_open":  {"tr": "Son açılış:",              "en": "Last opened:"},
    "proj_save_title": {"tr": "Programı Kaydet",          "en": "Save Program"},
    "proj_open_title": {"tr": "Program Dosyası Seç",      "en": "Select Program File"},

    # ── Gün isimleri ───────────────────────────────────────────────────────
    "day_0": {"tr": "Pazartesi", "en": "Monday"},
    "day_1": {"tr": "Salı",      "en": "Tuesday"},
    "day_2": {"tr": "Çarşamba",  "en": "Wednesday"},
    "day_3": {"tr": "Perşembe",  "en": "Thursday"},
    "day_4": {"tr": "Cuma",      "en": "Friday"},
    "day_5": {"tr": "Cumartesi", "en": "Saturday"},
    "day_6": {"tr": "Pazar",     "en": "Sunday"},
    "period": {"tr": ". Saat",   "en": ". Period"},
}


def get_lang() -> str:
    return _LANG


def set_lang(lang: str):
    global _LANG
    if lang in ("tr", "en"):
        _LANG = lang
        try:
            db.set_setting("language", lang)
        except Exception:
            pass


def load_lang_from_db():
    """Uygulama başlangıcında DB'den dil ayarını yükle."""
    global _LANG
    try:
        s = db.get_settings()
        lang = s.get("language", "tr")
        if lang in ("tr", "en"):
            _LANG = lang
    except Exception:
        pass


def t(key: str, **kwargs) -> str:
    """
    Verilen anahtarın aktif dildeki karşılığını döndürür.
    Anahtar bulunamazsa anahtarın kendisini döndürür.
    kwargs ile dinamik değer yerleştirme: t("x", n=5)
    """
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    text = entry.get(_LANG, entry.get("tr", key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text


def day_name(day_index: int) -> str:
    return t(f"day_{day_index}")


def period_label(hour: int) -> str:
    """Zil saati yoksa '1. Saat' / '1. Period' döndürür."""
    import schedule_config as sc
    bell = sc.get_bell_schedule()
    if hour in bell:
        b = bell[hour]
        return f"{b.get('start','')}–{b.get('end','')}"
    return f"{hour}{t('period')}"
