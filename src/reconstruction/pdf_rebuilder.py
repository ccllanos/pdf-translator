import fitz
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class PDFRebuilder:
    def __init__(self, input_pdf: str, output_pdf: str, user_font_mapping: Dict[str, str]):
        self.input_pdf = input_pdf
        self.output_pdf = output_pdf
        self.user_font_mapping = user_font_mapping # Recibe las decisiones de la GUI
        self.doc = fitz.open(self.input_pdf)

    def _clean_font_name(self, raw_font: str) -> str:
        return raw_font.split('+')[-1] if '+' in raw_font else raw_font

    def destroy_and_rebuild(self, translated_blocks: List[Dict]):
        logging.info("Iniciando reconstrucción aplicando el mapeo de fuentes del usuario...")

        for block in translated_blocks:
            page = self.doc[block['page_num'] - 1]
            bbox = block['bbox']
            new_text = block['translated_text']
            
            if not new_text or new_text.isspace():
                continue

            page.add_redact_annot(bbox, fill=(1, 1, 1))
            page.apply_redactions()

            rect = fitz.Rect(bbox)
            rect.x1 += 15 
            rect.y1 += 5  
            
            # Buscar la decisión del usuario basada en el nombre limpio de la fuente
            clean_original_font = self._clean_font_name(block['font_name'])
            
            # Si por algún motivo no está en el mapa, usamos Helvetica por defecto
            safe_font = self.user_font_mapping.get(clean_original_font, "helv")
            target_size = block['font_size']

            try:
                resultado = page.insert_textbox(rect, new_text, fontsize=target_size, fontname=safe_font, color=(0, 0, 0), align=0)
                
                if resultado < 0:
                    page.insert_textbox(rect, new_text, fontsize=-1, fontname=safe_font, color=(0, 0, 0), align=0)
                
            except Exception as e:
                logging.error(f"Error inyectando texto en {bbox}: {e}")

        self.doc.save(self.output_pdf, garbage=4, deflate=True)
        self.doc.close()