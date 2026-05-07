from lang import t, set_lang, get_lang, load_lang_from_db
import customtkinter as ctk
import json
import database as db
import schedule_config as sc

TEXT_PRI = "#e0e0e0"
TEXT_SEC = "#999999"
ACCENT   = "#3a7bd5"
SUCCESS  = "#27ae60"
WARNING  = "#e67e22"
BORDER   = "#2a2a2a"
CARD_BG  = "#1e1e1e"

DAY_LABELS = {
    0: "Pazartesi", 1: "Sali",      2: "Carsamba",
    3: "Persembe",  4: "Cuma",      5: "Cumartesi", 6: "Pazar"
}

class SettingsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._vars      = {}
        self._day_vars  = {}
        self._bell_vars = {}
        self._build()
        self.refresh()

    def _build(self):
        ctk.CTkLabel(self, text="Program Ayarlari",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=TEXT_PRI).pack(anchor="w", padx=20, pady=(20, 2))
        ctk.CTkLabel(self,
                     text="Okul bilgileri, calisma gunleri, ders saati sayisi ve zil saatleri",
                     font=ctk.CTkFont(size=13), text_color=TEXT_SEC
                     ).pack(anchor="w", padx=20, pady=(0, 14))

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self._build_content(self._scroll)

    def _build_content(self, parent):
        # 1. Okul Bilgileri
        self._section(parent, "Okul Bilgileri")
        sc1 = self._card(parent)
        sc1.columnconfigure(1, weight=1)
        fields = [
            ("school_name",    "Okul Adi",          "Cinak Ilkogretim Okulu"),
            ("academic_year",  "Ogretim Yili",       "2024-2025"),
            ("principal",      "Okul Muduru",        "Ad Soyad"),
            ("vice_principal", "Mudur Yardimcisi",   "Ad Soyad"),
        ]
        for ri, (key, label, ph) in enumerate(fields):
            ctk.CTkLabel(sc1, text=label, text_color=TEXT_SEC,
                          font=ctk.CTkFont(size=12), anchor="e", width=160
                          ).grid(row=ri, column=0, padx=(16,10), pady=7, sticky="e")
            var = ctk.StringVar()
            self._vars[key] = var
            ctk.CTkEntry(sc1, textvariable=var, placeholder_text=ph,
                          fg_color="#252525", border_color=BORDER,
                          text_color=TEXT_PRI, height=34
                          ).grid(row=ri, column=1, padx=(0,16), pady=7, sticky="ew")

        # 2. Calisma Gunleri
        self._section(parent, "Calisma Gunleri")
        sc2 = self._card(parent)
        ctk.CTkLabel(sc2,
                      text="Ders yapilacak gunleri secin (hafta sonu kurslar icin Cmt/Paz acilabilir)",
                      font=ctk.CTkFont(size=11), text_color=TEXT_SEC
                      ).pack(anchor="w", padx=16, pady=(10,6))
        day_row = ctk.CTkFrame(sc2, fg_color="transparent")
        day_row.pack(fill="x", padx=16, pady=(0,12))
        for d in range(7):
            var = ctk.BooleanVar(value=(d < 5))
            self._day_vars[d] = var
            color = "#7c3aed" if d >= 5 else ACCENT
            ctk.CTkCheckBox(day_row, text=DAY_LABELS[d], variable=var,
                             font=ctk.CTkFont(size=12), text_color=TEXT_PRI,
                             fg_color=color, hover_color=color,
                             checkmark_color="#fff", width=120
                             ).pack(side="left", padx=4)

        # 3. Gunluk Saat
        self._section(parent, "Gunluk Ders Saati Sayisi")
        sc3 = self._card(parent)
        h_row = ctk.CTkFrame(sc3, fg_color="transparent")
        h_row.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(h_row, text="Gunde kac ders saati?",
                      font=ctk.CTkFont(size=12), text_color=TEXT_SEC
                      ).pack(side="left", padx=(0,12))
        self._hours_var = ctk.StringVar(value="8")
        ctk.CTkOptionMenu(h_row, variable=self._hours_var,
                          values=[str(i) for i in range(1, 13)],
                          fg_color="#252525", button_color="#333",
                          text_color=TEXT_PRI, width=80,
                          command=lambda _: self._rebuild_bell()
                          ).pack(side="left")
        ctk.CTkLabel(h_row, text="  (bazi liselerde 10 saat olabilir)",
                      font=ctk.CTkFont(size=11), text_color="#555"
                      ).pack(side="left")

        # 4. Zil Saatleri
        self._section(parent, "Zil Saatleri")
        self._bell_card = self._card(parent)
        ctk.CTkLabel(self._bell_card,
                      text="Her ders saati icin baslangic ve bitis zamanlarini girin — raporlarda gorunur",
                      font=ctk.CTkFont(size=11), text_color=TEXT_SEC
                      ).pack(anchor="w", padx=16, pady=(10,4))
        self._bell_container = ctk.CTkFrame(self._bell_card, fg_color="transparent")
        self._bell_container.pack(fill="x", padx=16, pady=(0,12))

        # 5. Dil secimi
        add_language_section(parent, on_change_callback=self._on_lang_change)

        # 6. Kaydet
        save_row = ctk.CTkFrame(parent, fg_color="transparent")
        save_row.pack(fill="x", pady=(14,4))
        self._msg_lbl = ctk.CTkLabel(save_row, text="", font=ctk.CTkFont(size=12))
        self._msg_lbl.pack(side="left")
        self._save_btn = ctk.CTkButton(save_row, text=t("save_all_settings"),
                       width=200, height=40,
                       fg_color=SUCCESS, hover_color="#1e8449",
                       font=ctk.CTkFont(size=13, weight="bold"),
                       command=self._save)
        self._save_btn.pack(side="right")

    def _section(self, p, title):
        ctk.CTkLabel(p, text=title,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      text_color="#ccc").pack(anchor="w", pady=(14,4))

    def _card(self, p):
        c = ctk.CTkFrame(p, fg_color=CARD_BG, corner_radius=12,
                          border_width=1, border_color=BORDER)
        c.pack(fill="x", pady=(0,4))
        return c

    def _rebuild_bell(self):
        for w in self._bell_container.winfo_children():
            w.destroy()
        self._bell_vars = {}
        try:
            n = int(self._hours_var.get())
        except ValueError:
            n = 8

        existing = sc.get_bell_schedule()

        # Otomatik doldur
        def auto_fill():
            from datetime import datetime, timedelta
            try:
                nn = int(self._hours_var.get())
            except ValueError:
                nn = 8
            t = datetime(2000,1,1,8,0)
            for hh in range(1, nn+1):
                s = t.strftime("%H:%M")
                e = (t + timedelta(minutes=40)).strftime("%H:%M")
                if hh in self._bell_vars:
                    self._bell_vars[hh][0].set(s)
                    self._bell_vars[hh][1].set(e)
                t += timedelta(minutes=50)

        ctk.CTkButton(self._bell_container,
                       text="Otomatik Doldur  (08:00 baslangic, 40dk ders + 10dk teneffus)",
                       height=28, fg_color="#2a2a2a", hover_color="#333",
                       text_color="#ccc", font=ctk.CTkFont(size=11),
                       command=auto_fill).pack(anchor="w", pady=(0,8))

        # Sutun basliklari
        hdr = ctk.CTkFrame(self._bell_container, fg_color="#252525", corner_radius=8)
        hdr.pack(fill="x", pady=(0,4))
        for lbl, w in [("Saat",80),("Baslangic",110),("Bitis",110),("Onizleme",150)]:
            ctk.CTkLabel(hdr, text=lbl, width=w, anchor="w",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          text_color="#888"
                          ).pack(side="left", padx=8, pady=6)

        for h in range(1, n+1):
            row = ctk.CTkFrame(self._bell_container, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{h}. Saat",
                          font=ctk.CTkFont(size=12, weight="bold"),
                          text_color=TEXT_PRI, width=80, anchor="w"
                          ).pack(side="left")
            ex = existing.get(h, {})
            sv = ctk.StringVar(value=ex.get("start",""))
            ev = ctk.StringVar(value=ex.get("end",""))
            self._bell_vars[h] = (sv, ev)
            ctk.CTkEntry(row, textvariable=sv, placeholder_text="08:00",
                          fg_color="#252525", border_color=BORDER,
                          text_color="#60a5fa", height=30, width=100
                          ).pack(side="left", padx=(0,6))
            ctk.CTkLabel(row, text="-",
                          text_color="#555", font=ctk.CTkFont(size=14)
                          ).pack(side="left", padx=2)
            ctk.CTkEntry(row, textvariable=ev, placeholder_text="08:40",
                          fg_color="#252525", border_color=BORDER,
                          text_color="#f87171", height=30, width=100
                          ).pack(side="left", padx=(6,10))
            prev = ctk.CTkLabel(row, text="", font=ctk.CTkFont(size=11),
                                 text_color="#27ae60", width=140)
            prev.pack(side="left")
            def _upd(s=sv, e=ev, l=prev):
                if s.get() and e.get():
                    l.configure(text=f"{s.get()} - {e.get()}")
                else:
                    l.configure(text="")
            sv.trace_add("write", lambda *a, s=sv, e=ev, l=prev: _upd(s,e,l))
            ev.trace_add("write", lambda *a, s=sv, e=ev, l=prev: _upd(s,e,l))
            _upd()

    def refresh(self):
        s = db.get_settings()
        for key, var in self._vars.items():
            var.set(s.get(key, ""))
        active = sc.get_active_days()
        for d, var in self._day_vars.items():
            var.set(d in active)
        self._hours_var.set(str(sc.get_daily_hours()))
        self._rebuild_bell()

    def _on_lang_change(self):
        """Dil degisince tum sabit metinleri yenile."""
        # Baslik ve altyazi guncelle
        for w in self.winfo_children():
            w.destroy()
        self._vars      = {}
        self._day_vars  = {}
        self._bell_vars = {}
        self._build()
        self.refresh()

    def _save(self):
        for key, var in self._vars.items():
            db.set_setting(key, var.get().strip())
        active = [d for d, v in self._day_vars.items() if v.get()]
        sc.save_active_days(active or [0,1,2,3,4])
        sc.save_daily_hours(int(self._hours_var.get()))
        bell = {}
        for h, (sv, ev) in self._bell_vars.items():
            s2, e2 = sv.get().strip(), ev.get().strip()
            if s2 or e2:
                bell[h] = {"start": s2, "end": e2}
        sc.save_bell_schedule(bell)
        self._msg_lbl.configure(text=t("settings_saved"), text_color=SUCCESS)
        self.after(2500, lambda: self._msg_lbl.configure(text=""))


