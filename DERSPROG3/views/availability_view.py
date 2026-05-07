from lang import t
import customtkinter as ctk
import database as db
from engine.scheduler import DAY_NAMES

TEXT_PRI = "#e0e0e0"
TEXT_SEC = "#999999"
BORDER   = "#2a2a2a"
CARD_BG  = "#1e1e1e"

import schedule_config as _sc
DAYS  = list(range(5))
HOURS = list(range(1, 9))

STATUS_CYCLE = ["available", "unavailable", "preferred_not"]
STATUS_CFG = {
    "available":     {"bg": "#1a3a1a", "text": "✓",  "tc": "#4ade80"},
    "unavailable":   {"bg": "#3a1a1a", "text": "✗",  "tc": "#f87171"},
    "preferred_not": {"bg": "#3a3a1a", "text": "~",  "tc": "#fbbf24"},
}


class AvailabilityView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._resource_type = "teacher"
        self._resource_id   = None
        self._avail_data    = {}
        self._cell_btns     = {}
        self._build()
        self.refresh()

    def _build(self):
        ctk.CTkLabel(self, text=t("avail_title"),
                      font=ctk.CTkFont(size=22, weight="bold"),
                      text_color=TEXT_PRI).pack(anchor="w", padx=20, pady=(20, 2))
        ctk.CTkLabel(self, text=t("avail_subtitle"),
                      font=ctk.CTkFont(size=13), text_color=TEXT_SEC
                      ).pack(anchor="w", padx=20, pady=(0, 14))

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(0, 10))

        # Tür seçici — Öğretmen / Derslik / Sınıf
        ctk.CTkLabel(toolbar, text=t("resource_type"),
                      text_color=TEXT_SEC, font=ctk.CTkFont(size=12)
                      ).pack(side="left", padx=(0, 6))
        self._type_var = ctk.StringVar(value=t("res_teacher"))
        ctk.CTkOptionMenu(toolbar, variable=self._type_var,
                          values=[t("res_teacher"), t("res_classroom"), t("res_class")],
                          fg_color="#252525", button_color="#333",
                          text_color=TEXT_PRI, width=120,
                          command=self._on_type_change
                          ).pack(side="left", padx=(0, 14))

        ctk.CTkLabel(toolbar, text=t("resource_label"),
                      text_color=TEXT_SEC, font=ctk.CTkFont(size=12)
                      ).pack(side="left", padx=(0, 6))
        self._res_var = ctk.StringVar(value="— Seçin —")
        self._res_menu = ctk.CTkOptionMenu(
            toolbar, variable=self._res_var,
            values=["— Yükleniyor —"],
            fg_color="#252525", button_color="#333",
            text_color=TEXT_PRI, width=220,
            command=self._on_res_change)
        self._res_menu.pack(side="left", padx=(0, 14))

        # Hepsini müsait yap
        ctk.CTkButton(toolbar, text=t("all_available"),
                       width=130, height=32,
                       fg_color="#1a3a1a", hover_color="#27ae60",
                       text_color="#4ade80",
                       command=self._set_all_available
                       ).pack(side="right", padx=4)

        # Izgarası
        grid_wrap = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                                  border_width=1, border_color=BORDER)
        grid_wrap.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.grid_inner = ctk.CTkFrame(grid_wrap, fg_color="transparent")
        self.grid_inner.pack(padx=16, pady=16)

        # Açıklama
        leg = ctk.CTkFrame(self, fg_color="transparent")
        leg.pack(fill="x", padx=20, pady=(0, 14))
        for status, cfg in STATUS_CFG.items():
            f = ctk.CTkFrame(leg, fg_color=cfg['bg'], corner_radius=4,
                              width=90, height=24)
            f.pack(side="left", padx=4)
            labels = {"available":"Müsait",
                      "unavailable":"Müsait Değil",
                      "preferred_not":"Tercih Edilmez"}
            ctk.CTkLabel(f, text=labels[status],
                          text_color=cfg['tc'], font=ctk.CTkFont(size=10)
                          ).place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(leg, text="  (Hücreye tıklayarak durum değiştirin)",
                      text_color=TEXT_SEC, font=ctk.CTkFont(size=11)
                      ).pack(side="left")

    def refresh(self):
        self._update_resource_list()
        if self._resource_id:
            self._load_and_render()

    def _on_type_change(self, val):
        if val == t("res_teacher"):
            self._resource_type = "teacher"
        elif val == t("res_classroom"):
            self._resource_type = "classroom"
        else:
            self._resource_type = "class"
        self._resource_id   = None
        self._res_var.set("— Seçin —")
        self._update_resource_list()
        self._render_grid()

    def _update_resource_list(self):
        if self._resource_type == "teacher":
            resources = db.get_teachers()
            names = [f"{r['name']} {r['surname']}" for r in resources]
            self._res_id_map = {f"{r['name']} {r['surname']}": r['id']
                                for r in resources}
        elif self._resource_type == "classroom":
            resources = db.get_classrooms()
            names = [r['name'] for r in resources]
            self._res_id_map = {r['name']: r['id'] for r in resources}
        else:  # class
            resources = db.get_classes()
            names = [f"{r['level']}-{r['section']}" for r in resources]
            self._res_id_map = {f"{r['level']}-{r['section']}": r['id']
                                for r in resources}

        self._res_menu.configure(values=["— Seçin —"] + names
                                 if names else ["— Kayıt Yok —"])

    def _on_res_change(self, val):
        self._resource_id = self._res_id_map.get(val)
        if self._resource_id:
            self._load_and_render()

    def _load_and_render(self):
        self._avail_data = db.get_availability(
            self._resource_type, self._resource_id)
        self._render_grid()

    def _render_grid(self):
        for w in self.grid_inner.winfo_children():
            w.destroy()
        self._cell_btns = {}

        DAYS  = _sc.get_active_days()
        HOURS = _sc.get_hours_list()
        DAY_NAMES = _sc.ALL_DAY_NAMES

        if not self._resource_id:
            ctk.CTkLabel(self.grid_inner,
                          text=t("select_record"),
                          font=ctk.CTkFont(size=13), text_color=TEXT_SEC
                          ).grid(row=0, column=0, pady=40, padx=60)
            return

        # Başlık satırı
        ctk.CTkLabel(self.grid_inner, text="",
                      width=60, height=36).grid(row=0, column=0)
        for di, day in enumerate(DAYS):
            ctk.CTkLabel(self.grid_inner, text=DAY_NAMES[day],
                          font=ctk.CTkFont(size=12, weight="bold"),
                          text_color="#ccc", width=90
                          ).grid(row=0, column=di+1, padx=3)

        for hi, hour in enumerate(HOURS):
            ctk.CTkLabel(self.grid_inner, text=f"{hour}. Saat",
                          font=ctk.CTkFont(size=11), text_color=TEXT_SEC,
                          width=60, anchor="e"
                          ).grid(row=hi+1, column=0, padx=(0, 8), pady=3)

            for di, day in enumerate(DAYS):
                status = self._avail_data.get((day, hour), "available")
                cfg    = STATUS_CFG[status]
                btn = ctk.CTkButton(
                    self.grid_inner, text=cfg['text'],
                    width=88, height=38,
                    fg_color=cfg['bg'], hover_color="#3a3a3a",
                    text_color=cfg['tc'],
                    font=ctk.CTkFont(size=16, weight="bold"),
                    corner_radius=6,
                    command=lambda d=day, h=hour: self._toggle(d, h))
                btn.grid(row=hi+1, column=di+1, padx=3, pady=3)
                self._cell_btns[(day, hour)] = btn

    def _toggle(self, day, hour):
        if not self._resource_id:
            return
        current = self._avail_data.get((day, hour), "available")
        idx     = STATUS_CYCLE.index(current)
        new_status = STATUS_CYCLE[(idx + 1) % len(STATUS_CYCLE)]
        db.set_availability(self._resource_type, self._resource_id,
                            day, hour, new_status)
        self._avail_data[(day, hour)] = new_status
        # Hücreyi güncelle
        cfg = STATUS_CFG[new_status]
        btn = self._cell_btns.get((day, hour))
        if btn:
            btn.configure(fg_color=cfg['bg'], text=cfg['text'],
                          text_color=cfg['tc'])

    def _set_all_available(self):
        if not self._resource_id:
            return
        for day in DAYS:
            for hour in HOURS:
                db.set_availability(self._resource_type, self._resource_id,
                                    day, hour, "available")
                self._avail_data[(day, hour)] = "available"
        self._render_grid()
