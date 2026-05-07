import customtkinter as ctk
import database as db
import os
import sys
from engine.scheduler import parse_pattern

TEXT_PRI = "#e0e0e0"
TEXT_SEC = "#999999"
ACCENT   = "#3a7bd5"
DANGER   = "#e74c3c"
SUCCESS  = "#27ae60"
WARNING  = "#e67e22"
BORDER   = "#2a2a2a"
CARD_BG  = "#1e1e1e"


def _suggest_pattern(hours: int) -> str:
    table = {1:"1",2:"2",3:"2+1",4:"2+2",5:"2+2+1",
             6:"2+2+2",7:"2+2+2+1",8:"2+2+2+2",
             9:"2+2+2+2+1",10:"2+2+2+2+2"}
    if hours in table:
        return table[hours]
    blocks, r = [], hours
    while r > 0:
        b = min(2, r); blocks.append(str(b)); r -= b
    return "+".join(blocks)


def _validate_pattern(pattern_str: str, weekly_hours: int):
    p = (pattern_str or '').strip()
    if not p:
        return True, ""
    try:
        parts = [int(x) for x in p.split('+')]
    except ValueError:
        return False, "Yalnizca rakam ve + kullanin. Ornek: 2+2+1"
    if any(x < 1 for x in parts):
        return False, "Blok boyutu en az 1 olmalidir."
    if sum(parts) != weekly_hours:
        return False, f"Blok toplami ({sum(parts)}) haftalik saatle ({weekly_hours}) eslesmIyor."
    if any(x > 4 for x in parts):
        return False, "Tek blok 4 saatten fazla olamaz."
    return True, ""


class AssignmentsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._selected_class_id = None
        self._build()
        self.refresh()

    def _build(self):
        ctk.CTkLabel(self, text="📋  Ders Atamalari",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=TEXT_PRI).pack(anchor="w", padx=20, pady=(20, 2))
        ctk.CTkLabel(self,
                     text="Sinif basina ders, ogretmen, blok düzeni ve günlük saat siniri tanimlayin",
                     font=ctk.CTkFont(size=13), text_color=TEXT_SEC
                     ).pack(anchor="w", padx=20, pady=(0, 14))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        # ── Sol: Sinif listesi
        left = ctk.CTkFrame(content, fg_color=CARD_BG, corner_radius=12,
                            border_width=1, border_color=BORDER)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(left, text="Siniflar",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      text_color="#aaa").pack(padx=14, pady=(12, 6), anchor="w")
        self.class_scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.class_scroll.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        # ── Sag: Tablo
        right = ctk.CTkFrame(content, fg_color=CARD_BG, corner_radius=12,
                             border_width=1, border_color=BORDER)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)

        form_row = ctk.CTkFrame(right, fg_color="#252525", corner_radius=8)
        form_row.grid(row=0, column=0, sticky="ew", padx=2, pady=(2,0))
        self.selected_class_lbl = ctk.CTkLabel(
            form_row, text="<- Bir sinif secin",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#888")
        self.selected_class_lbl.pack(side="left", padx=14, pady=10)
        ctk.CTkButton(form_row, text="⚡ Toplu Ata", width=120, height=30,
                       fg_color="#7c3aed", hover_color="#5b21b6",
                       command=self._open_bulk_dialog
                       ).pack(side="right", padx=4, pady=10)
        ctk.CTkButton(form_row, text="+ Ders Ata", width=110, height=30,
                       fg_color=ACCENT, hover_color="#2563ba",
                       command=self._open_add_dialog
                       ).pack(side="right", padx=4, pady=10)

        header = ctk.CTkFrame(right, fg_color="#252525", corner_radius=8, height=32)
        header.grid(row=1, column=0, sticky="ew", padx=2, pady=(2,0))
        for col, w in [("Ders",140),("Ogretmen",140),("Saat",55),
                       ("Blok Düzeni",120),("Maks/Gün",85),("",60)]:
            ctk.CTkLabel(header, text=col,
                          font=ctk.CTkFont(size=11, weight="bold"),
                          text_color="#aaa", anchor="w", width=w
                          ).pack(side="left", padx=(8 if col == "Ders" else 0, 0))

        self.asgn_scroll = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self.asgn_scroll.grid(row=2, column=0, sticky="nsew", padx=4, pady=4)

    def refresh(self):
        for w in self.class_scroll.winfo_children():
            w.destroy()

        # Atama istatistiklerini tek sorguda çek
        with db.get_connection() as conn:
            stats = conn.execute("""
                SELECT class_id,
                       COUNT(*)        as ders_sayisi,
                       SUM(weekly_hours) as toplam_saat
                FROM class_subjects GROUP BY class_id
            """).fetchall()
        class_stats = {r['class_id']: dict(r) for r in stats}

        classes = db.get_classes()
        for cls in classes:
            cid      = cls['id']
            name     = f"{cls['level']}-{cls['section']}"
            st       = class_stats.get(cid, {})
            ders_say = st.get('ders_sayisi', 0)
            top_saat = st.get('toplam_saat', 0) or 0
            selected = (cid == self._selected_class_id)

            card = ctk.CTkFrame(
                self.class_scroll,
                fg_color=ACCENT if selected else "#252525",
                corner_radius=8, cursor="hand2")
            card.pack(fill="x", padx=4, pady=2)
            card.columnconfigure(0, weight=1)

            # Sol: sınıf adı
            ctk.CTkLabel(card, text=name,
                          font=ctk.CTkFont(size=13, weight="bold"),
                          text_color="#ffffff" if selected else TEXT_PRI,
                          anchor="w"
                          ).grid(row=0, column=0, padx=10, pady=(6,1), sticky="w")

            # Alt: ders & saat özeti
            sub_color = "#cce4ff" if selected else TEXT_SEC
            if ders_say > 0:
                sub_txt = f"{ders_say} ders  •  {top_saat} saat/hafta"
            else:
                sub_txt = "Henüz ders atanmadı"
                sub_color = WARNING if not selected else "#ffd080"

            ctk.CTkLabel(card, text=sub_txt,
                          font=ctk.CTkFont(size=10),
                          text_color=sub_color, anchor="w"
                          ).grid(row=1, column=0, padx=10, pady=(0,6), sticky="w")

            # Sağ: rozet
            if ders_say > 0:
                badge_bg  = "#1a5c2a" if not selected else "#145220"
                badge_txt = str(ders_say)
                ctk.CTkLabel(card,
                              text=badge_txt,
                              font=ctk.CTkFont(size=11, weight="bold"),
                              text_color="#4ade80",
                              fg_color=badge_bg,
                              corner_radius=8, width=28, height=20
                              ).grid(row=0, column=1, rowspan=2,
                                     padx=10, pady=6)

            # Tüm kart tıklanabilir
            for w in card.winfo_children():
                w.bind("<Button-1>",
                       lambda e, c=cid, n=name: self._select_class(c, n))
            card.bind("<Button-1>",
                      lambda e, c=cid, n=name: self._select_class(c, n))

        if self._selected_class_id:
            self._load_assignments()

    def _select_class(self, class_id, name):
        self._selected_class_id = class_id
        self.selected_class_lbl.configure(text=f"  {name}", text_color=TEXT_PRI)
        self.refresh()

    def _load_assignments(self):
        for w in self.asgn_scroll.winfo_children():
            w.destroy()
        rows = db.get_class_subjects(self._selected_class_id)
        for ri, row in enumerate(rows):
            bg = "#232323" if ri % 2 == 0 else "#1e1e1e"
            rf = ctk.CTkFrame(self.asgn_scroll, fg_color=bg,
                               corner_radius=0, height=40)
            rf.pack(fill="x")

            pat = row['block_pattern'] or ""
            ok, _ = _validate_pattern(pat, row['weekly_hours'])
            display_pat = pat if pat else _suggest_pattern(row['weekly_hours'])
            pat_color = SUCCESS if (pat and ok) else ("#888" if not pat else WARNING)

            ctk.CTkLabel(rf, text=row['subject_name'], text_color=TEXT_PRI,
                          font=ctk.CTkFont(size=12), width=140, anchor="w"
                          ).pack(side="left", padx=8)
            ctk.CTkLabel(rf, text=row['teacher_name'], text_color=TEXT_SEC,
                          font=ctk.CTkFont(size=12), width=140, anchor="w"
                          ).pack(side="left")
            ctk.CTkLabel(rf, text=str(row['weekly_hours']), text_color=TEXT_PRI,
                          font=ctk.CTkFont(size=12, weight="bold"),
                          width=55, anchor="center").pack(side="left")
            ctk.CTkLabel(rf, text=display_pat, text_color=pat_color,
                          font=ctk.CTkFont(size=12, weight="bold"),
                          width=120, anchor="center").pack(side="left")
            ctk.CTkLabel(rf, text=f"<={row['max_daily']}/gun",
                          text_color="#60a5fa",
                          font=ctk.CTkFont(size=12), width=85, anchor="center"
                          ).pack(side="left")

            rid = row['id']
            ctk.CTkButton(rf, text="Edit", width=36, height=26,
                           fg_color="#014c8d", hover_color="#3a3a3a",
                           text_color="#aaa",
                           command=lambda r=dict(row): self._open_edit_dialog(r)
                           ).pack(side="right", padx=4)
            ctk.CTkButton(rf, text="Del", width=36, height=26,
                           fg_color="#014c8d", hover_color=DANGER,
                           text_color="#aaa",
                           command=lambda r=rid: (db.delete_class_subject(r),
                                                   self.refresh())
                           ).pack(side="right", padx=2)

        if not rows:
            ctk.CTkLabel(self.asgn_scroll, text="Bu sinifa henüz ders atanmadi.",
                          font=ctk.CTkFont(size=13), text_color=TEXT_SEC
                          ).pack(pady=30)

    def _open_add_dialog(self):
        if not self._selected_class_id:
            return
        self._assignment_dialog(edit_row=None)

    def _open_edit_dialog(self, row):
        self._assignment_dialog(edit_row=row)

    def _assignment_dialog(self, edit_row=None):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Ders Ata" if not edit_row else "Atama Düzenle")
        dlg.geometry("430x600")
        # --- GÜVENLİ İKON YÜKLEME ---
        # İkonun 'assets' klasörü içinde olduğunu belirtiyoruz
        icon_path = os.path.join("assets", "AQ2.ico")

        if os.path.exists(icon_path):
            try:
                # Bazı Windows sürümlerinde wm_iconbitmap daha kararlı çalışır
                self.after(200, lambda: dlg.iconbitmap(icon_path))
            except Exception as e:
                print(f"İkon yükleme hatası: {e}")
        else:
            print(f"Uyarı: İkon dosyası bulunamadı ({icon_path}).")
        # ----------------------------
        dlg.grab_set()
        dlg.configure(fg_color="#096059")
        dlg.resizable(False, False)

        ctk.CTkLabel(dlg, text="Ders Ata" if not edit_row else "Atama Düzenle",
                      font=ctk.CTkFont(size=16, weight="bold"),
                      text_color=TEXT_PRI).pack(pady=(20, 2))
        ctk.CTkLabel(dlg,
                      text="Blok düzeni: dersin haftalik saatlerinin günlere nasil dagilacagini belirler",
                      font=ctk.CTkFont(size=11), text_color=TEXT_SEC,
                      wraplength=380).pack(pady=(0, 10))

        subjects = sorted(db.get_subjects(), key=lambda s: s['name'].lower())
        teachers = sorted(db.get_teachers(), key=lambda t: (t['surname'].lower(), t['name'].lower()))
        subj_map = {s['name']: dict(s) for s in subjects}
        tchr_map = {"-- Secin --": None}
        tchr_map.update({f"{t['name']} {t['surname']} ({t['branch']})": t['id']
                         for t in teachers})

        form = ctk.CTkFrame(dlg, fg_color="transparent")
        form.pack(fill="x", padx=24)

        def lbl(text):
            ctk.CTkLabel(form, text=text, text_color=TEXT_SEC,
                          font=ctk.CTkFont(size=12), anchor="w"
                          ).pack(anchor="w", pady=(8, 2))

        # Ders
        lbl("Ders")
        subj_var = ctk.StringVar(
            value=edit_row['subject_name'] if edit_row
            else (list(subj_map.keys())[0] if subj_map else ""))
        subj_menu = ctk.CTkOptionMenu(form, variable=subj_var,
                          values=list(subj_map.keys()),
                          fg_color="#252525", button_color="#333",
                          text_color=TEXT_PRI,
                          command=lambda _: _update_preview())
        subj_menu.pack(fill="x")
        if edit_row:
            subj_menu.configure(state="disabled")

        # Ogretmen
        lbl("Ogretmen")
        tchr_var = ctk.StringVar(value="-- Secin --")
        if edit_row:
            for k, v in tchr_map.items():
                if v == edit_row.get('teacher_id'):
                    tchr_var.set(k); break
        ctk.CTkOptionMenu(form, variable=tchr_var,
                          values=list(tchr_map.keys()),
                          fg_color="#252525", button_color="#333",
                          text_color=TEXT_PRI).pack(fill="x")

        # Haftalik saat
        lbl("Haftalik Saat")
        hours_var = ctk.StringVar(
            value=str(edit_row['weekly_hours']) if edit_row else "2")
        hours_entry = ctk.CTkEntry(form, textvariable=hours_var,
                      fg_color="#252525", border_color=BORDER,
                      text_color=TEXT_PRI, height=34)
        hours_entry.pack(fill="x")

        # Blok düzeni
        lbl("Blok Düzeni  (örn: 2+2+1  =>  5 saatlik ders için)")
        pat_row = ctk.CTkFrame(form, fg_color="transparent")
        pat_row.pack(fill="x")
        pat_row.columnconfigure(0, weight=1)

        pattern_var = ctk.StringVar(
            value=(edit_row.get('block_pattern','') if edit_row else ""))
        pat_entry = ctk.CTkEntry(pat_row, textvariable=pattern_var,
                      fg_color="#252525", border_color=BORDER,
                      text_color="#fbbf24", height=36,
                      font=ctk.CTkFont(size=15, weight="bold"),
                      placeholder_text="Örnek: 2+2+1")
        pat_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(pat_row, text="Öner", width=64, height=36,
                       fg_color="#333", hover_color="#444", text_color="#ccc",
                       command=lambda: (pattern_var.set(
                           _suggest_pattern(_safe_int(hours_var.get(), 2))),
                           _update_preview())
                       ).grid(row=0, column=1)

        preview_lbl = ctk.CTkLabel(form, text="",
                                    font=ctk.CTkFont(size=11),
                                    text_color=SUCCESS, wraplength=360,
                                    justify="left", anchor="w")
        preview_lbl.pack(anchor="w", pady=(4, 0))

        # Maks gunluk saat
        lbl("Günlük Maks. Saat  (ayni günde bu dersten en fazla kac saat)")
        max_daily_var = ctk.StringVar(
            value=str(edit_row.get('max_daily', 2)) if edit_row else "2")
        ctk.CTkOptionMenu(form, variable=max_daily_var,
                          values=["1", "2", "3", "4"],
                          fg_color="#252525", button_color="#333",
                          text_color="#60a5fa").pack(fill="x")

        msg = ctk.CTkLabel(dlg, text="", font=ctk.CTkFont(size=12))
        msg.pack(pady=(4, 0))

        def _safe_int(val, default=2):
            try: return int(val)
            except ValueError: return default

        def _update_preview(*_):
            h = _safe_int(hours_var.get(), 0)
            if h <= 0:
                preview_lbl.configure(text="", text_color=WARNING)
                return
            p = pattern_var.get().strip()
            if not p:
                preview_lbl.configure(
                    text=f"Bos birakilan blok düzeni otomatik uygulanir: {_suggest_pattern(h)}",
                    text_color="#666")
                return
            ok, err = _validate_pattern(p, h)
            if ok:
                parts = [int(x) for x in p.split('+')]
                preview_lbl.configure(
                    text=f"OK  {len(parts)} güne dagilacak: {' | '.join(str(x)+' saat' for x in parts)}",
                    text_color=SUCCESS)
                msg.configure(text="")
            else:
                preview_lbl.configure(text=f"Hata: {err}", text_color=DANGER)

        pattern_var.trace_add("write", _update_preview)
        hours_var.trace_add("write", _update_preview)
        _update_preview()

        def save():
            h = _safe_int(hours_var.get(), 0)
            if h <= 0:
                msg.configure(text="Saat sayi olmali", text_color=WARNING)
                return
            pat = pattern_var.get().strip()
            ok, err = _validate_pattern(pat, h)
            if pat and not ok:
                msg.configure(text=err, text_color=WARNING)
                return
            s_id = subj_map.get(subj_var.get(), {}).get('id')
            t_id = tchr_map.get(tchr_var.get())
            md   = int(max_daily_var.get())
            if not s_id:
                msg.configure(text="Ders seciniz", text_color=WARNING)
                return
            if edit_row:
                db.update_class_subject(edit_row['id'], t_id, h, pat, md)
            else:
                db.add_class_subject(self._selected_class_id, s_id, t_id, h, pat, md)
            dlg.destroy()
            self.refresh()

        ctk.CTkButton(dlg, text="Kaydet", fg_color=SUCCESS,
                       hover_color="#1e8449", height=38,
                       font=ctk.CTkFont(size=13),
                       command=save).pack(padx=24, fill="x", pady=(10, 4))
        ctk.CTkButton(dlg, text="Iptal", fg_color="#2a2a2a",
                       hover_color="#333", height=34,
                       command=dlg.destroy).pack(padx=24, fill="x", pady=(0, 14))

    # ─────────────────────── Toplu Atama Dialog ──────────────────────────────
    def _open_bulk_dialog(self):
        """Bir dersi birden fazla sınıfa aynı anda ata."""
        subjects = sorted(db.get_subjects(), key=lambda s: s['name'].lower())
        teachers = sorted(db.get_teachers(), key=lambda t: (t['surname'].lower(), t['name'].lower()))
        classes  = sorted(db.get_classes(),  key=lambda c: (c['level'], c['section']))

        if not subjects:
            return
        if not classes:
            return

        dlg = ctk.CTkToplevel(self)
        dlg.title("Toplu Ders Atama")
        dlg.geometry("600x720")
        # --- GÜVENLİ İKON YÜKLEME ---
        # İkonun 'assets' klasörü içinde olduğunu belirtiyoruz
        icon_path = os.path.join("assets", "AQ2.ico")

        if os.path.exists(icon_path):
            try:
                # Bazı Windows sürümlerinde wm_iconbitmap daha kararlı çalışır
                self.after(200, lambda: dlg.iconbitmap(icon_path))
            except Exception as e:
                print(f"İkon yükleme hatası: {e}")
        else:
            print(f"Uyarı: İkon dosyası bulunamadı ({icon_path}).")
        # ----------------------------
        dlg.grab_set()
        dlg.configure(fg_color="#096059")
        dlg.resizable(False, False)

        ctk.CTkLabel(dlg, text="⚡  Toplu Ders Atama",
                      font=ctk.CTkFont(size=17, weight="bold"),
                      text_color=TEXT_PRI).pack(pady=(18, 2))
        ctk.CTkLabel(dlg,
                      text="Bir ders seçin, sınıfları işaretleyin — hepsine aynı anda atanır",
                      font=ctk.CTkFont(size=11), text_color=TEXT_SEC
                      ).pack(pady=(0, 10))

        subj_map = {s["name"]: dict(s) for s in subjects}
        tchr_map = {"-- Öğretmen Seçin --": None}
        tchr_map.update({f"{t['name']} {t['surname']} ({t['branch']})": t["id"]
                         for t in teachers})

        form = ctk.CTkFrame(dlg, fg_color="#1e1e1e", corner_radius=10)
        form.pack(fill="x", padx=20, pady=(0, 8))
        form.columnconfigure(1, weight=1)

        def row(label, widget_fn, r):
            ctk.CTkLabel(form, text=label, text_color=TEXT_SEC,
                          font=ctk.CTkFont(size=12), anchor="e", width=120
                          ).grid(row=r, column=0, padx=(14,8), pady=6, sticky="e")
            widget_fn(r)

        # Ders
        subj_var = ctk.StringVar(value=list(subj_map.keys())[0])
        def mk_subj(r):
            ctk.CTkOptionMenu(form, variable=subj_var,
                              values=list(subj_map.keys()),
                              fg_color="#252525", button_color="#333",
                              text_color=TEXT_PRI
                              ).grid(row=r, column=1, padx=(0,14), sticky="ew")
        row("Ders", mk_subj, 0)

        # Öğretmen
        tchr_var = ctk.StringVar(value="-- Öğretmen Seçin --")
        def mk_tchr(r):
            ctk.CTkOptionMenu(form, variable=tchr_var,
                              values=list(tchr_map.keys()),
                              fg_color="#252525", button_color="#333",
                              text_color=TEXT_PRI
                              ).grid(row=r, column=1, padx=(0,14), sticky="ew")
        row("Öğretmen", mk_tchr, 1)

        # Haftalık saat
        hours_var = ctk.StringVar(value="2")
        def mk_hours(r):
            ctk.CTkEntry(form, textvariable=hours_var,
                          fg_color="#252525", border_color=BORDER,
                          text_color=TEXT_PRI, height=32
                          ).grid(row=r, column=1, padx=(0,14), sticky="ew")
        row("Haftalık Saat", mk_hours, 2)

        # Blok düzeni
        pattern_var = ctk.StringVar(value="")
        def mk_pattern(r):
            pf = ctk.CTkFrame(form, fg_color="transparent")
            pf.grid(row=r, column=1, padx=(0,14), sticky="ew")
            pf.columnconfigure(0, weight=1)
            ctk.CTkEntry(pf, textvariable=pattern_var,
                          placeholder_text="örn: 2+2+1  (boş = otomatik)",
                          fg_color="#252525", border_color=BORDER,
                          text_color="#fbbf24", height=32
                          ).grid(row=0, column=0, sticky="ew", padx=(0,4))
            ctk.CTkButton(pf, text="Öner", width=56, height=32,
                           fg_color="#333", hover_color="#444",
                           text_color="#ccc",
                           command=lambda: _suggest_pat()
                           ).grid(row=0, column=1)
        row("Blok Düzeni", mk_pattern, 3)

        # Max günlük
        max_var = ctk.StringVar(value="2")
        def mk_max(r):
            ctk.CTkOptionMenu(form, variable=max_var,
                              values=["1","2","3","4"],
                              fg_color="#252525", button_color="#333",
                              text_color="#60a5fa"
                              ).grid(row=r, column=1, padx=(0,14), sticky="ew")
        row("Günlük Maks.", mk_max, 4)

        def _suggest_pat():
            from engine.scheduler import parse_pattern
            try:
                h = int(hours_var.get())
            except ValueError:
                return
            parts = parse_pattern("", h)
            pattern_var.set("+".join(str(p) for p in parts))

        # ── Sınıf seçim listesi ───────────────────────────────────────────
        ctk.CTkLabel(dlg, text="Atanacak Sınıflar",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      text_color="#ccc").pack(anchor="w", padx=22, pady=(4,2))

        # Tümünü seç / kaldır
        sel_row = ctk.CTkFrame(dlg, fg_color="transparent")
        sel_row.pack(fill="x", padx=22)
        check_vars = {}

        def _select_all():
            for v in check_vars.values():
                v.set(True)
        def _deselect_all():
            for v in check_vars.values():
                v.set(False)

        ctk.CTkButton(sel_row, text="✓ Tümünü Seç", width=120, height=26,
                       fg_color="#333", hover_color="#444",
                       command=_select_all).pack(side="left", padx=(0,6))
        ctk.CTkButton(sel_row, text="✗ Tümünü Kaldır", width=130, height=26,
                       fg_color="#333", hover_color="#444",
                       command=_deselect_all).pack(side="left")

        cls_scroll = ctk.CTkScrollableFrame(dlg, fg_color="#1e1e1e",
                                             corner_radius=8, height=180)
        cls_scroll.pack(fill="x", padx=20, pady=(6, 0))

        # Sınıfları 3 sütunlu ızgaraya yerleştir
        cls_scroll.columnconfigure([0,1,2], weight=1)
        for ci, cls in enumerate(classes):
            cid  = cls["id"]
            name = f"{cls['level']}-{cls['section']}"
            var  = ctk.BooleanVar(value=False)
            check_vars[cid] = var
            ctk.CTkCheckBox(cls_scroll, text=name, variable=var,
                             text_color=TEXT_PRI,
                             checkmark_color="#fff",
                             fg_color=ACCENT, hover_color="#2563ba"
                             ).grid(row=ci//3, column=ci%3,
                                    padx=10, pady=6, sticky="w")

        msg = ctk.CTkLabel(dlg, text="", font=ctk.CTkFont(size=12))
        msg.pack(pady=(8, 0))

        def save_bulk():
            from views.assignments import _validate_pattern
            selected = [cid for cid, v in check_vars.items() if v.get()]
            if not selected:
                msg.configure(text="⚠ En az bir sınıf seçin", text_color=WARNING)
                return
            try:
                h = int(hours_var.get())
            except ValueError:
                msg.configure(text="⚠ Saat sayı olmalı", text_color=WARNING)
                return
            pat = pattern_var.get().strip()
            ok, err = _validate_pattern(pat, h)
            if pat and not ok:
                msg.configure(text=f"⚠ {err}", text_color=WARNING)
                return
            s_id = subj_map.get(subj_var.get(), {}).get("id")
            t_id = tchr_map.get(tchr_var.get())
            md   = int(max_var.get())
            if not s_id:
                msg.configure(text="⚠ Ders seçiniz", text_color=WARNING)
                return
            for cid in selected:
                db.add_class_subject(cid, s_id, t_id, h, pat, md)
            dlg.destroy()
            self.refresh()

        ctk.CTkButton(dlg, text=f"⚡  Seçili Sınıflara Ata",
                       fg_color="#7c3aed", hover_color="#5b21b6",
                       height=40, font=ctk.CTkFont(size=13, weight="bold"),
                       command=save_bulk).pack(padx=20, fill="x", pady=(10,4))
        ctk.CTkButton(dlg, text="İptal", fg_color="#2a2a2a",
                       hover_color="#333", height=34,
                       command=dlg.destroy).pack(padx=20, fill="x", pady=(0,14))
