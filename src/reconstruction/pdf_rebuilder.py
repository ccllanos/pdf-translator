import fitz
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class PDFRebuilder:
    def __init__(self, input_pdf: str, output_pdf: str):
        self.input_pdf = input_pdf
        self.output_pdf = output_pdf
        self.doc = fitz.open(self.input_pdf)
        
        # Mapeo de fuentes comunes a las 3 base nativas de PDF para asegurar compatibilidad
        self.font_mapper = {
            "times": "tiro",
            "tiro": "tiro",
            "helvetica": "helv",
            "helv": "helv",
            "arial": "helv",
            "courier": "cour"
        }

    def _get_safe_font(self, original_font: str) -> str:
        """Encuentra la fuente nativa más cercana a la original del PDF."""
        font_lower = original_font.lower()
        for key, pdf_font in self.font_mapper.items():
            if key in font_lower:
                return pdf_font
        return "helv" # Fuente de respaldo por defecto

    def destroy_and_rebuild(self, translated_blocks: List[Dict]):
        logging.info("Iniciando reconstrucción con preservación de fuentes y saltos de línea...")

        for block in translated_blocks:
            page = self.doc[block['page_num'] - 1]
            bbox = block['bbox']
            new_text = block['translated_text']
            
            if not new_text or new_text.isspace():
                continue

            # FASE 1: Destrucción
            page.add_redact_annot(bbox, fill=(1, 1, 1))
            page.apply_redactions()

            # FASE 2: Preparación de la caja (Word Wrap)
            rect = fitz.Rect(bbox)
            
            # Margen de seguridad: expandimos ligeramente la caja hacia la derecha y abajo
            # para dar espacio extra al español antes de hacer saltos de línea
            rect.x1 += 15 
            rect.y1 += 5  
            
            # Detectamos qué fuente usar y su tamaño
            safe_font = self._get_safe_font(block['font_name'])
            target_size = block['font_size']

            try:
                # Intento 1: Inyectar respetando el tamaño de fuente original y haciendo salto de línea
                resultado = page.insert_textbox(
                    rect, 
                    new_text, 
                    fontsize=target_size, 
                    fontname=safe_font, 
                    color=(0, 0, 0),
                    align=0
                )
                
                # Si el resultado es menor a 0, significa que el español es demasiado largo
                # y no cabe en la caja ni haciendo saltos de línea.
                if resultado < 0:
                    logging.info(f"Texto desborda caja original. Auto-reduciendo tamaño de letra...")
                    # Intento 2 (Shrink-to-Fit): fontsize=-1 obliga a PyMuPDF a reducir
                    # el tamaño de la letra hasta que encaje perfectamente dentro del rectángulo.
                    page.insert_textbox(
                        rect, 
                        new_text, 
                        fontsize=-1, 
                        fontname=safe_font, 
                        color=(0, 0, 0),
                        align=0
                    )
                
                # GUÍA VISUAL
                # page.draw_rect(rect, color=(0, 0, 1), width=0.5)

            except Exception as e:
                logging.error(f"Error inyectando texto en {bbox}: {e}")

        self.doc.save(self.output_pdf, garbage=4, deflate=True)
        self.doc.close()
        logging.info(f"✅ Documento generado: {self.output_pdf}")