import customtkinter as ctk
import database as db
import schedule_config as sc
from lang import t

TEXT_PRI = "#e0e0e0"
TEXT_SEC = "#999999"
ACCENT   = "#3a7bd5"
DANGER   = "#e74c3c"
SUCCESS  = "#27ae60"
WARNING  = "#e67e22"
PURPLE   = "#7c3aed"
BORDER   = "#2a2a2a"
CARD_BG  = "#1e1e1e"
PIN_BG   = "#1a1a2e"   # sabitlenmiş slot arka planı


class PinnedSlotsView(ctk.CTkFrame):
    """
    Belirli ders saatlerini gün+saat'e sabitleme modülü.
    Örnek kullanım: Tüm sınıflarda Pazartesi 5. saat = Rehberlik
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build()
        self.refresh()

    def _build(self):
        # ── Başlık ──────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="📌  Sabitlenmiş Saatler",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=TEXT_PRI).pack(anchor="w", padx=20, pady=(20, 2))
        ctk.CTkLabel(self,
                     text="Belirli ders saatlerini gün ve saate sabitleyin — planlayıcı bu slotları önce yerleştirir ve değiştirmez",
                     font=ctk.CTkFont(size=13), text_color=TEXT_SEC
                     ).pack(anchor="w", padx=20, pady=(0, 14))

        # ── İçerik ──────────────────────────────────────────────────────────
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=0)
        content.columnconfigure(0, weight=2)
        content.columnconfigure(1, weight=3)
        content.rowconfigure(0, weight=1)

        # ── Sol: Mevcut sabitler ─────────────────────────────────────────────
        left = ctk.CTkFrame(content, fg_color=CARD_BG, corner_radius=12,
                             border_width=1, border_color=BORDER)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        # Header
        hdr = ctk.CTkFrame(left, fg_color="#252525", corner_radius=8)
        hdr.grid(row=0, column=0, sticky="ew", padx=2, pady=(2, 0))
        ctk.CTkLabel(hdr, text="📌  Tanımlı Sabitler",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      text_color="#ccc").pack(side="left", padx=14, pady=10)

        self._count_badge = ctk.CTkLabel(hdr, text="0",
                                          font=ctk.CTkFont(size=11, weight="bold"),
                                          text_color="#fff", fg_color=PURPLE,
                                          corner_radius=8, width=28, height=20)
        self._count_badge.pack(side="left", padx=4)

        ctk.CTkButton(hdr, text="🗑 Tümünü Sil", width=110, height=28,
                       fg_color="#2a2a2a", hover_color=DANGER,
                       text_color="#aaa", font=ctk.CTkFont(size=11),
                       command=self._clear_all
                       ).pack(side="right", padx=8)

        self._list_scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self._list_scroll.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)

        # Izgara önizlemesi
        preview_card = ctk.CTkFrame(left, fg_color="#1a1a1a", corner_radius=8)
        preview_card.grid(row=2, column=0, sticky="ew", padx=2, pady=(0, 2))
        ctk.CTkLabel(preview_card,
                      text="📋  Sabitlenmiş slotlar program oluşturulunca önce yerleştirilir,\n    ardından diğer dersler boş kalan saatlere atanır.",
                      font=ctk.CTkFont(size=11), text_color="#666",
                      justify="left"
                      ).pack(padx=14, pady=10)

        # ── Sağ: Yeni sabitleme formu ─────────────────────────────────────────
        right = ctk.CTkFrame(content, fg_color=CARD_BG, corner_radius=12,
                              border_width=1, border_color=BORDER)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        self._build_form(right)

    # ─────────────────────── Form ────────────────────────────────────────────
    def _build_form(self, parent):
        ctk.CTkLabel(parent, text="➕  Yeni Sabitleme Ekle",
                      font=ctk.CTkFont(size=15, weight="bold"),
                      text_color=TEXT_PRI).pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkLabel(parent,
                      text="Hangi ders, hangi gün ve saatte sabitlensin?",
                      font=ctk.CTkFont(size=12), text_color=TEXT_SEC
                      ).pack(anchor="w", padx=16, pady=(0, 12))

        form = ctk.CTkFrame(parent, fg_color="transparent")
        form.pack(fill="x", padx=16)
        form.columnconfigure(1, weight=1)

        def row(r, label, widget_fn):
            ctk.CTkLabel(form, text=label, text_color=TEXT_SEC,
                          font=ctk.CTkFont(size=12), anchor="e", width=140
                          ).grid(row=r, column=0, padx=(0, 10), pady=7, sticky="e")
            widget_fn(r)

        subjects   = sorted(db.get_subjects(),   key=lambda s: s['name'].lower())
        teachers   = sorted(db.get_teachers(),   key=lambda t: (t['surname'].lower(), t['name'].lower()))
        classes    = sorted(db.get_classes(),    key=lambda c: (c['level'], c['section']))
        classrooms = sorted(db.get_classrooms(), key=lambda r: r['name'].lower())
        days       = sc.get_active_days()
        hours      = sc.get_hours_list()

        self._subj_map = {s['name']: s['id'] for s in subjects}
        self._tchr_map = {"— Seçiniz —": None}
        self._tchr_map.update({f"{t['name']} {t['surname']} ({t['branch']})": t['id']
                               for t in teachers})
        self._cls_map  = {"Tüm Sınıflar": None}
        self._cls_map.update({f"{c['level']}-{c['section']}": c['id'] for c in classes})
        self._cr_map   = {"— Seçiniz —": None}
        self._cr_map.update({r['name']: r['id'] for r in classrooms})
        self._day_names = {d: sc.ALL_DAY_NAMES[d] for d in days}
        self._hour_names = {h: sc.get_period_label(h) for h in hours}

        # Ders
        self._subj_var = ctk.StringVar(
            value=list(self._subj_map.keys())[0] if self._subj_map else "")
        def mk_subj(r):
            ctk.CTkOptionMenu(form, variable=self._subj_var,
                              values=list(self._subj_map.keys()),
                              fg_color="#252525", button_color="#333",
                              text_color=TEXT_PRI
                              ).grid(row=r, column=1, sticky="ew")
        row(0, "Ders", mk_subj)

        # Öğretmen
        self._tchr_var = ctk.StringVar(value="— Seçiniz —")
        def mk_tchr(r):
            ctk.CTkOptionMenu(form, variable=self._tchr_var,
                              values=list(self._tchr_map.keys()),
                              fg_color="#252525", button_color="#333",
                              text_color=TEXT_PRI
                              ).grid(row=r, column=1, sticky="ew")
        row(1, "Öğretmen", mk_tchr)

        # Sınıf
        self._cls_var = ctk.StringVar(value="Tüm Sınıflar")
        def mk_cls(r):
            ctk.CTkOptionMenu(form, variable=self._cls_var,
                              values=list(self._cls_map.keys()),
                              fg_color="#252525", button_color="#333",
                              text_color=TEXT_PRI
                              ).grid(row=r, column=1, sticky="ew")
        row(2, "Sınıf / Kapsam", mk_cls)

        # Derslik
        self._cr_var = ctk.StringVar(value="— Seçiniz —")
        def mk_cr(r):
            ctk.CTkOptionMenu(form, variable=self._cr_var,
                              values=list(self._cr_map.keys()),
                              fg_color="#252525", button_color="#333",
                              text_color=TEXT_PRI
                              ).grid(row=r, column=1, sticky="ew")
        row(3, "Derslik", mk_cr)

        # Gün
        self._day_var = ctk.StringVar(
            value=list(self._day_names.values())[0] if self._day_names else "")
        def mk_day(r):
            ctk.CTkOptionMenu(form, variable=self._day_var,
                              values=list(self._day_names.values()),
                              fg_color="#252525", button_color="#333",
                              text_color="#60a5fa"
                              ).grid(row=r, column=1, sticky="ew")
        row(4, "Gün", mk_day)

        # Saat
        self._hour_var = ctk.StringVar(
            value=list(self._hour_names.values())[0] if self._hour_names else "")
        def mk_hour(r):
            ctk.CTkOptionMenu(form, variable=self._hour_var,
                              values=list(self._hour_names.values()),
                              fg_color="#252525", button_color="#333",
                              text_color="#f87171"
                              ).grid(row=r, column=1, sticky="ew")
        row(5, "Saat", mk_hour)

        # Önizleme
        self._preview_lbl = ctk.CTkLabel(form, text="",
                                          font=ctk.CTkFont(size=11),
                                          text_color="#27ae60", anchor="w")
        self._preview_lbl.grid(row=6, column=0, columnspan=2,
                                pady=(8, 0), sticky="w")

        def _update_preview(*_):
            s = self._subj_var.get()
            cls = self._cls_var.get()
            day = self._day_var.get()
            hour = self._hour_var.get()
            t = self._tchr_var.get()
            tchr_txt = "" if t == "— Seçiniz —" else f" • {t}"
            self._preview_lbl.configure(
                text=f"📌  {cls}  ←  {s}{tchr_txt}  @  {day} {hour}")

        for v in [self._subj_var, self._tchr_var, self._cls_var,
                  self._day_var, self._hour_var]:
            v.trace_add("write", _update_preview)
        _update_preview()

        # Mesaj + kaydet
        self._msg = ctk.CTkLabel(parent, text="",
                                  font=ctk.CTkFont(size=12))
        self._msg.pack(pady=(10, 0))

        ctk.CTkButton(parent, text="📌  Sabitle",
                       fg_color=PURPLE, hover_color="#5b21b6",
                       height=40, font=ctk.CTkFont(size=14, weight="bold"),
                       command=self._save
                       ).pack(fill="x", padx=16, pady=(8, 4))

        # Toplu sabitleme bölümü
        bulk_card = ctk.CTkFrame(parent, fg_color="#1a1a2e",
                                  corner_radius=8, border_width=1,
                                  border_color="#2a2a4a")
        bulk_card.pack(fill="x", padx=16, pady=(8, 16))
        ctk.CTkLabel(bulk_card,
                      text="⚡  Toplu Sabitleme: Aynı ders için birden fazla saat/gün eklemek istiyorsanız\n    her kombinasyon için ayrı ayrı 'Sabitle' butonuna basın.",
                      font=ctk.CTkFont(size=10), text_color="#666",
                      justify="left"
                      ).pack(padx=12, pady=8)

    # ─────────────────────── Kaydet ──────────────────────────────────────────
    def _save(self):
        s_id  = self._subj_map.get(self._subj_var.get())
        t_id  = self._tchr_map.get(self._tchr_var.get())
        c_id  = self._cls_map.get(self._cls_var.get())
        cr_id = self._cr_map.get(self._cr_var.get())

        # Gün → index
        day_idx = next((d for d, n in self._day_names.items()
                        if n == self._day_var.get()), None)
        # Saat → index
        hour_idx = next((h for h, n in self._hour_names.items()
                         if n == self._hour_var.get()), None)

        if s_id is None:
            self._msg.configure(text="⚠ Ders seçiniz", text_color=WARNING)
            return
        if day_idx is None or hour_idx is None:
            self._msg.configure(text="⚠ Gün ve saat seçiniz", text_color=WARNING)
            return

        apply_all = 1 if c_id is None else 0
        db.add_pinned_slot(c_id, s_id, t_id, cr_id, day_idx, hour_idx, apply_all)
        self._msg.configure(text="✅  Sabitlendi", text_color=SUCCESS)
        self.after(1800, lambda: self._msg.configure(text=""))
        self.refresh()

    # ─────────────────────── Liste ───────────────────────────────────────────
    def refresh(self):
        for w in self._list_scroll.winfo_children():
            w.destroy()

        slots = db.get_pinned_slots()
        self._count_badge.configure(text=str(len(slots)))

        if not slots:
            ctk.CTkLabel(self._list_scroll,
                          text="Henüz sabitlenmiş saat yok.\nSağ taraftaki formu kullanın.",
                          font=ctk.CTkFont(size=12), text_color=TEXT_SEC,
                          justify="center"
                          ).pack(pady=30)
            return

        for ri, s in enumerate(slots):
            s = dict(s)
            bg = "#1e1e2e" if ri % 2 == 0 else "#1a1a28"
            rf = ctk.CTkFrame(self._list_scroll, fg_color=bg,
                               corner_radius=8, height=52)
            rf.pack(fill="x", pady=2)

            day_name  = sc.ALL_DAY_NAMES.get(s['day'],   f"Gün {s['day']}")
            hour_name = sc.get_period_label(s['hour'])

            # Sol: bilgi
            info = ctk.CTkFrame(rf, fg_color="transparent")
            info.pack(side="left", padx=10, pady=6)

            ctk.CTkLabel(info,
                          text=f"📌  {s['subject_name']}",
                          font=ctk.CTkFont(size=12, weight="bold"),
                          text_color="#c084fc", anchor="w"
                          ).pack(anchor="w")

            detail = f"{s['class_name']}  •  {day_name}  {hour_name}"
            if s['teacher_name'] != '—':
                detail += f"  •  {s['teacher_name']}"
            if s['classroom_name'] != '—':
                detail += f"  •  {s['classroom_name']}"

            ctk.CTkLabel(info, text=detail,
                          font=ctk.CTkFont(size=10), text_color=TEXT_SEC,
                          anchor="w"
                          ).pack(anchor="w")

            # Sağ: rozet + sil
            right = ctk.CTkFrame(rf, fg_color="transparent")
            right.pack(side="right", padx=8)

            if s.get('apply_all'):
                ctk.CTkLabel(right, text="TÜM SINIFLAR",
                              font=ctk.CTkFont(size=9, weight="bold"),
                              text_color="#fff", fg_color=PURPLE,
                              corner_radius=6, width=88, height=18
                              ).pack(side="left", padx=(0, 6))

            sid = s['id']
            ctk.CTkButton(right, text="🗑", width=32, height=28,
                           fg_color="#2a2a2a", hover_color=DANGER,
                           text_color="#aaa",
                           command=lambda i=sid: self._delete(i)
                           ).pack(side="left")

    def _delete(self, slot_id):
        db.delete_pinned_slot(slot_id)
        self.refresh()

    def _clear_all(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Tümünü Sil")
        dlg.geometry("320x130")
        dlg.grab_set()
        dlg.configure(fg_color="#1a1a1a")
        ctk.CTkLabel(dlg, text="Tüm sabitlenmiş saatler silinsin mi?",
                      font=ctk.CTkFont(size=13), text_color=TEXT_PRI
                      ).pack(pady=20)
        bf = ctk.CTkFrame(dlg, fg_color="transparent")
        bf.pack()
        def confirm():
            for s in db.get_pinned_slots():
                db.delete_pinned_slot(s['id'])
            dlg.destroy()
            self.refresh()
        ctk.CTkButton(bf, text="Evet, Sil", fg_color=DANGER,
                       hover_color="#c0392b", width=110,
                       command=confirm).pack(side="left", padx=6)
        ctk.CTkButton(bf, text="İptal", fg_color="#333",
                       hover_color="#444", width=110,
                       command=dlg.destroy).pack(side="left", padx=6)
