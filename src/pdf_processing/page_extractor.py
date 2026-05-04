import fitz
from pydantic import BaseModel
from typing import List, Tuple, Set

class TextBlock(BaseModel):
    text: str
    bbox: Tuple[float, float, float, float]
    primary_font: str
    font_size: float
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
                if block.get("type") == 0: # Bloque de texto
                    current_text = ""
                    current_bbox = None
                    current_font = None
                    current_size = None
                    
                    for line in block.get("lines", []):
                        if not line.get("spans"): continue
                        
                        # Tomamos la fuente predominante de la línea
                        first_span = line["spans"][0]
                        line_font = first_span.get("font", "Unknown")
                        line_size = first_span.get("size", 12.0)
                        line_text = "".join([s.get("text", "") for s in line["spans"]]).strip()
                        
                        if not line_text: continue
                        unique_fonts.add(line_font)

                        # Si es la primera línea del bloque, inicializamos
                        if current_font is None:
                            current_font = line_font
                            current_size = line_size
                            current_bbox = list(line["bbox"])
                            current_text = line_text
                        else:
                            # CRÍTICO: Si la fuente cambia, o el tamaño cambia más de 1 punto,
                            # significa que pasamos de Título a Cuerpo (o viceversa). 
                            # CORTAMOS EL BLOQUE AQUÍ.
                            if current_font != line_font or abs(current_size - line_size) > 1.0:
                                blocks_extracted.append(TextBlock(
                                    text=current_text, bbox=tuple(current_bbox),
                                    primary_font=current_font, font_size=current_size,
                                    page_num=page_num + 1, char_count=len(current_text)
                                ))
                                # Reiniciamos para el nuevo estilo
                                current_font = line_font
                                current_size = line_size
                                current_bbox = list(line["bbox"])
                                current_text = line_text
                            else:
                                # Tienen el mismo estilo, pertenecen al mismo párrafo
                                current_text += " " + line_text
                                # Expandimos la caja delimitadora para abarcar esta nueva línea
                                current_bbox[0] = min(current_bbox[0], line["bbox"][0])
                                current_bbox[1] = min(current_bbox[1], line["bbox"][1])
                                current_bbox[2] = max(current_bbox[2], line["bbox"][2])
                                current_bbox[3] = max(current_bbox[3], line["bbox"][3])
                                
                    # Guardar el último sub-bloque procesado
                    if current_text:
                        blocks_extracted.append(TextBlock(
                            text=current_text, bbox=tuple(current_bbox),
                            primary_font=current_font, font_size=current_size,
                            page_num=page_num + 1, char_count=len(current_text)
                        ))
        doc.close()
        return blocks_extracted, unique_fonts
    except Exception as e:
        raise RuntimeError(f"Error procesando el PDF: {str(e)}")