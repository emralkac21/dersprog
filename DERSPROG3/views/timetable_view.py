from lang import t
import customtkinter as ctk
import database as db
from engine.scheduler import validate_timetable, DAY_NAMES

TEXT_PRI = "#e0e0e0"
TEXT_SEC = "#999999"
ACCENT   = "#3a7bd5"
DANGER   = "#e74c3c"
SUCCESS  = "#27ae60"
WARNING  = "#e67e22"
BORDER   = "#2a2a2a"
CARD_BG  = "#1e1e1e"

import schedule_config as _sc
# Dinamik — her render'da güncellenir
DAYS  = [0, 1, 2, 3, 4]
HOURS = list(range(1, 9))

# Zorluk → renk
DIFF_COLORS = {
    1: "#1a472a",   # yeşil
    2: "#1a3a5c",   # mavi
    3: "#4a2c0a",   # turuncu
    4: "#5c1a1a",   # kırmızı
    5: "#3b1a5c",   # mor
}
DIFF_TEXT = {
    1: "#4ade80",
    2: "#60a5fa",
    3: "#fb923c",
    4: "#f87171",
    5: "#c084fc",
}


class TimetableView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._selected_class_id = None
        self._selected_class_name = ""
        self._build()
        self.refresh()

    def _build(self):
        # Başlık
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(20, 4))
        ctk.CTkLabel(hdr, text=t("timetable_title"),
                      font=ctk.CTkFont(size=22, weight="bold"),
                      text_color=TEXT_PRI).pack(side="left")

        # Araç çubuğu
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(toolbar, text=t("select_class_lbl"),
                      font=ctk.CTkFont(size=13), text_color=TEXT_SEC
                      ).pack(side="left", padx=(0, 6))

        self._class_var = ctk.StringVar(value=t("class_select_ph"))
        self._class_menu = ctk.CTkOptionMenu(
            toolbar, variable=self._class_var,
            values=["— Yükleniyor —"],
            fg_color="#252525", button_color="#333",
            text_color=TEXT_PRI, width=180,
            command=self._on_class_change)
        self._class_menu.pack(side="left", padx=(0, 14))

        ctk.CTkLabel(toolbar, text=t("select_teacher_lbl"),
                      font=ctk.CTkFont(size=13), text_color=TEXT_SEC
                      ).pack(side="left", padx=(0, 6))
        self._teacher_var = ctk.StringVar(value=t("teacher_select_ph"))
        self._teacher_menu = ctk.CTkOptionMenu(
            toolbar, variable=self._teacher_var,
            values=["— Yükleniyor —"],
            fg_color="#252525", button_color="#333",
            text_color=TEXT_PRI, width=200,
            command=self._on_teacher_change)
        self._teacher_menu.pack(side="left", padx=(0, 14))

        # Çatışma butonu
        ctk.CTkButton(toolbar, text=t("check_conflicts"),
                       width=150, height=32,
                       fg_color="#333", hover_color="#444",
                       command=self._show_conflicts
                       ).pack(side="right", padx=4)

        # İçerik: program ızgarası
        self.grid_scroll = ctk.CTkScrollableFrame(
            self, fg_color=CARD_BG, corner_radius=12)
        self.grid_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Açıklama
        legend = ctk.CTkFrame(self, fg_color="transparent")
        legend.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkLabel(legend, text=t("difficulty_label"),
                      text_color=TEXT_SEC,
                      font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 8))
        for diff, label in [(1,t("difficulty_easy")),(2,t("difficulty_med")),(3,t("difficulty_hard")),(4,t("difficulty_vhard")),(5,t("difficulty_crit"))]:
            f = ctk.CTkFrame(legend, fg_color=DIFF_COLORS[diff],
                              corner_radius=4, width=70, height=22)
            f.pack(side="left", padx=3)
            ctk.CTkLabel(f, text=label,
                          text_color=DIFF_TEXT[diff],
                          font=ctk.CTkFont(size=10)).place(relx=0.5, rely=0.5, anchor="center")

    # ─────────────────────────────────────────────────────────────────────────
    def refresh(self):
        # Sınıf listesini güncelle
        classes = sorted(db.get_classes(), key=lambda c: (c['level'], c['section']))
        self._class_map = {f"{c['level']}-{c['section']}": c['id'] for c in classes}
        class_names = [t("class_select_ph")] + list(self._class_map.keys())
        self._class_menu.configure(values=class_names)
        if self._class_var.get() not in class_names:
            self._class_var.set(t("class_select_ph"))

        # Öğretmen listesini güncelle
        teachers = sorted(db.get_teachers(), key=lambda te: (te['surname'].lower(), te['name'].lower()))
        self._teacher_map = {f"{te['name']} {te['surname']}": te['id'] for te in teachers}
        teacher_names = [t("teacher_select_ph")] + list(self._teacher_map.keys())
        self._teacher_menu.configure(values=teacher_names)

        self._render_grid()

    def _on_class_change(self, val):
        if val in self._class_map:
            self._selected_class_id = self._class_map[val]
            self._teacher_var.set(t("teacher_select_ph"))
        else:
            self._selected_class_id = None
        self._render_grid()

    def _on_teacher_change(self, val):
        if val in self._teacher_map:
            self._teacher_id = self._teacher_map[val]
            self._class_var.set(t("class_select_ph"))
            self._selected_class_id = None
        else:
            self._teacher_id = None
        self._render_grid()

    # ─────────────────────── Grid render ────────────────────────────────────
    def _render_grid(self):
        for w in self.grid_scroll.winfo_children():
            w.destroy()

        # Dinamik gün/saat
        DAYS  = _sc.get_active_days()
        HOURS = _sc.get_hours_list()
        DAY_NAMES = _sc.ALL_DAY_NAMES

        # Veriyi yükle
        if self._selected_class_id:
            rows = db.get_timetable(self._selected_class_id)
        elif hasattr(self, '_teacher_id') and self._teacher_id:
            rows = db.get_timetable_for_teacher(self._teacher_id)
        else:
            self._show_placeholder()
            return

        # slot_map: (day, hour) → row_dict
        slot_map = {(r['day'], r['hour']): dict(r) for r in rows}

        # Sabitlenmiş slotları işaretle
        pinned_keys = set()
        try:
            import database as _db
            pinned = _db.get_pinned_slots_expanded()
            view_class_id = self._selected_class_id
            view_teacher_id = getattr(self, '_teacher_id', None)
            for p in pinned:
                if view_class_id and p['class_id'] == view_class_id:
                    pinned_keys.add((p['day'], p['hour']))
                elif view_teacher_id and p['teacher_id'] == view_teacher_id:
                    pinned_keys.add((p['day'], p['hour']))
        except Exception:
            pass

        # Diff map
        with db.get_connection() as conn:
            diff_map = {r['id']: r['difficulty']
                        for r in conn.execute(
                            "SELECT id,difficulty FROM subjects").fetchall()}

        # Başlık satırı
        self.grid_scroll.columnconfigure(
            list(range(1 + len(DAYS))), weight=1)

        header_corner = ctk.CTkFrame(self.grid_scroll, fg_color="#252525",
                                      corner_radius=8, height=38, width=60)
        header_corner.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        ctk.CTkLabel(header_corner, text="Saat",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      text_color="#888").place(relx=0.5, rely=0.5, anchor="center")

        for di, day in enumerate(DAYS):
            dh = ctk.CTkFrame(self.grid_scroll, fg_color="#252525",
                               corner_radius=8, height=38)
            dh.grid(row=0, column=di+1, sticky="nsew", padx=1, pady=1)
            ctk.CTkLabel(dh, text=DAY_NAMES[day],
                          font=ctk.CTkFont(size=12, weight="bold"),
                          text_color="#ccc"
                          ).place(relx=0.5, rely=0.5, anchor="center")

        # Saat satırları
        for hi, hour in enumerate(HOURS):
            # Saat etiketi
            hl = ctk.CTkFrame(self.grid_scroll, fg_color="#252525",
                               corner_radius=8, height=64, width=60)
            hl.grid(row=hi+1, column=0, sticky="nsew", padx=1, pady=1)
            ctk.CTkLabel(hl, text=f"{hour}.",
                          font=ctk.CTkFont(size=13, weight="bold"),
                          text_color="#888"
                          ).place(relx=0.5, rely=0.5, anchor="center")

            for di, day in enumerate(DAYS):
                entry = slot_map.get((day, hour))
                diff  = diff_map.get(entry['subject_id'], 1) if entry else 0
                bg    = DIFF_COLORS.get(diff, "#252525") if entry else "#252525"
                txt_c = DIFF_TEXT.get(diff, TEXT_SEC) if entry else "#444"

                cell = ctk.CTkFrame(self.grid_scroll, fg_color=bg,
                                     corner_radius=6, height=64)
                cell.grid(row=hi+1, column=di+1, sticky="nsew",
                           padx=1, pady=1)

                is_pinned = (day, hour) in pinned_keys
                if entry:
                    if is_pinned:
                        pin_lbl = ctk.CTkLabel(cell, text="📌",
                                                font=ctk.CTkFont(size=9),
                                                text_color="#c084fc",
                                                fg_color="transparent")
                        pin_lbl.place(relx=0.02, rely=0.05)
                    ctk.CTkLabel(cell,
                                  text=entry['subject_name'],
                                  font=ctk.CTkFont(size=11, weight="bold"),
                                  text_color=txt_c, wraplength=110,
                                  justify="center"
                                  ).place(relx=0.5, rely=0.35, anchor="center")
                    # Öğretmen görünümünde sınıf adı, sınıf görünümünde öğretmen adı göster
                    if hasattr(self, '_teacher_id') and self._teacher_id:
                        sub_text  = entry.get('class_name', '')
                        sub_color = "#60a5fa"   # mavi = sınıf
                        sub_font_size = 11
                    else:
                        sub_text  = entry.get('teacher_name', '')
                        sub_color = "#aaa"
                        sub_font_size = 9
                    if sub_text and sub_text != '—':
                        ctk.CTkLabel(cell, text=sub_text,
                                      font=ctk.CTkFont(size=sub_font_size, weight="bold"),
                                      text_color=sub_color, wraplength=110,
                                      justify="center"
                                      ).place(relx=0.5, rely=0.75, anchor="center")
                    # Sil butonu (hover ile göster)
                    entry_id = entry['id']
                    del_btn = ctk.CTkButton(
                        cell, text="✕", width=18, height=18,
                        fg_color="#7a0000", hover_color=DANGER,
                        text_color="#fff", font=ctk.CTkFont(size=9),
                        corner_radius=4,
                        command=lambda eid=entry_id: self._delete_entry(eid))
                    del_btn.place(relx=1.0, rely=0.0, anchor="ne", x=-2, y=2)
                else:
                    ctk.CTkLabel(cell, text="—",
                                  font=ctk.CTkFont(size=11),
                                  text_color="#333"
                                  ).place(relx=0.5, rely=0.5, anchor="center")

    def _show_placeholder(self):
        ctk.CTkLabel(self.grid_scroll,
                      text=t("select_to_view"),
                      font=ctk.CTkFont(size=14), text_color=TEXT_SEC
                      ).pack(pady=60)

    def _delete_entry(self, entry_id):
        db.delete_timetable_entry(entry_id)
        self._render_grid()

    # ─────────────────────── Çatışma paneli ──────────────────────────────────
    def _show_conflicts(self):
        issues = validate_timetable()
        dlg = ctk.CTkToplevel(self)
        dlg.title("Çatışma Raporu")
        dlg.geometry("580x400")
        dlg.grab_set()
        dlg.configure(fg_color="#1a1a1a")

        ctk.CTkLabel(dlg, text=t("conflict_report"),
                      font=ctk.CTkFont(size=16, weight="bold"),
                      text_color=TEXT_PRI).pack(pady=(18, 8))

        scroll = ctk.CTkScrollableFrame(dlg, fg_color="#1e1e1e")
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        if not issues:
            ctk.CTkLabel(scroll,
                          text=t("no_conflicts"),
                          font=ctk.CTkFont(size=13), text_color=SUCCESS
                          ).pack(pady=30)
        else:
            for issue in issues:
                color = DANGER if issue['type'] == 'teacher' else WARNING
                f = ctk.CTkFrame(scroll, fg_color="#252525", corner_radius=8)
                f.pack(fill="x", pady=3)
                ctk.CTkLabel(f, text=issue['msg'],
                              font=ctk.CTkFont(size=12),
                              text_color=color, wraplength=500,
                              justify="left", anchor="w"
                              ).pack(padx=12, pady=8, anchor="w")

        ctk.CTkButton(dlg, text=t("close"), command=dlg.destroy,
                       fg_color="#333", hover_color="#444"
                       ).pack(pady=(0, 14))
