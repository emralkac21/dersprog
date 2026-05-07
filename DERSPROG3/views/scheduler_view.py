from lang import t
import customtkinter as ctk
import threading
import database as db
from engine.scheduler import Scheduler

TEXT_PRI = "#e0e0e0"
TEXT_SEC = "#999999"
ACCENT   = "#3a7bd5"
DANGER   = "#e74c3c"
SUCCESS  = "#27ae60"
WARNING  = "#e67e22"
BORDER   = "#2a2a2a"
CARD_BG  = "#1e1e1e"


class SchedulerView(ctk.CTkFrame):
    def __init__(self, master, on_done_callback=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_done = on_done_callback
        self._running = False
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text=t("scheduler_title"),
                      font=ctk.CTkFont(size=22, weight="bold"),
                      text_color=TEXT_PRI).pack(anchor="w", padx=20, pady=(20, 2))
        ctk.CTkLabel(self, text=t("scheduler_subtitle"),
                      font=ctk.CTkFont(size=13), text_color=TEXT_SEC
                      ).pack(anchor="w", padx=20, pady=(0, 18))

        # Üst: kontroller + özet
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(0, 12))
        top.columnconfigure([0, 1], weight=1)

        # ── Sol: Kontrol kartı ──────────────────────────────────────────────
        ctrl = ctk.CTkFrame(top, fg_color=CARD_BG, corner_radius=12,
                             border_width=1, border_color=BORDER)
        ctrl.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(ctrl, text=t("sched_settings"),
                      font=ctk.CTkFont(size=14, weight="bold"),
                      text_color="#ccc").pack(padx=18, pady=(16, 8), anchor="w")

        # İpuçları
        tips = [
            "• Ders atamaları (Ders Atamaları menüsü) tamamlandıktan sonra çalıştırın.",
            "• Mevcut program silinerek yeniden oluşturulur.",
            "• Zorluk derecesi yüksek dersler sabah saatlerine önceliklendirilir.",
            "• Algoritma çakışmaları otomatik olarak önler.",
        ]
        for tip in tips:
            ctk.CTkLabel(ctrl, text=tip,
                          font=ctk.CTkFont(size=11), text_color=TEXT_SEC,
                          justify="left", anchor="w"
                          ).pack(anchor="w", padx=18, pady=1)

        ctk.CTkFrame(ctrl, fg_color=BORDER, height=1).pack(
            fill="x", padx=18, pady=12)

        # İlerleme barı
        self.progress_bar = ctk.CTkProgressBar(ctrl, height=14,
                                                progress_color=ACCENT,
                                                fg_color="#2d2d2d")
        self.progress_bar.pack(fill="x", padx=18, pady=(0, 6))
        self.progress_bar.set(0)

        self.progress_lbl = ctk.CTkLabel(ctrl, text=t("sched_waiting"),
                                          font=ctk.CTkFont(size=11),
                                          text_color=TEXT_SEC)
        self.progress_lbl.pack(padx=18, anchor="w", pady=(0, 12))

        # Butonlar
        btn_f = ctk.CTkFrame(ctrl, fg_color="transparent")
        btn_f.pack(padx=18, pady=(0, 18), fill="x")

        self.run_btn = ctk.CTkButton(btn_f, text=t("sched_run"),
                                      fg_color=SUCCESS, hover_color="#1e8449",
                                      height=40, font=ctk.CTkFont(size=14),
                                      command=self._start)
        self.run_btn.pack(fill="x", pady=(0, 6))

        ctk.CTkButton(btn_f, text=t("sched_clear"),
                       fg_color="#333", hover_color=DANGER,
                       height=36, command=self._clear
                       ).pack(fill="x")

        # ── Sağ: Veri özeti ─────────────────────────────────────────────────
        summary = ctk.CTkFrame(top, fg_color=CARD_BG, corner_radius=12,
                                border_width=1, border_color=BORDER)
        summary.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(summary, text=t("data_summary"),
                      font=ctk.CTkFont(size=14, weight="bold"),
                      text_color="#ccc").pack(padx=18, pady=(16, 8), anchor="w")

        self.summary_frame = ctk.CTkFrame(summary, fg_color="transparent")
        self.summary_frame.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        self._refresh_summary()

        # ── Alt: Log ─────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text=t("log_title"),
                      font=ctk.CTkFont(size=14, weight="bold"),
                      text_color="#ccc"
                      ).pack(anchor="w", padx=20, pady=(8, 4))

        self.log_box = ctk.CTkTextbox(self, height=200, fg_color="#141414",
                                       text_color=TEXT_PRI,
                                       font=ctk.CTkFont(family="Consolas", size=12),
                                       border_color=BORDER, border_width=1)
        self.log_box.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.log_box.configure(state="disabled")

    def _refresh_summary(self):
        for w in self.summary_frame.winfo_children():
            w.destroy()
        s = db.get_stats()
        items = [
            ("👨 Öğretmen", s['teachers']),
            ("📚 Ders",       s['subjects']),
            ("🏫 Sınıf",      s['classes']),
            ("🚪 Derslik",    s['classrooms']),
            ("📋 Atama",      s['assignments']),
            ("⏱ Toplam Saat", s['total_hours']),
            ("✅ Yerleştirilen", s['placed_hours']),
        ]
        for label, val in items:
            row = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=label,
                          font=ctk.CTkFont(size=12), text_color=TEXT_SEC,
                          anchor="w").pack(side="left")
            color = ACCENT if isinstance(val, int) and val > 0 else TEXT_SEC
            ctk.CTkLabel(row, text=str(val),
                          font=ctk.CTkFont(size=12, weight="bold"),
                          text_color=color).pack(side="right")

    def _log(self, msg):
        if msg.startswith("__PROGRESS__"):
            pct = int(msg.replace("__PROGRESS__", "")) / 100
            self.progress_bar.set(pct)
            self.progress_lbl.configure(text=f"İşleniyor… %{int(pct*100)}")
            return
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _start(self):
        if self._running:
            return
        s = db.get_stats()
        if s['assignments'] == 0:
            self._log("⚠ Henüz ders ataması yapılmamış. Önce ders atamalarını tamamlayın.")
            return

        self._running = True
        self.run_btn.configure(state="disabled", text=t("sched_running"))
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self.progress_bar.set(0)

        db.clear_timetable()

        def run():
            sched = Scheduler(progress_callback=lambda m: self.after(0, self._log, m))
            done, total, conflicts = sched.run()
            self.after(0, self._on_finished, done, total)

        threading.Thread(target=run, daemon=True).start()

    def _on_finished(self, done, total):
        self._running = False
        color = SUCCESS if done == total else WARNING if done > 0 else DANGER
        self.progress_lbl.configure(
            text=f"Tamamlandı: {done}/{total}", text_color=color)
        self.run_btn.configure(state="normal", text=t("sched_run"))
        self._refresh_summary()
        if self._on_done:
            self._on_done()

    def _clear(self):
        db.clear_timetable()
        self.progress_bar.set(0)
        self.progress_lbl.configure(text="Program temizlendi.", text_color=WARNING)
        self._log("🗑  Tüm program silindi.")
        self._refresh_summary()
        if self._on_done:
            self._on_done()

    def refresh(self):
        self._refresh_summary()
