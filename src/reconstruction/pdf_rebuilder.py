import fitz
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class PDFRebuilder:
    def __init__(self, input_pdf: str, output_pdf: str, user_font_mapping: Dict[str, str]):
        self.input_pdf = input_pdf
        self.output_pdf = output_pdf
        self.user_font_mapping = user_font_mapping
        self.doc = fitz.open(self.input_pdf)

    def _clean_font_name(self, raw_font: str) -> str:
        return raw_font.split('+')[-1] if '+' in raw_font else raw_font

    def destroy_and_rebuild(self, translated_blocks: List[Dict]):
        logging.info("Iniciando reconstrucción con ajuste de fuente milimétrico...")

        for block in translated_blocks:
            page = self.doc[block['page_num'] - 1]
            bbox = block['bbox']
            new_text = block['translated_text']
            
            if not new_text or new_text.isspace():
                continue

            # FASE 1: Destrucción
            page.add_redact_annot(bbox, fill=(1, 1, 1))
            page.apply_redactions()

            # FASE 2: Preparación Estricta de la Caja
            rect = fitz.Rect(bbox)
            rect.normalize()
            
            # CRÍTICO: Reducimos la generosidad drásticamente.
            # Solo damos 2 puntos verticales para tolerar letras que "cuelgan" (como g, p, q)
            # y 5 puntos horizontales para dar un pequeño margen de respiración.
            # Esto PROHÍBE físicamente el salto de línea.
            rect.x1 += 5  
            rect.y1 += 2  
            
            clean_original_font = self._clean_font_name(block['font_name'])
            safe_font = self.user_font_mapping.get(clean_original_font, "helv")
            
            # FASE 3: Inyección Algorítmica de Precisión (Shrink-to-Fit Granular)
            current_size = float(block['font_size'])
            min_size = 5.0
            texto_insertado = False

            while current_size >= min_size:
                resultado = page.insert_textbox(
                    rect, 
                    new_text, 
                    fontsize=current_size, 
                    fontname=safe_font, 
                    color=(0, 0, 0), 
                    align=0
                )
                
                if resultado >= 0:
                    texto_insertado = True
                    # Logeamos a qué tamaño se logró encajar perfectamente
                    if current_size < block['font_size']:
                        logging.info(f"Ajuste preciso logrado: '{new_text[:15]}...' reducido de {block['font_size']}pt a {current_size}pt")
                    break
                else:
                    # Reducción fina: 0.5 puntos en lugar de 1 entero para un encaje mucho más natural
                    current_size -= 0.5

            if not texto_insertado:
                logging.warning(f"Extrema longitud. Forzando inyección en 5pt para: {new_text[:15]}...")
                punto_seguro = fitz.Point(rect.x0, rect.y0 + 5)
                page.insert_text(punto_seguro, new_text, fontsize=5, fontname=safe_font, color=(0, 0, 0))

        self.doc.save(self.output_pdf, garbage=4, deflate=True)
        self.doc.close()
        logging.info(f"✅ Documento generado con ajuste algorítmico perfecto en: {self.output_pdf}")