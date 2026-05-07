import customtkinter as ctk
from views.base_crud import BaseCRUDView
from lang import t
import database as db

# ══════════════════════════════════════════════════════════════════
#  Öğretmenler
# ══════════════════════════════════════════════════════════════════
class TeachersView(BaseCRUDView):
    # Sınıf değişkeni yok — get_* metodları t() ile dinamik döner

    def get_title(self):     return t("teachers_title")
    def get_subtitle(self):  return t("teachers_subtitle")
    def get_columns(self):   return [
        (t("col_name"),      110),
        (t("col_surname"),   110),
        (t("col_branch"),    140),
        (t("col_max_hours"),  90),
    ]
    def get_form_fields(self): return [
        (t("lbl_name"),    "Ahmet",     "name"),
        (t("lbl_surname"), "Yılmaz",    "surname"),
        (t("lbl_branch"),  "Matematik", "branch"),
    ]
    def get_quick_fields(self): return [
        (t("lbl_name"),       "name",      90),
        (t("lbl_surname"),    "surname",  100),
        (t("lbl_branch"),     "branch",   120),
        (t("col_max_hours"),  "max_hours", 80),
    ]

    def build_form_extra(self, parent):
        ctk.CTkLabel(parent, text=t("lbl_max_hours"),
                      font=ctk.CTkFont(size=12), text_color="#999"
                      ).grid(row=self._extra_start_row, column=0,
                              padx=18, pady=(6,2), sticky="w")
        self._max_hours_var = ctk.StringVar(value="30")
        ctk.CTkEntry(parent, textvariable=self._max_hours_var,
                      placeholder_text="30",
                      fg_color="#252525", border_color="#2a2a2a",
                      text_color="#e0e0e0", height=34
                      ).grid(row=self._extra_start_row+1, column=0,
                              padx=18, sticky="ew")

    def populate_form_extras(self, row):
        self._max_hours_var.set(str(row['max_hours']))

    def collect_extras(self):
        return {'max_hours': self._max_hours_var.get()}

    def validate(self, data):
        if not data.get('name') or not data.get('surname'):
            return False, "Ad ve soyad zorunludur." if t("lbl_name")=="Ad" else "Name and surname required."
        if not data.get('branch'):
            return False, "Branş zorunludur." if t("lbl_branch")=="Branş" else "Branch required."
        try:
            int(data.get('max_hours', 30))
        except (ValueError, TypeError):
            return False, "Maks. saat sayı olmalıdır." if t("lbl_branch")=="Branş" else "Max hours must be a number."
        return True, ""

    def load_data(self):     return [dict(r) for r in db.get_teachers()]

    def on_save(self, data, edit_id):
        h = int(data.get('max_hours', 30) or 30)
        if edit_id:
            db.update_teacher(edit_id, data['name'], data['surname'], data['branch'], h)
        else:
            db.add_teacher(data['name'], data['surname'], data['branch'], h)

    def on_delete(self, item_id): db.delete_teacher(item_id)

    def row_values(self, row):
        return (row['name'], row['surname'], row['branch'], row['max_hours'])


