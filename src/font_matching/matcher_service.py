from typing import Set, Dict, List
from .cloud_fonts_api import CloudFontsAPI

class FontMatcherService:
    """Orquesta la identificación y coincidencia de tipografías."""
    
    def __init__(self):
        self.cloud_api = CloudFontsAPI()
        
        # Diccionario para normalizar los nombres internos que usan los PDFs
        self.pdf_font_mappings = {
            "helv": "Helvetica",
            "tiro": "Times New Roman",
            "cour": "Courier",
            "symb": "Symbol",
            "zadb": "ZapfDingbats"
        }

    def normalize_name(self, raw_name: str) -> str:
        """Limpia prefijos (ej: ABCDEF+Arial) y normaliza acrónimos del PDF."""
        # Limpiar subconjuntos de PDF (texto antes del '+')
        clean_name = raw_name.split('+')[-1] if '+' in raw_name else raw_name
        
        # Buscar en el mapa de normalización
        return self.pdf_font_mappings.get(clean_name.lower(), clean_name)

    def analyze_fonts(self, extracted_fonts: Set[str]) -> List[Dict]:
        """
        Toma las fuentes extraídas, las normaliza y las busca en la nube.
        Genera el reporte de estado de cada una.
        """
        report_data = []
        for raw_font in extracted_fonts:
            real_name = self.normalize_name(raw_font)
            cloud_result = self.cloud_api.search_font(real_name)
            
            status = "✅ DISPONIBLE EN LA NUBE" if cloud_result["found"] else "⚠️ NO DISPONIBLE (Sustituir)"
            
            report_data.append({
                "raw_name": raw_font,
                "real_name": real_name,
                "status_icon": status,
                "provider": cloud_result["provider"],
                "action": cloud_result["action"]
            })
            
        return report_data