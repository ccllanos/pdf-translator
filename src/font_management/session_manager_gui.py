from typing import Dict, List, Set
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                               QPushButton, QGridLayout, QFileDialog, QTabWidget, QWidget, QLineEdit, QMessageBox)

class SessionSettingsGUI(QDialog):
    def __init__(self, pdf_fonts: Set[str], font_cloud_report: List[Dict], total_pages: int, initial_font_mappings: Dict = None):
        super().__init__()
        self.pdf_fonts = pdf_fonts
        self.font_cloud_report = font_cloud_report
        self.total_pages = total_pages
        
        # Diccionario maestro que sobrevivirá a la destrucción visual de la ventana
        self.final_configuration = None 
        
        self.saved_mappings = initial_font_mappings or {}
        
        self.font_to_pdf_code = {
            "Helvetica (Base)": "helv",
            "Times-Roman (Base)": "tiro",
            "Courier (Base)": "cour",
            "Symbol (Base)": "symb",
            "ZapfDingbats (Base)": "zadb"
        }
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Configuración de Proyecto de Traducción")
        self.resize(800, 500)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2 style='color:#2c3e50;'>⚙️ Parámetros de la Sesión</h2>"))
        
        self.tabs = QTabWidget()
        
        # --- TAB 1: PÁGINAS ---
        tab_pages = QWidget()
        layout_pages = QVBoxLayout(tab_pages)
        layout_pages.addWidget(QLabel("<h3>1. Rango de Páginas a Procesar</h3>"))
        layout_pages.addWidget(QLabel(f"Total de páginas en el documento: <b>{self.total_pages}</b>"))
        
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("Desde:"))
        self.txt_start = QLineEdit("1")
        self.txt_start.setFixedWidth(50)
        range_layout.addWidget(self.txt_start)
        
        range_layout.addWidget(QLabel("Hasta:"))
        self.txt_end = QLineEdit(str(self.total_pages))
        self.txt_end.setFixedWidth(50)
        range_layout.addWidget(self.txt_end)
        range_layout.addStretch()
        
        layout_pages.addLayout(range_layout)
        layout_pages.addStretch()
        self.tabs.addTab(tab_pages, "1. Selección de Páginas")

        # --- TAB 2: FUENTES ---
        tab_fonts = QWidget()
        layout_fonts = QVBoxLayout(tab_fonts)
        layout_fonts.addWidget(QLabel("<h3>2. Configuración de Tipografías</h3>"))
        
        grid_fonts = QGridLayout()
        grid_fonts.addWidget(QLabel("<b>Fuente Original</b>"), 0, 0)
        grid_fonts.addWidget(QLabel("<b>Reemplazo</b>"), 0, 1)
        grid_fonts.addWidget(QLabel("<b>Archivo Custom (.ttf)</b>"), 0, 2)

        self.font_comboboxes = {}
        self.font_custom_paths = {}

        for row, font_info in enumerate(self.font_cloud_report, start=1):
            raw_font = font_info['raw_name']
            grid_fonts.addWidget(QLabel(f"• {raw_font}"), row, 0)

            cb = QComboBox()
            cb.addItems(list(self.font_to_pdf_code.keys()) + ["-- USAR ARCHIVO .TTF --"])
            
            # Carga de caché o inteligente
            saved = self.saved_mappings.get(raw_font)
            if saved:
                if saved["type"] == "custom":
                    cb.setCurrentText("-- USAR ARCHIVO .TTF --")
                    self.font_custom_paths[raw_font] = saved["value"]
                else:
                    for k, v in self.font_to_pdf_code.items():
                        if v == saved["value"]: cb.setCurrentText(k)
            else:
                if "times" in raw_font.lower() or "serif" in raw_font.lower():
                    cb.setCurrentText("Times-Roman (Base)")
                else:
                    cb.setCurrentText("Helvetica (Base)")

            grid_fonts.addWidget(cb, row, 1)
            self.font_comboboxes[raw_font] = cb

            lbl_file = QLabel("No cargado" if raw_font not in self.font_custom_paths else os.path.basename(self.font_custom_paths[raw_font]))
            btn_browse = QPushButton("Examinar...")
            btn_browse.clicked.connect(lambda r=raw_font, c=cb, l=lbl_file: self._browse_font(r, c, l))
            
            hb = QHBoxLayout()
            hb.addWidget(btn_browse)
            hb.addWidget(lbl_file)
            grid_fonts.addLayout(hb, row, 2)

        layout_fonts.addLayout(grid_fonts)
        layout_fonts.addStretch()
        self.tabs.addTab(tab_fonts, "2. Mapeo de Fuentes")

        # --- TAB 3: MODOS Y FONDOS ---
        tab_modes = QWidget()
        layout_modes = QVBoxLayout(tab_modes)
        layout_modes.addWidget(QLabel("<h3>3. Modos de Página & Fondos</h3>"))
        
        self.page_widgets = {}
        grid_modes = QGridLayout()
        grid_modes.addWidget(QLabel("<b>Página</b>"), 0, 0)
        grid_modes.addWidget(QLabel("<b>Modo</b>"), 0, 1)
        grid_modes.addWidget(QLabel("<b>Fondo Limpio</b>"), 0, 2)

        max_rows = min(self.total_pages, 8)
        for p in range(1, max_rows + 1):
            grid_modes.addWidget(QLabel(f"Página {p}"), p, 0)
            
            cb_mode = QComboBox()
            cb_mode.addItems(["Básico (Sin fondos)", "Editorial (Fondo Limpio)"])
            cb_mode.setCurrentText("Básico (Sin fondos)")
            grid_modes.addWidget(cb_mode, p, 1)

            lbl_bg = QLabel("Ninguno seleccionado")
            btn_bg = QPushButton("Aportar Arte...")
            btn_bg.clicked.connect(lambda page=p, c=cb_mode, l=lbl_bg: self._browse_bg(page, c, l))
            
            hb = QHBoxLayout()
            hb.addWidget(btn_bg)
            hb.addWidget(lbl_bg)
            grid_modes.addLayout(hb, p, 2)
            
            self.page_widgets[p] = {"combo": cb_mode, "path": None}

        layout_modes.addLayout(grid_modes)
        layout_modes.addStretch()
        self.tabs.addTab(tab_modes, "3. Modos y Arte")

        layout.addWidget(self.tabs)

        # Botones
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        
        btn_confirm = QPushButton("Confirmar y Procesar ➔")
        btn_confirm.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px;")
        btn_confirm.clicked.connect(self._save_and_accept)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_confirm)
        layout.addLayout(btn_layout)

    def _browse_font(self, raw_font, combobox, label):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar .ttf", "C:\\Windows\\Fonts", "Fuentes (*.ttf *.otf)")
        if file_path:
            short_name = os.path.basename(file_path)
            if short_name.startswith("._") or "__MACOSX" in file_path:
                QMessageBox.warning(self, "Error", "Archivo residual de Mac no permitido.")
                return
            combobox.setCurrentText("-- USAR ARCHIVO .TTF --")
            label.setText(short_name)
            self.font_custom_paths[raw_font] = file_path

    def _browse_bg(self, page_num, combobox, label):
        file_path, _ = QFileDialog.getOpenFileName(self, f"Arte Pág {page_num}", "", "Imágenes (*.png *.jpg *.jpeg)")
        if file_path:
            combobox.setCurrentText("Editorial (Fondo Limpio)")
            label.setText(os.path.basename(file_path))
            self.page_widgets[page_num]["path"] = file_path

    def _save_and_accept(self):
        """Recopila todas las variables antes de destruir la ventana."""
        try:
            start = int(self.txt_start.text())
            end = int(self.txt_end.text())
            if not (1 <= start <= end <= self.total_pages): raise ValueError()
        except:
            QMessageBox.critical(self, "Error", "Rango de páginas inválido.")
            return

        out_fonts = {}
        for raw_font, cb in self.font_comboboxes.items():
            selection = cb.currentText()
            if selection == "-- USAR ARCHIVO .TTF --" and raw_font in self.font_custom_paths:
                out_fonts[raw_font] = {"type": "custom", "value": self.font_custom_paths[raw_font]}
            else:
                base_sel = selection if selection != "-- USAR ARCHIVO .TTF --" else "Helvetica (Base)"
                out_fonts[raw_font] = {"type": "base", "value": self.font_to_pdf_code[base_sel]}

        out_modes = {}
        for p, widgets in self.page_widgets.items():
            mode_str = "editorial" if widgets["combo"].currentText() == "Editorial (Fondo Limpio)" else "standard"
            out_modes[p] = {"mode": mode_str, "bg_path": widgets["path"]}

        # GUARDAMOS EN LA VARIABLE MAESTRA PERMANENTE
        self.final_configuration = {
            "selected_pages": list(range(start, end + 1)),
            "font_mappings": out_fonts,
            "page_modes": out_modes
        }
        self.accept()

    def get_results(self):
        self.exec()
        # Retorna la variable maestra construida justo antes de cerrarse
        return self.final_configuration