# ══════════════════════════════════════════════════════════════════
#  Dersler
# ══════════════════════════════════════════════════════════════════
class SubjectsView(BaseCRUDView):
    def get_title(self):    return t("subjects_title")
    def get_subtitle(self): return t("subjects_subtitle")
    def get_columns(self):  return [
        (t("col_subject_name"), 160),
        (t("col_difficulty"),    80),
        (t("col_weekly_hours"), 100),
        (t("col_block"),         60),
    ]
    def get_form_fields(self): return [
        (t("lbl_subject_name"), "Matematik", "name"),
    ]
    def get_quick_fields(self): return [
        (t("lbl_subject_name"), "name",         160),
        (t("lbl_weekly_hours"), "weekly_hours", 100),
    ]

    def _diff_opts(self):  return ["1","2","3","4","5"]
    def _block_opts(self): return [t("no"), t("yes")]

    def build_form_extra(self, parent):
        r = self._extra_start_row
        ctk.CTkLabel(parent, text=t("lbl_difficulty"),
                      font=ctk.CTkFont(size=12), text_color="#999"
                      ).grid(row=r, column=0, padx=18, pady=(6,2), sticky="w")
        self._diff_var = ctk.StringVar(value="1")
        ctk.CTkOptionMenu(parent, variable=self._diff_var,
                          values=self._diff_opts(),
                          fg_color="#252525", button_color="#333", text_color="#e0e0e0"
                          ).grid(row=r+1, column=0, padx=18, sticky="ew")
        ctk.CTkLabel(parent, text=t("lbl_block"),
                      font=ctk.CTkFont(size=12), text_color="#999"
                      ).grid(row=r+2, column=0, padx=18, pady=(6,2), sticky="w")
        self._block_var = ctk.StringVar(value=t("no"))
        ctk.CTkOptionMenu(parent, variable=self._block_var,
                          values=self._block_opts(),
                          fg_color="#252525", button_color="#333", text_color="#e0e0e0"
                          ).grid(row=r+3, column=0, padx=18, sticky="ew")

    def build_quickadd_extras(self, parent):
        self._q_diff_var  = ctk.StringVar(value="1")
        self._q_block_var = ctk.StringVar(value=t("no"))
        ctk.CTkLabel(parent, text=t("col_difficulty")+":", text_color="#888",
                      font=ctk.CTkFont(size=11)).pack(side="left", padx=(4,0))
        ctk.CTkOptionMenu(parent, variable=self._q_diff_var,
                          values=self._diff_opts(), width=60,
                          fg_color="#1e2a1e", button_color="#2a4a2a", text_color="#e0e0e0"
                          ).pack(side="left", padx=(2,6))
        ctk.CTkLabel(parent, text=t("col_block")+":", text_color="#888",
                      font=ctk.CTkFont(size=11)).pack(side="left", padx=(4,0))
        ctk.CTkOptionMenu(parent, variable=self._q_block_var,
                          values=self._block_opts(), width=80,
                          fg_color="#1e2a1e", button_color="#2a4a2a", text_color="#e0e0e0"
                          ).pack(side="left", padx=(2,6))

    def populate_form_extras(self, row):
        self._diff_var.set(str(row['difficulty']))
        self._block_var.set(t("yes") if row['block_allowed'] else t("no"))

    def collect_extras(self):
        return {'difficulty': self._diff_var.get(),
                'block_allowed': self._block_var.get()}

    def collect_quick_extras(self):
        return {'difficulty': self._q_diff_var.get(),
                'block_allowed': self._q_block_var.get()}

    def reset_quick_extras(self):
        self._q_diff_var.set("1")
        self._q_block_var.set(t("no"))

    def validate(self, data):
        if not data.get('name'):
            return False, "Ders adı zorunludur." if t("lbl_branch")=="Branş" else "Subject name required."
        try:
            int(data.get('weekly_hours', 2))
        except (ValueError, TypeError):
            return False, "Haftalık saat sayı olmalıdır." if t("lbl_branch")=="Branş" else "Weekly hours must be a number."
        return True, ""

    def load_data(self):  return [dict(r) for r in db.get_subjects()]

    def on_save(self, data, edit_id):
        block = 1 if data.get('block_allowed') == t("yes") else 0
        h = int(data.get('weekly_hours', 2) or 2)
        d = int(data.get('difficulty', 1) or 1)
        if edit_id:
            db.update_subject(edit_id, data['name'], d, h, block)
        else:
            db.add_subject(data['name'], d, h, block)

    def on_delete(self, item_id): db.delete_subject(item_id)

    def row_values(self, row):
        stars = "★"*row['difficulty'] + "☆"*(5-row['difficulty'])
        return (row['name'], stars, row['weekly_hours'],
                t("yes") if row['block_allowed'] else "—")


# ══════════════════════════════════════════════════════════════════
#  Sınıflar
# ══════════════════════════════════════════════════════════════════
class ClassesView(BaseCRUDView):
    def get_title(self):    return t("classes_title")
    def get_subtitle(self): return t("classes_subtitle")
    def get_columns(self):  return [
        (t("col_level"),    80),
        (t("col_section"),  70),
        (t("col_students"), 90),
    ]
    def get_form_fields(self): return [
        (t("lbl_level"),   "9", "level"),
        (t("lbl_section"), "A", "section"),
    ]
    def get_quick_fields(self): return [
        (t("lbl_level")+"  (9)",   "level",         70),
        (t("lbl_section")+" (A)",  "section",        70),
        (t("lbl_students"),        "student_count",  80),
    ]

    def build_form_extra(self, parent):
        ctk.CTkLabel(parent, text=t("lbl_students"),
                      font=ctk.CTkFont(size=12), text_color="#999"
                      ).grid(row=self._extra_start_row, column=0,
                              padx=18, pady=(6,2), sticky="w")
        self._sc_var = ctk.StringVar(value="30")
        ctk.CTkEntry(parent, textvariable=self._sc_var,
                      fg_color="#252525", border_color="#2a2a2a",
                      text_color="#e0e0e0", height=34
                      ).grid(row=self._extra_start_row+1, column=0,
                              padx=18, sticky="ew")

    def populate_form_extras(self, row): self._sc_var.set(str(row['student_count']))
    def collect_extras(self):            return {'student_count': self._sc_var.get()}

    def validate(self, data):
        if not data.get('level') or not data.get('section'):
            return False, "Seviye ve şube zorunludur." if t("lbl_branch")=="Branş" else "Grade and section required."
        try:
            int(data.get('student_count', 30))
        except (ValueError, TypeError):
            return False, "Mevcut sayı olmalıdır." if t("lbl_branch")=="Branş" else "Student count must be a number."
        return True, ""

    def load_data(self): return [dict(r) for r in db.get_classes()]

    def on_save(self, data, edit_id):
        sc = int(data.get('student_count', 30) or 30)
        if edit_id:
            db.update_class(edit_id, data['level'], data['section'], sc)
        else:
            db.add_class(data['level'], data['section'], sc)

    def on_delete(self, item_id): db.delete_class(item_id)
    def row_values(self, row):    return (row['level'], row['section'], row['student_count'])


