import logging
from typing import List, Set
# AQUÍ ESTÁ LA CORRECCIÓN: Importamos TextBlock en lugar de TextElement
from .page_extractor import extract_text_elements, TextBlock

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class PDFAnalyzer:
    """Clase responsable de orquestar el análisis estructural del documento."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.elements: List[TextBlock] = []  # Usamos el nuevo modelo de bloques
        self.fonts: Set[str] = set()
        
    def analyze(self):
        """Ejecuta la extracción y prepara los datos para la traducción."""
        logging.info(f"Iniciando análisis estructural y de Layout de: {self.filepath}")
        self.elements, self.fonts = extract_text_elements(self.filepath)
        logging.info(f"Análisis completado. {len(self.elements)} bloques de texto lógicos extraídos.")
        
    def get_font_report(self) -> str:
        """Genera el informe de tipografías requeridas para la preservación visual."""
        report = []
        report.append("========================================")
        report.append(f"DOCUMENTO: {self.filepath}")
        report.append("FUENTES DETECTADAS (REQUERIDAS PARA 1:1):")
        report.append("========================================")
        for font in self.fonts:
            report.append(f" - {font} (Estado: Pendiente de validación online)")
        return "\n".join(report)