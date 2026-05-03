import fitz
import logging
import os
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class PDFRebuilder:
    def __init__(self, input_pdf: str, output_pdf: str, user_font_mapping: Dict[str, Dict]):
        self.input_pdf = input_pdf
        self.output_pdf = output_pdf
        self.user_font_mapping = user_font_mapping
        self.doc = fitz.open(self.input_pdf)
        self.custom_font_counter = 0

    def destroy_and_rebuild(self, translated_blocks: List[Dict]):
        logging.info("Iniciando reconstrucción. Incrustando fuentes físicas si aplica...")

        for block in translated_blocks:
            page = self.doc[block['page_num'] - 1]
            bbox = block['bbox']
            new_text = block['translated_text']
            raw_font = block['font_name']
            
            if not new_text or new_text.isspace():
                continue

            page.add_redact_annot(bbox, fill=(1, 1, 1))
            page.apply_redactions()

            rect = fitz.Rect(bbox)
            rect.normalize()
            rect.x1 += 5  
            rect.y1 += 2  
            
            # Recuperar la decisión del usuario
            mapping_info = self.user_font_mapping.get(raw_font, {"type": "base", "value": "helv"})
            
            target_fontname = "helv" # Fallback

            # Si es un archivo físico .ttf, debemos registrarlo en la página antes de usarlo
            if mapping_info["type"] == "custom":
                ttf_path = mapping_info["value"]
                if os.path.exists(ttf_path):
                    # Generamos un nombre interno único (ej: cfont_0)
                    target_fontname = f"cfont_{self.custom_font_counter}"
                    # ¡MAGIA! Incrustamos el archivo TTF dentro del PDF
                    page.insert_font(fontname=target_fontname, fontfile=ttf_path)
                    self.custom_font_counter += 1
                else:
                    logging.warning(f"No se encontró el archivo {ttf_path}. Usando base.")
            else:
                target_fontname = mapping_info["value"]

            # Inyección de Precisión
            current_size = float(block['font_size'])
            texto_insertado = False

            while current_size >= 5.0:
                resultado = page.insert_textbox(
                    rect, new_text, fontsize=current_size, 
                    fontname=target_fontname, color=(0, 0, 0), align=0
                )
                
                if resultado >= 0:
                    texto_insertado = True
                    break
                else:
                    current_size -= 0.5

            if not texto_insertado:
                punto_seguro = fitz.Point(rect.x0, rect.y0 + 5)
                page.insert_text(punto_seguro, new_text, fontsize=5, fontname=target_fontname, color=(0, 0, 0))

        self.doc.save(self.output_pdf, garbage=4, deflate=True)
        self.doc.close()
        logging.info(f"✅ Documento generado en: {self.output_pdf}")