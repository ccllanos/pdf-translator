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

    def _wrap_text_math(self, text: str, font_obj: fitz.Font, fontsize: float, max_width: float) -> List[str]:
        """Algoritmo matemático para cortar el texto en líneas perfectas respetando el ancho."""
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            # Medimos matemáticamente si la línea + la nueva palabra cabe en el ancho
            if font_obj.text_length(test_line, fontsize=fontsize) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    lines.append(word)
                    current_line = ""
        if current_line:
            lines.append(current_line)
        return lines

    def destroy_and_rebuild(self, translated_blocks: List[Dict]):
        self._apply_backgrounds()
        logging.info("Iniciando reconstrucción con estequiometría de párrafos...")

        for block in translated_blocks:
            page = self.doc[block['page_num'] - 1]
            bbox = block['bbox']
            new_text = block['translated_text']
            raw_font = block['font_name']
            
            if not new_text or new_text.isspace():
                continue

            # === FASE 1: DESTRUCCIÓN TRANSPARENTE (Preservación del Arte) ===
            # Sin parámetro 'fill'. Esto borra la información vectorial del texto original
            # pero DEJA INTACTOS los píxeles del pergamino, arte o textura que haya debajo.
            page.add_redact_annot(bbox, cross_out=False)
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

            rect = fitz.Rect(bbox)
            rect.normalize()
            box_width = rect.width
            box_height = rect.height
            
            is_single_line = box_height <= (block['font_size'] * 1.8)

            # === FASE 2: CARGA DE FUENTES Y MÉTRICAS ===
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
                        font_obj = fitz.Font(fontname=target_fontname)
                else:
                    target_fontname = "helv"
                    font_obj = fitz.Font(fontname=target_fontname)
            else:
                target_fontname = mapping_info["value"]
                font_obj = fitz.Font(fontname=target_fontname)

            # === FASE 3: ESTEQUIOMETRÍA Y DISTRIBUCIÓN ARMÓNICA ===
            if is_single_line:
                # Títulos: Ajuste exacto al ancho
                len_1pt = font_obj.text_length(new_text, fontsize=1)
                if len_1pt > 0:
                    final_size = min(box_width / len_1pt, block['font_size'] * 1.15)
                else:
                    final_size = block['font_size']

                baseline_y = rect.y0 + (final_size * 0.85)
                page.insert_text(fitz.Point(rect.x0, baseline_y), new_text, fontsize=final_size, fontname=target_fontname, color=(0, 0, 0))
                
            else:
                # Cuerpos de Texto: Algoritmo de Distribución Vertical
                current_size = float(block['font_size'])
                min_size = 6.0
                best_lines = []
                best_size = current_size

                # Buscamos el tamaño de fuente perfecto donde el texto envuelto quepa en la caja
                while current_size >= min_size:
                    lines = self._wrap_text_math(new_text, font_obj, current_size, box_width)
                    estimated_height = len(lines) * (current_size * 1.2) # Altura base
                    if estimated_height <= box_height * 1.1: # Permitimos un desborde milimétrico (10%)
                        best_lines = lines
                        best_size = current_size
                        break
                    current_size -= 0.5
                
                if not best_lines:
                    best_size = 6.0
                    best_lines = self._wrap_text_math(new_text, font_obj, best_size, box_width)

                # Inyección Línea por Línea
                N = len(best_lines)
                if N == 1:
                    baseline_y = rect.y0 + (best_size * 0.85)
                    page.insert_text(fitz.Point(rect.x0, baseline_y), best_lines[0], fontsize=best_size, fontname=target_fontname, color=(0, 0, 0))
                else:
                    # CÁLCULO DE INTERLINEADO (LEADING):
                    # Espacio total libre repartido entre los huecos de las líneas
                    gap = (box_height - (N * best_size)) / (N - 1)
                    
                    # Límites armónicos: Ni muy pegado, ni exageradamente separado
                    max_gap = best_size * 0.6
                    min_gap = best_size * 0.15
                    
                    if gap > max_gap: gap = max_gap
                    if gap < min_gap: gap = min_gap

                    # Coordenada 'Y' inicial (Línea base de la primera letra)
                    y_cursor = rect.y0 + (best_size * 0.85)
                    
                    for line in best_lines:
                        page.insert_text(fitz.Point(rect.x0, y_cursor), line, fontsize=best_size, fontname=target_fontname, color=(0, 0, 0))
                        y_cursor += best_size + gap # Avanzamos al siguiente renglón

        self.doc.save(self.output_pdf, garbage=4, deflate=True)
        self.doc.close()
        logging.info(f"✅ Documento editorial generado en: {self.output_pdf}")