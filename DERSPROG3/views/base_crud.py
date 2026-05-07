import os

import customtkinter as ctk

# ── Renkler ────────────────────────────────────────────────────────────────
CARD_BG  = "#1e1e1e"
ACCENT   = "#3a7bd5"
DANGER   = "#e74c3c"
SUCCESS  = "#27ae60"
TEXT_PRI = "#ffffff"
TEXT_SEC = "#C5C5C5"
BORDER   = "#2a2a2a"
ROW_ODD  = "#232323"
ROW_EVEN = "#003D0E"
QUICKADD = "#1a2a1a"

BTN_W    = 76   # Sağdaki düzenle/sil buton alanı sabit genişlik
ROW_H    = 36   # Satır yüksekliği


class BaseCRUDView(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._rows    = []
        self._edit_id = None
        self._build_layout()
        self.refresh()

    # ─────────────────────── Ana yerleşim ────────────────────────────────────
    def _build_layout(self):
        # Başlık
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(20, 0))
        self._title_lbl = ctk.CTkLabel(hdr, text=self.get_title(),
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=TEXT_PRI)
        self._title_lbl.pack(side="left")
        self.count_badge = ctk.CTkLabel(
            hdr, text="0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#fff", fg_color=ACCENT,
            corner_radius=10, width=32, height=22)
        self.count_badge.pack(side="left", padx=10)

        self._subtitle_lbl = ctk.CTkLabel(self, text=self.get_subtitle(),
                     font=ctk.CTkFont(size=13), text_color=TEXT_SEC)
        self._subtitle_lbl.pack(anchor="w", padx=20, pady=(2, 10))

        # Arama
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(0, 8))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter())
        ctk.CTkEntry(toolbar, textvariable=self.search_var,
                     placeholder_text="🔍  Ara…",
                     fg_color="#1e1e1e", border_color=BORDER,
                     text_color=TEXT_PRI, width=260, height=34
                     ).pack(side="left")

        # İçerik
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=0)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=0)
        content.rowconfigure(0, weight=1)

        # ── Tablo kartı ──────────────────────────────────────────────────
        table_wrap = ctk.CTkFrame(content, fg_color=CARD_BG,
                                   corner_radius=12, border_width=1,
                                   border_color=BORDER)
        table_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        table_wrap.rowconfigure(1, weight=1)
        table_wrap.columnconfigure(0, weight=1)

        # Başlık satırı — sabit yükseklik, fill=x
        self._header_frame = ctk.CTkFrame(table_wrap, fg_color="#252525",
                                           corner_radius=10, height=36)
        self._header_frame.grid(row=0, column=0, sticky="ew", padx=2, pady=(2, 0))
        self._header_frame.pack_propagate(False)
        # Header genişlik değişince yeniden çiz
        self._header_frame.bind("<Configure>", lambda e: self.after(5, self._draw_headers))

        # Satır listesi
        self.scroll_frame = ctk.CTkScrollableFrame(
            table_wrap, fg_color="transparent",
            scrollbar_button_color="#2d2d2d",
            scrollbar_button_hover_color="#3a3a3a")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=2)
        self.scroll_frame.columnconfigure(0, weight=1)

        # ── Hızlı ekleme satırı ──────────────────────────────────────────
        self._quickadd_frame = ctk.CTkFrame(
            table_wrap, fg_color=QUICKADD,
            corner_radius=10, height=46)
        self._quickadd_frame.grid(row=2, column=0, sticky="ew", padx=2, pady=(0, 2))
        self._quickadd_frame.columnconfigure(0, weight=1)
        self._build_quickadd()

        # ── Düzenleme paneli (sağ, başta gizli) ──────────────────────────
        self.form_panel = ctk.CTkFrame(content, fg_color=CARD_BG,
                                        corner_radius=12, border_width=1,
                                        border_color=BORDER, width=300)
        self.form_panel.grid(row=0, column=1, sticky="ns")
        self.form_panel.grid_remove()
        self._build_form_panel()

    # ─────────────────────── Sütun genişliği hesaplama ───────────────────────
    def _get_col_widths(self):
        """
        get_columns() → [(name, hint_w), ...]
        Gerçek container genişliğine göre orantısal piksel genişlikleri döner.
        """
        cols      = self.get_columns()
        container = self._header_frame.winfo_width()
        if container < 50:
            container = 800  # henüz render edilmemişse makul bir varsayılan

        total_hint = sum(w for _, w in cols)
        avail      = max(container - BTN_W - 4, total_hint)

        widths = []
        for _, hint in cols:
            widths.append(max(int(avail * hint / total_hint), hint))
        return widths

    # ─────────────────────── Başlık çizimi ───────────────────────────────────
    def _draw_headers(self):
        for w in self._header_frame.winfo_children():
            w.destroy()

        cols   = self.get_columns()
        widths = self._get_col_widths()

        # Sütun etiketleri — hepsi pack(side="left"), sabit width
        for ci, ((name, _), w) in enumerate(zip(cols, widths)):
            ctk.CTkLabel(self._header_frame, text=name,
                          font=ctk.CTkFont(size=12, weight="bold"),
                          text_color="#aaa", anchor="w",
                          width=w
                          ).pack(side="left",
                                 padx=(10 if ci == 0 else 0, 0),
                                 pady=4)

        # Sağda buton alanı kadar boşluk
        ctk.CTkLabel(self._header_frame, text="", width=BTN_W
                     ).pack(side="right")

    # ─────────────────────── Tablo render ────────────────────────────────────
    def refresh(self):
        if hasattr(self, '_title_lbl'):
            self._title_lbl.configure(text=self.get_title())
        if hasattr(self, '_subtitle_lbl'):
            self._subtitle_lbl.configure(text=self.get_subtitle())
        self._rows = self.load_data()
        self._render(self._rows)
        self.count_badge.configure(text=str(len(self._rows)))

    def _filter(self):
        q = self.search_var.get().lower()
        self._render([r for r in self._rows
                      if q in str(self.row_values(r)).lower()])

    def _render(self, rows):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        self.scroll_frame.columnconfigure(0, weight=1)

        cols = self.get_columns()

        for ri, row in enumerate(rows):
            bg = ROW_ODD if ri % 2 == 0 else ROW_EVEN
            rf = ctk.CTkFrame(self.scroll_frame, fg_color=bg,
                               corner_radius=0, height=ROW_H)
            rf.grid(row=ri, column=0, sticky="ew")
            rf.pack_propagate(False)
            # Genişlik değişince sütun genişliklerini yeniden hesapla
            rf.bind("<Configure>",
                    lambda e, r=rf, ro=row: self._draw_row(r, ro))

        if not rows:
            ctk.CTkLabel(self.scroll_frame, text="Kayıt bulunamadı.",
                          font=ctk.CTkFont(size=13), text_color=TEXT_SEC
                          ).grid(row=0, column=0, pady=30)

        self.after(5, self._draw_headers)

    def _draw_row(self, rf, row):
        """Tek bir satırı _header ile aynı genişlikleri kullanarak çizer."""
        for w in rf.winfo_children():
            w.destroy()

        cols   = self.get_columns()
        widths = self._get_col_widths()
        vals   = self.row_values(row)

        # Sağ: buton grubu — önce pack et ki yer ayırsın
        bf = ctk.CTkFrame(rf, fg_color="transparent")
        bf.pack(side="right", padx=4)
        rid = row["id"]
        ctk.CTkButton(bf, text="✏", width=28, height=26,
                       fg_color="#2a2a2a", hover_color="#3a3a3a",
                       text_color="#aaa",
                       command=lambda r=row: self._open_form(r)
                       ).pack(side="left", padx=2)
        ctk.CTkButton(bf, text="🗑", width=28, height=26,
                       fg_color="#2a2a2a", hover_color=DANGER,
                       text_color="#aaa",
                       command=lambda r=rid: self._confirm_delete(r)
                       ).pack(side="left", padx=2)

        # Sol: veri sütunları — header ile aynı width ve padx
        for ci, (val, w) in enumerate(zip(vals, widths)):
            ctk.CTkLabel(rf, text=str(val),
                          font=ctk.CTkFont(size=12),
                          text_color=TEXT_PRI, anchor="w",
                          width=w
                          ).pack(side="left",
                                 padx=(10 if ci == 0 else 0, 0),
                                 pady=0)

    # ─────────────────────── Hızlı ekleme ────────────────────────────────────
    def _build_quickadd(self):
        f = self._quickadd_frame

        ctk.CTkLabel(f, text="  ➕  Hızlı Ekle:",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      text_color="#4ade80").pack(side="left", padx=(10, 6), pady=8)

        quick = self.get_quick_fields()
        self._quick_vars = {}

        for placeholder, attr, w in quick:
            var = ctk.StringVar()
            self._quick_vars[attr] = var
            e = ctk.CTkEntry(f, textvariable=var,
                              placeholder_text=placeholder,
                              fg_color="#1e2a1e", border_color="#2a4a2a",
                              text_color=TEXT_PRI, height=30, width=w)
            e.pack(side="left", padx=4, pady=8)
            e.bind("<Return>", lambda ev: self._quick_save())

        self.build_quickadd_extras(f)

        ctk.CTkButton(f, text="Kaydet", width=80, height=30,
                       fg_color=SUCCESS, hover_color="#1e8449",
                       font=ctk.CTkFont(size=12),
                       command=self._quick_save).pack(side="left", padx=(8, 4))

        self._quick_msg = ctk.CTkLabel(f, text="",
                                        font=ctk.CTkFont(size=11))
        self._quick_msg.pack(side="left", padx=4)

    def _quick_save(self):
        data = {attr: var.get().strip()
                for attr, var in self._quick_vars.items()}
        data.update(self.collect_quick_extras())

        ok, msg = self.validate(data)
        if not ok:
            self._quick_msg.configure(text=f"⚠ {msg}", text_color="#e67e22")
            self.after(2500, lambda: self._quick_msg.configure(text=""))
            return

        self.on_save(data, None)
        for var in self._quick_vars.values():
            var.set("")
        self.reset_quick_extras()
        self._quick_msg.configure(text="✓ Kaydedildi", text_color=SUCCESS)
        self.after(1500, lambda: self._quick_msg.configure(text=""))
        self.refresh()

    # ─────────────────────── Düzenleme formu ─────────────────────────────────
    def _build_form_panel(self):
        p = self.form_panel
        p.columnconfigure(0, weight=1)

        self.form_title_lbl = ctk.CTkLabel(
            p, text="Kaydı Düzenle",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT_PRI)
        self.form_title_lbl.grid(row=0, column=0, padx=18, pady=(18, 10), sticky="w")

        self._form_widgets = {}
        for ri, (label, placeholder, attr) in enumerate(
                self.get_form_fields(), start=1):
            ctk.CTkLabel(p, text=label,
                          font=ctk.CTkFont(size=12), text_color=TEXT_SEC
                          ).grid(row=ri*2-1, column=0, padx=18, pady=(6, 2), sticky="w")
            var = ctk.StringVar()
            ctk.CTkEntry(p, textvariable=var,
                          placeholder_text=placeholder,
                          fg_color="#252525", border_color=BORDER,
                          text_color=TEXT_PRI, height=34
                          ).grid(row=ri*2, column=0, padx=18, sticky="ew")
            self._form_widgets[attr] = var

        self._extra_start_row = len(self.get_form_fields()) * 2 + 1
        self.build_form_extra(p)

        btn_row = self._extra_start_row + 20
        bf = ctk.CTkFrame(p, fg_color="transparent")
        bf.grid(row=btn_row, column=0, padx=18, pady=(16, 8), sticky="ew")
        bf.columnconfigure([0, 1], weight=1)
        ctk.CTkButton(bf, text="Güncelle", fg_color=ACCENT,
                       hover_color="#2563ba", height=34,
                       command=self._save).grid(row=0, column=0, padx=(0, 4), sticky="ew")
        ctk.CTkButton(bf, text="İptal", fg_color="#333",
                       hover_color="#444", height=34,
                       command=self._close_form).grid(row=0, column=1, padx=(4, 0), sticky="ew")

        self.msg_lbl = ctk.CTkLabel(p, text="", font=ctk.CTkFont(size=12))
        self.msg_lbl.grid(row=btn_row+1, column=0, padx=18, pady=(0, 8))

    # ─────────────────────── Form açma/kapama ────────────────────────────────
    def _open_form(self, row):
        self._edit_id = row['id']
        for attr, var in self._form_widgets.items():
            var.set(str(row[attr]) if attr in row.keys() else "")
        self.populate_form_extras(row)
        self.form_panel.grid()
        self.msg_lbl.configure(text="")

    def _close_form(self):
        self.form_panel.grid_remove()
        self._edit_id = None

    def _save(self):
        data = {attr: var.get().strip() for attr, var in self._form_widgets.items()}
        data.update(self.collect_extras())
        ok, msg = self.validate(data)
        if not ok:
            self.msg_lbl.configure(text=f"⚠ {msg}", text_color="#e67e22")
            return
        self.on_save(data, self._edit_id)
        self._close_form()
        self.refresh()

    def _confirm_delete(self, item_id):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Silme Onayı")
        
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
        dlg.geometry("320x140")
        dlg.grab_set()
        dlg.configure(fg_color="#1a1a1a")
        ctk.CTkLabel(dlg, text="Bu kaydı silmek istediğinizden\nemin misiniz?",
                      font=ctk.CTkFont(size=13), text_color=TEXT_PRI
                      ).pack(pady=20)
        bf = ctk.CTkFrame(dlg, fg_color="transparent")
        bf.pack()
        ctk.CTkButton(bf, text="Evet, Sil", fg_color=DANGER,
                       hover_color="#c0392b", width=110,
                       command=lambda: (self.on_delete(item_id),
                                         dlg.destroy(), self.refresh())
                       ).pack(side="left", padx=6)
        ctk.CTkButton(bf, text="İptal", fg_color="#333",
                       hover_color="#444", width=110,
                       command=dlg.destroy).pack(side="left", padx=6)

    # ─────────────────────── Subclass hooks ──────────────────────────────────
    def build_form_extra(self, parent):       pass
    def populate_form_extras(self, row):      pass
    def collect_extras(self):                 return {}
    def build_quickadd_extras(self, parent):  pass
    def collect_quick_extras(self):           return {}
    def reset_quick_extras(self):             pass
    def validate(self, data):                 return True, ""
    def load_data(self):                      return []
    def on_save(self, data, edit_id):         pass
    def on_delete(self, item_id):             pass
    def row_values(self, row):                return tuple(row)
    def get_title(self):                      return ""
    def get_subtitle(self):                   return ""
    def get_columns(self):                    return []
    def get_form_fields(self):                return []
    def get_quick_fields(self):               return []
