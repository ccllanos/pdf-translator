import logging
from typing import List, Set
from .page_extractor import extract_text_elements, TextElement

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class PDFAnalyzer:
    """Clase responsable de orquestar el analisis estructural del documento."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.elements: List[TextElement] = []
        self.fonts: Set[str] = set()
        
    def analyze(self):
        """Ejecuta la extraccion y prepara los datos para la traduccion."""
        logging.info(f"Iniciando analisis estructural de: {self.filepath}")
        self.elements, self.fonts = extract_text_elements(self.filepath)
        logging.info(f"Analisis completado. {len(self.elements)} fragmentos de texto extraidos.")
        
    def get_font_report(self) -> str:
        """Genera el informe de tipografias requeridas para la preservacion visual."""
        report = []
        report.append("========================================")
        report.append(f"DOCUMENTO: {self.filepath}")
        report.append("FUENTES DETECTADAS (REQUERIDAS PARA 1:1):")
        report.append("========================================")
        for font in self.fonts:
            # En etapas futuras, aqui se conectara con font_matching
            report.append(f" - {font} (Estado: Pendiente de validacion online)")
        return "\n".join(report)