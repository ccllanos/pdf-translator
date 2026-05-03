from typing import Set, Dict
# Cambiado a PySide6
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QComboBox, QPushButton, QGridLayout)
from PySide6.QtCore import Qt

class FontMapperGUI(QDialog):
    def __init__(self, pdf_fonts: Set[str]):
        super().__init__()
        self.pdf_fonts = self._clean_font_names(pdf_fonts)
        self.final_mapping = {}
        self.comboboxes = {}
        
        self.available_system_fonts = [
            "Helvetica (Sans-Serif)", 
            "Times-Roman (Serif)", 
            "Courier (Mono)", 
            "Symbol", 
            "ZapfDingbats"
        ]
        
        self.font_to_pdf_code = {
            "Helvetica (Sans-Serif)": "helv",
            "Times-Roman (Serif)": "tiro",
            "Courier (Mono)": "cour",
            "Symbol": "symb",
            "ZapfDingbats": "zadb"
        }
        
        self._init_ui()

    def _clean_font_names(self, raw_fonts: Set[str]) -> Set[str]:
        return {f.split('+')[-1] if '+' in f else f for f in raw_fonts}

    def _init_ui(self):
        self.setWindowTitle("Inspector de Fuentes - PDF Translator")
        self.resize(550, 300)
        
        layout = QVBoxLayout(self)

        header = QLabel("🎨 Mapeo de Tipografías")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)

        desc = QLabel("Se han detectado las siguientes fuentes en el documento.\nSelecciona con cuál deseas reemplazarlas en la traducción:")
        layout.addWidget(desc)
        layout.addSpacing(15)

        grid = QGridLayout()
        grid.addWidget(QLabel("<b>Fuente Original (PDF)</b>"), 0, 0)
        grid.addWidget(QLabel("<b>Fuente de Reemplazo</b>"), 0, 1)

        row = 1
        for font in self.pdf_fonts:
            lbl = QLabel(f"• {font}")
            cb = QComboBox()
            cb.addItems(self.available_system_fonts)
            
            font_lower = font.lower()
            if "times" in font_lower or "serif" in font_lower:
                cb.setCurrentText("Times-Roman (Serif)")
            elif "cour" in font_lower or "mono" in font_lower:
                cb.setCurrentText("Courier (Mono)")
            else:
                cb.setCurrentText("Helvetica (Sans-Serif)")
            
            cb.setStyleSheet("padding: 3px;")
            grid.addWidget(lbl, row, 0)
            grid.addWidget(cb, row, 1)
            
            self.comboboxes[font] = cb
            row += 1

        layout.addLayout(grid)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        
        btn_cancel = QPushButton("Cancelar y Abortar")
        btn_cancel.clicked.connect(self.reject)
        
        btn_confirm = QPushButton("Confirmar y Traducir ➔")
        btn_confirm.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
        btn_confirm.clicked.connect(self.accept)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_confirm)
        
        layout.addLayout(btn_layout)

    def get_mapping(self) -> Dict[str, str]:
        result = self.exec() 
        
        # En PySide6 evaluamos QDialog.Accepted
        if result == QDialog.Accepted:
            for original_font, cb in self.comboboxes.items():
                self.final_mapping[original_font] = self.font_to_pdf_code[cb.currentText()]
            return self.final_mapping
            
        return None