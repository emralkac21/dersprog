from lang import t
import customtkinter as ctk
import database as db
from database import get_stats

class DashboardView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build()

    def _build(self):
        # Başlık
        ctk.CTkLabel(self, text=t("dashboard_title"),
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#e0e0e0").pack(anchor="w", padx=20, pady=(20, 4))
        ctk.CTkLabel(self, text=t("dashboard_subtitle"),
                     font=ctk.CTkFont(size=13), text_color="#888").pack(anchor="w", padx=20, pady=(0, 20))

        self.card_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.card_frame.pack(fill="x", padx=20, pady=0)

        self.progress_frame = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=12)
        self.progress_frame.pack(fill="x", padx=20, pady=(18, 0))

        self.info_label = ctk.CTkLabel(self, text="",
                                        font=ctk.CTkFont(size=12), text_color="#666")
        self.info_label.pack(anchor="w", padx=20, pady=(20, 0))
        self.refresh()

    def refresh(self):
        # Kartları temizle
        for w in self.card_frame.winfo_children():
            w.destroy()
        for w in self.progress_frame.winfo_children():
            w.destroy()

        s = get_stats()

        cards = [
            ("👨", "Öğretmen",  str(s['teachers']),   "#3a7bd5"),
            ("📚", "Ders",       str(s['subjects']),   "#9b59b6"),
            ("🏫", "Sınıf",      str(s['classes']),    "#27ae60"),
            ("🚪", "Derslik",    str(s['classrooms']), "#e67e22"),
            ("📋", "Atama",      str(s['assignments']),"#e74c3c"),
        ]

        self.card_frame.columnconfigure(list(range(len(cards))), weight=1)
        for col, (icon, label, val, color) in enumerate(cards):
            card = ctk.CTkFrame(self.card_frame, fg_color="#1e1e1e",
                                corner_radius=12, border_width=1,
                                border_color="#2a2a2a")
            card.grid(row=0, column=col, padx=6, pady=4, sticky="ew")
            ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=28)).pack(pady=(14, 2))
            ctk.CTkLabel(card, text=val,
                         font=ctk.CTkFont(size=26, weight="bold"),
                         text_color=color).pack()
            ctk.CTkLabel(card, text=label,
                         font=ctk.CTkFont(size=12), text_color="#999").pack(pady=(0, 14))

        # İlerleme barı
        pct = s['completion']
        color = "#27ae60" if pct >= 80 else "#e67e22" if pct >= 40 else "#e74c3c"

        ctk.CTkLabel(self.progress_frame,
                     text=f"  Ders Yerleştirme İlerlemesi",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#ccc").pack(anchor="w", padx=16, pady=(14, 6))

        bar_container = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        bar_container.pack(fill="x", padx=16, pady=(0, 6))

        bar = ctk.CTkProgressBar(bar_container, height=18, corner_radius=9,
                                  progress_color=color, fg_color="#2d2d2d")
        bar.pack(side="left", fill="x", expand=True)
        bar.set(pct / 100)

        ctk.CTkLabel(bar_container,
                     text=f"  {pct}%",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=color, width=55).pack(side="left")

        ctk.CTkLabel(self.progress_frame,
                     text=f"  {s['placed_hours']} / {s['total_hours']} ders saati yerleştirildi",
                     font=ctk.CTkFont(size=12), text_color="#888").pack(anchor="w", padx=16, pady=(0, 14))

        # Detay özeti
        with db.get_connection() as conn:
            atanan = conn.execute(
                "SELECT COUNT(DISTINCT class_id) FROM class_subjects").fetchone()[0]
            tum    = s['classes']
        if tum > 0:
            detail = (f"Son güncelleme: az önce  •  "
                      f"{atanan}/{tum} sınıfa ders atandı  •  "
                      f"Veritabanı: timetable.db")
        else:
            detail = "Son güncelleme: az önce  •  Veritabanı: timetable.db"
        self.info_label.configure(text=detail)