# ── Dil değiştirici widget (SettingsView içine entegre edilir) ────────────────
def add_language_section(parent_frame, on_change_callback=None):
    """
    Ayarlar sayfasına eklenecek dil seçim kartı.
    on_change_callback(): dil değişince çağrılır.
    """
    import customtkinter as ctk
    from lang import t, set_lang, get_lang

    CARD_BG = "#1e1e1e"
    BORDER  = "#2a2a2a"
    TEXT_PRI= "#e0e0e0"
    TEXT_SEC= "#999999"
    ACCENT  = "#3a7bd5"

    ctk.CTkLabel(parent_frame, text=t("sec_language"),
                  font=ctk.CTkFont(size=14, weight="bold"),
                  text_color="#ccc").pack(anchor="w", pady=(14,4))

    card = ctk.CTkFrame(parent_frame, fg_color=CARD_BG, corner_radius=12,
                         border_width=1, border_color=BORDER)
    card.pack(fill="x", pady=(0,4))

    row = ctk.CTkFrame(card, fg_color="transparent")
    row.pack(fill="x", padx=16, pady=12)

    ctk.CTkLabel(row, text=t("lang_label"),
                  font=ctk.CTkFont(size=12), text_color=TEXT_SEC
                  ).pack(side="left", padx=(0,14))

    lang_var = ctk.StringVar(value="Türkçe" if get_lang()=="tr" else "English")

    def on_lang_select(val):
        new = "tr" if val == "Türkçe" else "en"
        set_lang(new)
        if on_change_callback:
            on_change_callback()

    ctk.CTkSegmentedButton(row,
                            values=["Türkçe", "English"],
                            variable=lang_var,
                            command=on_lang_select,
                            fg_color="#252525",
                            selected_color=ACCENT,
                            selected_hover_color="#2563ba",
                            unselected_color="#2a2a2a",
                            text_color=TEXT_PRI,
                            ).pack(side="left")

    ctk.CTkLabel(row, text=t("lang_restart_note"),
                  font=ctk.CTkFont(size=11), text_color="#555"
                  ).pack(side="left", padx=(14,0))
