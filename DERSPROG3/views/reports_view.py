from lang import t
import customtkinter as ctk
import threading
import os
import subprocess
import sys
import database as db
from engine.export_engine import (
    export_pdf_class, export_pdf_teacher,
    export_pdf_all_classes, export_pdf_all_teachers,
    export_excel_class, export_excel_teacher,
    export_excel_all_classes, export_excel_all_teachers,
)

TEXT_PRI = "#e0e0e0"
TEXT_SEC = "#999999"
ACCENT   = "#3a7bd5"
DANGER   = "#e74c3c"
SUCCESS  = "#27ae60"
WARNING  = "#e67e22"
BORDER   = "#2a2a2a"
CARD_BG  = "#1e1e1e"

PDF_COLOR   = "#c0392b"
PDF_HOVER   = "#96281b"
EXCEL_COLOR = "#1e7e34"
EXCEL_HOVER = "#155724"


def _open_file(path):
    """Dosyayı işletim sisteminin varsayılan programıyla aç."""
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
    except Exception:
        pass


def _default_dir():
    return os.path.join(os.path.expanduser("~"), "Desktop")


class ReportsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build()
        self.refresh()

    def _build(self):
        # ── Başlık ──────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text=t("reports_title"),
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=TEXT_PRI).pack(anchor="w", padx=20, pady=(20, 2))
        ctk.CTkLabel(self,
                     text=t("reports_subtitle"),
                     font=ctk.CTkFont(size=13), text_color=TEXT_SEC
                     ).pack(anchor="w", padx=20, pady=(0, 16))

        # ── Kayıt dizini seçici ──────────────────────────────────────────────
        dir_frame = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10,
                                  border_width=1, border_color=BORDER)
        dir_frame.pack(fill="x", padx=20, pady=(0, 14))

        ctk.CTkLabel(dir_frame, text=t("save_folder"),
                      font=ctk.CTkFont(size=13, weight="bold"),
                      text_color="#ccc").pack(anchor="w", padx=16, pady=(12, 4))

        dir_row = ctk.CTkFrame(dir_frame, fg_color="transparent")
        dir_row.pack(fill="x", padx=16, pady=(0, 12))
        dir_row.columnconfigure(0, weight=1)

        self._dir_var = ctk.StringVar(value=_default_dir())
        ctk.CTkEntry(dir_row, textvariable=self._dir_var,
                      fg_color="#252525", border_color=BORDER,
                      text_color=TEXT_PRI, height=34
                      ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(dir_row, text=t("browse"), width=90, height=34,
                       fg_color="#333", hover_color="#444",
                       command=self._browse_dir
                       ).grid(row=0, column=1)

        # ── İki sütun: Sınıf | Öğretmen ─────────────────────────────────────
        cols = ctk.CTkFrame(self, fg_color="transparent")
        cols.pack(fill="both", expand=True, padx=20, pady=(0, 14))
        cols.columnconfigure([0, 1], weight=1)
        cols.rowconfigure(0, weight=1)

        self._build_class_panel(cols)
        self._build_teacher_panel(cols)

        # ── Durum çubuğu ─────────────────────────────────────────────────────
        self._status_var = ctk.StringVar(value="")
        self._status_lbl = ctk.CTkLabel(self, textvariable=self._status_var,
                                         font=ctk.CTkFont(size=12),
                                         text_color=SUCCESS)
        self._status_lbl.pack(anchor="w", padx=20, pady=(0, 10))

    # ── Sınıf paneli ──────────────────────────────────────────────────────────
    def _build_class_panel(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12,
                             border_width=1, border_color=BORDER)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        card.rowconfigure(2, weight=1)
        card.columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text=t("class_based"),
                      font=ctk.CTkFont(size=15, weight="bold"),
                      text_color=TEXT_PRI).grid(row=0, column=0, padx=16,
                                                pady=(14, 4), sticky="w")

        # Tüm sınıflar butonu
        bulk_f = ctk.CTkFrame(card, fg_color="#252525", corner_radius=8)
        bulk_f.grid(row=1, column=0, padx=16, pady=(4, 8), sticky="ew")
        ctk.CTkLabel(bulk_f, text=t("all_classes"),
                      font=ctk.CTkFont(size=12, weight="bold"),
                      text_color="#ccc").pack(side="left", padx=12, pady=10)
        bf = ctk.CTkFrame(bulk_f, fg_color="transparent")
        bf.pack(side="right", padx=8)
        ctk.CTkButton(bf, text="📕 PDF", width=80, height=30,
                       fg_color=PDF_COLOR, hover_color=PDF_HOVER,
                       font=ctk.CTkFont(size=12, weight="bold"),
                       command=lambda: self._export("pdf", "all_classes")
                       ).pack(side="left", padx=4)
        ctk.CTkButton(bf, text="📗 Excel", width=80, height=30,
                       fg_color=EXCEL_COLOR, hover_color=EXCEL_HOVER,
                       font=ctk.CTkFont(size=12, weight="bold"),
                       command=lambda: self._export("excel", "all_classes")
                       ).pack(side="left", padx=4)

        # Tek tek sınıflar
        self._class_scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self._class_scroll.grid(row=2, column=0, sticky="nsew",
                                 padx=8, pady=(0, 10))

    # ── Öğretmen paneli ───────────────────────────────────────────────────────
    def _build_teacher_panel(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12,
                             border_width=1, border_color=BORDER)
        card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        card.rowconfigure(2, weight=1)
        card.columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text=t("teacher_based"),
                      font=ctk.CTkFont(size=15, weight="bold"),
                      text_color=TEXT_PRI).grid(row=0, column=0, padx=16,
                                                pady=(14, 4), sticky="w")

        # Tüm öğretmenler butonu
        bulk_f = ctk.CTkFrame(card, fg_color="#252525", corner_radius=8)
        bulk_f.grid(row=1, column=0, padx=16, pady=(4, 8), sticky="ew")
        ctk.CTkLabel(bulk_f, text=t("all_teachers"),
                      font=ctk.CTkFont(size=12, weight="bold"),
                      text_color="#ccc").pack(side="left", padx=12, pady=10)
        bf = ctk.CTkFrame(bulk_f, fg_color="transparent")
        bf.pack(side="right", padx=8)
        ctk.CTkButton(bf, text="📕 PDF", width=80, height=30,
                       fg_color=PDF_COLOR, hover_color=PDF_HOVER,
                       font=ctk.CTkFont(size=12, weight="bold"),
                       command=lambda: self._export("pdf", "all_teachers")
                       ).pack(side="left", padx=4)
        ctk.CTkButton(bf, text="📗 Excel", width=80, height=30,
                       fg_color=EXCEL_COLOR, hover_color=EXCEL_HOVER,
                       font=ctk.CTkFont(size=12, weight="bold"),
                       command=lambda: self._export("excel", "all_teachers")
                       ).pack(side="left", padx=4)

        self._teacher_scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self._teacher_scroll.grid(row=2, column=0, sticky="nsew",
                                   padx=8, pady=(0, 10))

    # ── Veriyi yükle ──────────────────────────────────────────────────────────
    def refresh(self):
        # ── Atama istatistikleri ──────────────────────────────────────────
        with db.get_connection() as conn:
            cls_stats = {r['class_id']: dict(r) for r in conn.execute("""
                SELECT class_id, COUNT(*) as ders, SUM(weekly_hours) as saat
                FROM class_subjects GROUP BY class_id""").fetchall()}
            tch_stats = {r['teacher_id']: dict(r) for r in conn.execute("""
                SELECT teacher_id, COUNT(*) as ders, SUM(weekly_hours) as saat
                FROM class_subjects WHERE teacher_id IS NOT NULL
                GROUP BY teacher_id""").fetchall()}
            placed_cls = {r['class_id']: r['cnt'] for r in conn.execute("""
                SELECT class_id, COUNT(*) as cnt FROM timetable
                GROUP BY class_id""").fetchall()}
            placed_tch = {r['teacher_id']: r['cnt'] for r in conn.execute("""
                SELECT teacher_id, COUNT(*) as cnt FROM timetable
                WHERE teacher_id IS NOT NULL GROUP BY teacher_id""").fetchall()}

        # ── Sınıflar ─────────────────────────────────────────────────────
        for w in self._class_scroll.winfo_children():
            w.destroy()
        classes = sorted(db.get_classes(), key=lambda c: (c['level'], c['section']))
        if not classes:
            ctk.CTkLabel(self._class_scroll, text=t("no_classes_msg"),
                          text_color=TEXT_SEC, font=ctk.CTkFont(size=12)
                          ).pack(pady=20)
        for ri, cls in enumerate(classes):
            cid  = cls['id']
            st   = cls_stats.get(cid, {})
            ders = st.get('ders', 0)
            saat = st.get('saat', 0) or 0
            plcd = placed_cls.get(cid, 0)
            sub  = f"{cls['student_count']} öğrenci  •  {ders} ders  •  {saat} saat/hafta"
            if ders > 0 and plcd > 0:
                sub += f"  •  ✅ {plcd}/{saat} yerleşti"
            elif ders > 0:
                sub += "  •  ⚠ program oluşturulmadı"
            self._render_row(self._class_scroll, ri,
                              f"{cls['level']}-{cls['section']}", sub,
                              lambda c=cid: self._export("pdf",   "class", c),
                              lambda c=cid: self._export("excel", "class", c))

        # ── Öğretmenler ───────────────────────────────────────────────────
        for w in self._teacher_scroll.winfo_children():
            w.destroy()
        teachers = sorted(db.get_teachers(), key=lambda te: (te['surname'].lower(), te['name'].lower()))
        if not teachers:
            ctk.CTkLabel(self._teacher_scroll, text=t("no_teachers_msg"),
                          text_color=TEXT_SEC, font=ctk.CTkFont(size=12)
                          ).pack(pady=20)
        for ri, t in enumerate(teachers):
            tid  = t['id']
            st   = tch_stats.get(tid, {})
            ders = st.get('ders', 0)
            saat = st.get('saat', 0) or 0
            plcd = placed_tch.get(tid, 0)
            sub  = f"{t['branch']}  •  {ders} sınıf  •  {saat} saat/hafta"
            if ders > 0 and plcd > 0:
                sub += f"  •  ✅ {plcd} saat yerleşti"
            self._render_row(self._teacher_scroll, ri,
                              f"{t['name']} {t['surname']}", sub,
                              lambda tid2=tid: self._export("pdf",   "teacher", tid2),
                              lambda tid2=tid: self._export("excel", "teacher", tid2))

    def _render_row(self, parent, ri, title, subtitle, pdf_cmd, excel_cmd):
        bg = "#232323" if ri % 2 == 0 else "#1e1e1e"
        row = ctk.CTkFrame(parent, fg_color=bg, corner_radius=6, height=48)
        row.pack(fill="x", pady=2)
        row.columnconfigure(0, weight=1)

        # İsim + alt bilgi
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", padx=12, pady=6)
        ctk.CTkLabel(info, text=title,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      text_color=TEXT_PRI, anchor="w").pack(anchor="w")
        ctk.CTkLabel(info, text=subtitle,
                      font=ctk.CTkFont(size=10), text_color=TEXT_SEC,
                      anchor="w").pack(anchor="w")

        # Butonlar
        btn_f = ctk.CTkFrame(row, fg_color="transparent")
        btn_f.pack(side="right", padx=8)
        ctk.CTkButton(btn_f, text="📕 PDF", width=76, height=28,
                       fg_color=PDF_COLOR, hover_color=PDF_HOVER,
                       font=ctk.CTkFont(size=11, weight="bold"),
                       command=pdf_cmd).pack(side="left", padx=4)
        ctk.CTkButton(btn_f, text="📗 Excel", width=76, height=28,
                       fg_color=EXCEL_COLOR, hover_color=EXCEL_HOVER,
                       font=ctk.CTkFont(size=11, weight="bold"),
                       command=excel_cmd).pack(side="left", padx=4)

    # ── Dizin seçici ──────────────────────────────────────────────────────────
    def _browse_dir(self):
        from tkinter import filedialog
        d = filedialog.askdirectory(initialdir=self._dir_var.get(),
                                    title="Kayıt klasörü seçin")
        if d:
            self._dir_var.set(d)

    # ── Dışa aktarım ana işlevi ───────────────────────────────────────────────
    def _export(self, fmt, scope, resource_id=None):
        save_dir = self._dir_var.get().strip()
        if not save_dir:
            save_dir = _default_dir()
        os.makedirs(save_dir, exist_ok=True)

        # Dosya adını oluştur
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = "pdf" if fmt == "pdf" else "xlsx"

        if scope == "all_classes":
            fname = f"tum_siniflar_{ts}.{ext}"
        elif scope == "all_teachers":
            fname = f"tum_ogretmenler_{ts}.{ext}"
        elif scope == "class":
            with db.get_connection() as conn:
                cls = conn.execute("SELECT level,section FROM classes WHERE id=?",
                                   (resource_id,)).fetchone()
            cname = f"{cls['level']}-{cls['section']}" if cls else str(resource_id)
            fname = f"sinif_{cname}_{ts}.{ext}"
        else:  # teacher
            with db.get_connection() as conn:
                teacher_row= conn.execute("SELECT name,surname FROM teachers WHERE id=?",
                                 (resource_id,)).fetchone()
            tname = f"{teacher_row['name']}_{teacher_row['surname']}" if teacher_row else str(resource_id)
            fname = f"ogretmen_{tname}_{ts}.{ext}"

        output_path = os.path.join(save_dir, fname)

        self._set_status(t("generating"), WARNING)

        def run():
            try:
                if fmt == "pdf":
                    if scope == "all_classes":
                        export_pdf_all_classes(output_path)
                    elif scope == "all_teachers":
                        export_pdf_all_teachers(output_path)
                    elif scope == "class":
                        export_pdf_class(resource_id, output_path)
                    else:
                        export_pdf_teacher(resource_id, output_path)
                else:
                    if scope == "all_classes":
                        export_excel_all_classes(output_path)
                    elif scope == "all_teachers":
                        export_excel_all_teachers(output_path)
                    elif scope == "class":
                        export_excel_class(resource_id, output_path)
                    else:
                        export_excel_teacher(resource_id, output_path)

                self.after(0, self._export_done, output_path, True)
            except Exception as e:
                self.after(0, self._export_done, str(e), False)

        threading.Thread(target=run, daemon=True).start()

    def _export_done(self, result, success):
        if success:
            fname = os.path.basename(result)
            self._set_status(f"✅  Kaydedildi: {fname}", SUCCESS)
            # Dosyayı otomatik aç
            _open_file(result)
        else:
            self._set_status(f"❌  Hata: {result}", DANGER)

    def _set_status(self, msg, color):
        self._status_var.set(msg)
        self._status_lbl.configure(text_color=color)
