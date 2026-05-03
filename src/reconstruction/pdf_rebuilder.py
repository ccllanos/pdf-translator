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
        logging.info("Iniciando reconstrucción con algoritmo seguro de escalado...")

        for block in translated_blocks:
            page = self.doc[block['page_num'] - 1]
            bbox = block['bbox']
            new_text = block['translated_text']
            
            if not new_text or new_text.isspace():
                continue

            # FASE 1: Destrucción
            page.add_redact_annot(bbox, fill=(1, 1, 1))
            page.apply_redactions()

            # FASE 2: Preparación matemática segura de la caja
            rect = fitz.Rect(bbox)
            rect.normalize()  # CRÍTICO: Previene que la caja esté invertida matemáticamente
            
            # Margen de seguridad más amplio para traducciones al español
            rect.x1 += 30  # Expandir ancho (Word Wrap)
            rect.y1 += 20  # Expandir alto (Multilínea)
            
            clean_original_font = self._clean_font_name(block['font_name'])
            safe_font = self.user_font_mapping.get(clean_original_font, "helv")
            
            # FASE 3: Inyección Segura (Safe Shrink-to-Fit)
            current_size = block['font_size']
            min_size = 6.0  # Límite absoluto para no quedar ciego
            texto_insertado = False

            while current_size >= min_size:
                # Intentamos insertar con el tamaño actual
                resultado = page.insert_textbox(
                    rect, 
                    new_text, 
                    fontsize=current_size, 
                    fontname=safe_font, 
                    color=(0, 0, 0), 
                    align=0
                )
                
                if resultado >= 0:
                    # Éxito: El texto cupo perfectamente sin invertirse
                    texto_insertado = True
                    break
                else:
                    # Fallo: Es muy grande. Reducimos 1 punto y volvemos a intentar
                    current_size -= 1.0

            # FALLBACK DE EMERGENCIA: Si ni siquiera en tamaño 6 cabe en la caja
            if not texto_insertado:
                logging.warning(f"Texto demasiado largo para la caja. Forzando inyección libre.")
                # Lo inyectamos forzosamente en la esquina superior izquierda a 8pts
                punto_seguro = fitz.Point(rect.x0, rect.y0 + 8)
                page.insert_text(
                    punto_seguro, 
                    new_text, 
                    fontsize=8, 
                    fontname=safe_font, 
                    color=(0, 0, 0)
                )

        self.doc.save(self.output_pdf, garbage=4, deflate=True)
        self.doc.close()
        logging.info(f"✅ Documento generado de forma segura en: {self.output_pdf}")