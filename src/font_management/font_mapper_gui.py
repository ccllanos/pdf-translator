from typing import Dict, List
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QComboBox, QPushButton, QGridLayout, QFileDialog)
from PySide6.QtCore import Qt

class FontMapperGUI(QDialog):
    def __init__(self, font_cloud_report: List[Dict]):
        super().__init__()
        self.font_cloud_report = font_cloud_report
        self.final_mapping = {}
        
        # Diccionarios para rastrear los widgets de cada fila
        self.comboboxes = {}
        self.file_labels = {}
        self.custom_paths = {}
        
        self.font_to_pdf_code = {
            "Helvetica (Base)": "helv",
            "Times-Roman (Base)": "tiro",
            "Courier (Base)": "cour",
            "Symbol (Base)": "symb",
            "ZapfDingbats (Base)": "zadb"
        }
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Inspector de Fuentes Inteligente")
        self.resize(750, 400)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<h2 style='color:#2c3e50;'>🎨 Mapeo de Tipografías Inteligente</h2>"))
        layout.addWidget(QLabel("Se ha consultado la base de datos en la nube. Selecciona una fuente base o carga un archivo .ttf local."))
        layout.addSpacing(15)

        grid = QGridLayout()
        grid.addWidget(QLabel("<b>Fuente en PDF</b>"), 0, 0)
        grid.addWidget(QLabel("<b>Estado Nube</b>"), 0, 1)
        grid.addWidget(QLabel("<b>Acción de Reemplazo</b>"), 0, 2)
        grid.addWidget(QLabel("<b>Archivo Custom (.ttf)</b>"), 0, 3)

        for row, font_info in enumerate(self.font_cloud_report, start=1):
            raw_name = font_info['raw_name']
            real_name = font_info['real_name']
            
            # 1. Nombre original
            grid.addWidget(QLabel(f"• {raw_name}"), row, 0)
            
            # 2. Estado en la nube
            color = "green" if "DISPONIBLE" in font_info['status_icon'] else "red"
            status_lbl = QLabel(f"<span style='color:{color};'>{font_info['status_icon']}</span>")
            grid.addWidget(status_lbl, row, 1)
            
            # 3. Dropdown base
            cb = QComboBox()
            cb.addItems(list(self.font_to_pdf_code.keys()) + ["-- USAR ARCHIVO .TTF --"])
            
            # Autoselección inteligente
            if "times" in real_name.lower() or "serif" in real_name.lower():
                cb.setCurrentText("Times-Roman (Base)")
            else:
                cb.setCurrentText("Helvetica (Base)")
                
            grid.addWidget(cb, row, 2)
            self.comboboxes[raw_name] = cb
            
            # 4. Botón y Label para TTF Custom
            btn_layout = QHBoxLayout()
            btn_browse = QPushButton("Examinar...")
            lbl_file = QLabel("No seleccionado")
            lbl_file.setStyleSheet("color: gray; font-size: 10px;")
            
            # Conectar botón pasándole el raw_name
            btn_browse.clicked.connect(lambda n=raw_name, c=cb, l=lbl_file: self._browse_font(n, c, l))

            
            btn_layout.addWidget(btn_browse)
            btn_layout.addWidget(lbl_file)
            grid.addLayout(btn_layout, row, 3)
            
            self.file_labels[raw_name] = lbl_file

        layout.addLayout(grid)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        
        btn_confirm = QPushButton("Confirmar y Traducir ➔")
        btn_confirm.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
        btn_confirm.clicked.connect(self.accept)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_confirm)
        layout.addLayout(btn_layout)

    def _browse_font(self, font_name, combobox, label):
        """Abre el explorador de Windows directamente en la carpeta de fuentes."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Seleccionar fuente TTF/OTF", 
            "C:\\Windows\\Fonts",
            "Fuentes (*.ttf *.otf)"
        )
        if file_path:
            short_name = file_path.split("/")[-1]
            
            # BLOQUEO DE ARCHIVOS FANTASMA DE MAC
            if short_name.startswith("._") or "__MACOSX" in file_path:
                QMessageBox.warning(self, "Archivo Inválido", 
                                  f"Has seleccionado '{short_name}', que es un archivo residual basura de Mac, no una fuente real.\n\nPor favor, busca el archivo original que NO empieza con '._'")
                return

            combobox.setCurrentText("-- USAR ARCHIVO .TTF --")
            label.setText(short_name)
            label.setStyleSheet("color: blue; font-size: 10px; font-weight: bold;")
            self.custom_paths[font_name] = file_path

    def get_mapping(self) -> Dict[str, Dict]:
        if self.exec() == QDialog.Accepted:
            for raw_font, cb in self.comboboxes.items():
                selection = cb.currentText()
                if selection == "-- USAR ARCHIVO .TTF --" and raw_font in self.custom_paths:
                    self.final_mapping[raw_font] = {"type": "custom", "value": self.custom_paths[raw_font]}
                else:
                    # Si eligió TTF pero no cargó archivo, o si eligió Base
                    base_selection = selection if selection != "-- USAR ARCHIVO .TTF --" else "Helvetica (Base)"
                    self.final_mapping[raw_font] = {"type": "base", "value": self.font_to_pdf_code[base_selection]}
            return self.final_mapping
        return None