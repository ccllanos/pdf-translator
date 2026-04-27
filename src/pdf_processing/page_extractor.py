import fitz  # PyMuPDF
from pydantic import BaseModel
from typing import List, Tuple, Set

class TextElement(BaseModel):
    """Modelo estricto para preservar la información de cada elemento de texto."""
    text: str
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    font_name: str
    font_size: float
    page_num: int

def extract_text_elements(pdf_path: str) -> Tuple[List[TextElement], Set[str]]:
    """
    Analiza el PDF y extrae el texto junto con sus coordenadas exactas y tipografía.
    También recopila un set de todas las fuentes únicas utilizadas (para el informe).
    """
    elements = []
    unique_fonts = set()
    
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Extraer en formato diccionario para obtener metadata de fuentes
            dict_text = page.get_text("dict")
            
            for block in dict_text.get("blocks", []):
                if block.get("type") == 0:  # Tipo 0 es bloque de texto
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            if text:
                                font = span.get("font", "Unknown")
                                unique_fonts.add(font)
                                
                                elements.append(TextElement(
                                    text=text,
                                    bbox=span.get("bbox"),
                                    font_name=font,
                                    font_size=span.get("size"),
                                    page_num=page_num + 1
                                ))
        doc.close()
        return elements, unique_fonts
    except Exception as e:
        raise RuntimeError(f"Error procesando el PDF {pdf_path}: {str(e)}")