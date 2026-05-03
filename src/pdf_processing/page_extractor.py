import fitz
from pydantic import BaseModel
from typing import List, Tuple, Set

class TextBlock(BaseModel):
    text: str
    bbox: Tuple[float, float, float, float]
    primary_font: str
    font_size: float  # NUEVO: Capturar tamaño de letra
    page_num: int
    char_count: int

def extract_text_elements(pdf_path: str) -> Tuple[List[TextBlock], Set[str]]:
    blocks_extracted = []
    unique_fonts = set()
    
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            dict_text = page.get_text("dict")
            
            for block in dict_text.get("blocks", []):
                if block.get("type") == 0:
                    block_text = ""
                    primary_font = "Unknown"
                    primary_size = 12.0
                    
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            if text:
                                block_text += text + " "
                                if primary_font == "Unknown":
                                    primary_font = span.get("font", "Unknown")
                                    primary_size = span.get("size", 12.0) # Capturamos el tamaño
                                unique_fonts.add(span.get("font", "Unknown"))
                    
                    block_text = block_text.strip()
                    if block_text:
                        blocks_extracted.append(TextBlock(
                            text=block_text,
                            bbox=block.get("bbox"),
                            primary_font=primary_font,
                            font_size=primary_size, # Lo guardamos
                            page_num=page_num + 1,
                            char_count=len(block_text)
                        ))
        doc.close()
        return blocks_extracted, unique_fonts
    except Exception as e:
        raise RuntimeError(f"Error procesando el PDF: {str(e)}")