# ══════════════════════════════════════════════════════════════════
#  Derslikler
# ══════════════════════════════════════════════════════════════════
class ClassroomsView(BaseCRUDView):
    def get_title(self):    return t("classrooms_title")
    def get_subtitle(self): return t("classrooms_subtitle")
    def get_columns(self):  return [
        (t("col_room_name"), 120),
        (t("col_room_type"), 110),
        (t("col_capacity"),   90),
    ]
    def get_form_fields(self): return [
        (t("col_room_name"), "A101", "name"),
    ]
    def get_quick_fields(self): return [
        (t("col_room_name")+" (A101)", "name",       130),
        (t("col_capacity"),            "capacity",    80),
    ]

    def _room_types(self):
        return [t("room_standard"), t("room_lab"), t("room_gym"), t("room_conf")]

    def build_form_extra(self, parent):
        r = self._extra_start_row
        ctk.CTkLabel(parent, text=t("col_room_type"),
                      font=ctk.CTkFont(size=12), text_color="#999"
                      ).grid(row=r, column=0, padx=18, pady=(6,2), sticky="w")
        self._type_var = ctk.StringVar(value=t("room_standard"))
        ctk.CTkOptionMenu(parent, variable=self._type_var,
                          values=self._room_types(),
                          fg_color="#252525", button_color="#333", text_color="#e0e0e0"
                          ).grid(row=r+1, column=0, padx=18, sticky="ew")
        ctk.CTkLabel(parent, text=t("col_capacity"),
                      font=ctk.CTkFont(size=12), text_color="#999"
                      ).grid(row=r+2, column=0, padx=18, pady=(6,2), sticky="w")
        self._cap_var = ctk.StringVar(value="30")
        ctk.CTkEntry(parent, textvariable=self._cap_var,
                      fg_color="#252525", border_color="#2a2a2a",
                      text_color="#e0e0e0", height=34
                      ).grid(row=r+3, column=0, padx=18, sticky="ew")

    def build_quickadd_extras(self, parent):
        self._q_type_var = ctk.StringVar(value=t("room_standard"))
        ctk.CTkLabel(parent, text=t("col_room_type")+":", text_color="#888",
                      font=ctk.CTkFont(size=11)).pack(side="left", padx=(4,0))
        ctk.CTkOptionMenu(parent, variable=self._q_type_var,
                          values=self._room_types(), width=120,
                          fg_color="#1e2a1e", button_color="#2a4a2a", text_color="#e0e0e0"
                          ).pack(side="left", padx=(2,6))

    def populate_form_extras(self, row):
        # DB'deki değer TR'de saklanıyor; eşleştir
        rt = row['room_type']
        mapping = {"Standart": t("room_standard"), "Laboratuvar": t("room_lab"),
                   "Spor Salonu": t("room_gym"), "Konferans Salonu": t("room_conf")}
        self._type_var.set(mapping.get(rt, t("room_standard")))
        self._cap_var.set(str(row['capacity']))

    def collect_extras(self):
        # t() değerini DB için TR'ye çevir
        val = self._type_var.get()
        rev = {t("room_standard"): "Standart", t("room_lab"): "Laboratuvar",
               t("room_gym"): "Spor Salonu", t("room_conf"): "Konferans Salonu"}
        return {'room_type': rev.get(val, val), 'capacity': self._cap_var.get()}

    def collect_quick_extras(self):
        val = self._q_type_var.get()
        rev = {t("room_standard"): "Standart", t("room_lab"): "Laboratuvar",
               t("room_gym"): "Spor Salonu", t("room_conf"): "Konferans Salonu"}
        return {'room_type': rev.get(val, val)}

    def reset_quick_extras(self): self._q_type_var.set(t("room_standard"))

    def validate(self, data):
        if not data.get('name'):
            return False, "Derslik adı zorunludur." if t("lbl_branch")=="Branş" else "Room name required."
        try:
            int(data.get('capacity', 30))
        except (ValueError, TypeError):
            return False, "Kapasite sayı olmalıdır." if t("lbl_branch")=="Branş" else "Capacity must be a number."
        return True, ""

    def load_data(self): return [dict(r) for r in db.get_classrooms()]

    def on_save(self, data, edit_id):
        cap = int(data.get('capacity', 30) or 30)
        rt  = data.get('room_type', 'Standart')
        if edit_id:
            db.update_classroom(edit_id, data['name'], rt, cap)
        else:
            db.add_classroom(data['name'], rt, cap)

    def on_delete(self, item_id): db.delete_classroom(item_id)

    def row_values(self, row):
        mapping = {"Standart": t("room_standard"), "Laboratuvar": t("room_lab"),
                   "Spor Salonu": t("room_gym"), "Konferans Salonu": t("room_conf")}
        return (row['name'], mapping.get(row['room_type'], row['room_type']), row['capacity'])
