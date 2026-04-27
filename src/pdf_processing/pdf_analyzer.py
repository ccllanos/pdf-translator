import logging
from typing import List, Set
from .page_extractor import extract_text_elements, TextElement

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class PDFAnalyzer:
    """Clase responsable de orquestar el análisis estructural del documento."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.elements: List[TextElement] = []
        self.fonts: Set[str] = set()
        
    def analyze(self):
        """Ejecuta la extracción y prepara los datos para la traducción."""
        logging.info(f"Iniciando análisis estructural de: {self.filepath}")
        self.elements, self.fonts = extract_text_elements(self.filepath)
        logging.info(f"Análisis completado. {len(self.elements)} fragmentos de texto extraídos.")
        
    def get_font_report(self) -> str:
        """Genera el informe de tipografías requeridas para la preservación visual."""
        report = []
        report.append("========================================")
        report.append(f"DOCUMENTO: {self.filepath}")
        report.append("FUENTES DETECTADAS (REQUERIDAS PARA 1:1):")
        report.append("========================================")
        for font in self.fonts:
            # En etapas futuras, aquí se conectará con font_matching
            report.append(f" - {font} (Estado: Pendiente de validación online)")
        return "\n".join(report)