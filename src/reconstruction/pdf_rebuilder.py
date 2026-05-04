import fitz
import logging
import os
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class PDFRebuilder:
    def __init__(self, input_pdf: str, output_pdf: str, user_font_mapping: Dict[str, Dict], bg_folder: str = None):
        self.input_pdf = input_pdf
        self.output_pdf = output_pdf
        self.user_font_mapping = user_font_mapping
        self.bg_folder = bg_folder
        self.doc = fitz.open(self.input_pdf)
        self.custom_font_counter = 0

    def _clean_font_name(self, raw_font: str) -> str:
        return raw_font.split('+')[-1] if '+' in raw_font else raw_font

    def _apply_backgrounds(self):
        if not self.bg_folder or not os.path.isdir(self.bg_folder):
            return

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            human_page = page_num + 1
            bg_path = None
            for ext in ['.png', '.jpg', '.jpeg']:
                test_path = os.path.join(self.bg_folder, f"page_{human_page}{ext}")
                if os.path.exists(test_path):
                    bg_path = test_path
                    break
            
            if bg_path:
                logging.info(f"Aplicando fondo limpio a la página {human_page}...")
                page.insert_image(page.rect, filename=bg_path)

    def destroy_and_rebuild(self, translated_blocks: List[Dict]):
        self._apply_backgrounds()
        logging.info("Iniciando reconstrucción tipográfica respetando arte e interlineado...")

        for block in translated_blocks:
            page = self.doc[block['page_num'] - 1]
            bbox = block['bbox']
            new_text = block['translated_text']
            raw_font = block['font_name']
            
            if not new_text or new_text.isspace():
                continue

            # === FASE 1: DESTRUCCIÓN NO DESTRUCTIVA DEL ARTE ===
            if self.bg_folder:
                # MODO EDITORIAL: Fondo provisto.
                # Como ya tapamos el arte original con la imagen nueva, aplicamos redacción estándar.
                # (Se borra la memoria del texto de fondo).
                page.add_redact_annot(bbox)
                page.apply_redactions()
            else:
                # MODO NORMAL: D&D sin fondo de reemplazo.
                # Aquí pintamos el rectángulo blanco, pero usamos la constante correcta
                # images=fitz.PDF_REDACT_IMAGE_NONE para proteger las fotos e ilustraciones que
                # pudieran estar cruzando la caja de texto.
                page.add_redact_annot(bbox, fill=(1, 1, 1))
                page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

            rect = fitz.Rect(bbox)
            rect.normalize()
            box_width = rect.width
            box_height = rect.height
            
            is_single_line = box_height <= (block['font_size'] * 1.8)

            # === FASE 2: CARGA DE FUENTES ===
            mapping_info = self.user_font_mapping.get(raw_font, {"type": "base", "value": "helv"})
            font_obj = None

            if mapping_info["type"] == "custom":
                ttf_path = mapping_info["value"]
                if os.path.exists(ttf_path):
                    target_fontname = f"cfont_{self.custom_font_counter}"
                    try:
                        page.insert_font(fontname=target_fontname, fontfile=ttf_path)
                        font_obj = fitz.Font(fontfile=ttf_path)
                        self.custom_font_counter += 1
                    except:
                        target_fontname = "helv"
                else:
                    target_fontname = "helv"
            else:
                target_fontname = mapping_info["value"]
                font_obj = fitz.Font(fontname=target_fontname)

            # === FASE 3: INYECCIÓN CON ESTEQUIOMETRÍA EDITORIAL ===
            if is_single_line:
                if font_obj:
                    len_1pt = font_obj.text_length(new_text, fontsize=1)
                    if len_1pt > 0:
                        perfect_size = box_width / len_1pt
                        final_size = min(perfect_size, block['font_size'] * 1.15)
                    else:
                        final_size = block['font_size']
                else:
                    final_size = block['font_size']

                baseline_y = rect.y0 + (final_size * 0.85)
                punto_base = fitz.Point(rect.x0, baseline_y)
                page.insert_text(punto_base, new_text, fontsize=final_size, fontname=target_fontname, color=(0, 0, 0))
                
            else:
                rect.x1 += 5
                rect.y1 += 5
                
                current_size = float(block['font_size'])
                texto_insertado = False
                
                # INTERLINEADO EDITORIAL
                espaciado_lineal = 1.35 

                while current_size >= 6.0:
                    resultado = page.insert_textbox(
                        rect, new_text, 
                        fontsize=current_size, 
                        fontname=target_fontname, 
                        color=(0, 0, 0), 
                        align=0,
                        lineheight=espaciado_lineal
                    )
                    
                    if resultado >= 0:
                        texto_insertado = True
                        break
                    else:
                        current_size -= 0.5

                if not texto_insertado:
                    punto_seguro = fitz.Point(rect.x0, rect.y0 + 8)
                    page.insert_text(punto_seguro, new_text, fontsize=8, fontname=target_fontname, color=(0, 0, 0))

        self.doc.save(self.output_pdf, garbage=4, deflate=True)
        self.doc.close()
        logging.info(f"✅ Documento editorial generado en: {self.output_pdf}")