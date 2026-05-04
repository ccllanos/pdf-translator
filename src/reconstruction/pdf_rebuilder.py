import fitz
import logging
import os
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class PDFRebuilder:
    def __init__(self, input_pdf: str, output_pdf: str, user_font_mapping: Dict[str, Dict]):
        self.input_pdf = input_pdf
        self.output_pdf = output_pdf
        self.user_font_mapping = user_font_mapping
        self.doc = fitz.open(self.input_pdf)
        self.custom_font_counter = 0

    def _clean_font_name(self, raw_font: str) -> str:
        return raw_font.split('+')[-1] if '+' in raw_font else raw_font

    def _wrap_text_math(self, text: str, font_obj: fitz.Font, fontsize: float, max_width: float) -> List[str]:
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
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

    def apply_page_rendering(self, page_num: int, mode: str, bg_path: str, blocks: List[Dict[str, Any]]):
        page = self.doc[page_num - 1]

        # 1. Aplicar Fondo Limpio si existe
        if mode == "editorial" and bg_path and os.path.exists(bg_path):
            page.insert_image(page.rect, filename=bg_path)

        # 2. Inyección de Bloques
        for block in blocks:
            bbox = block['bbox']
            new_text = block['translated_text']
            raw_font = block['font_name']
            
            if not new_text or new_text.isspace():
                continue

            # CRÍTICO: Corrección del Rectángulo Blanco.
            if mode == "editorial":
                # La redacción no tiene color (transparente) y NO borramos imágenes
                page.add_redact_annot(bbox, cross_out=False)
                page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
            else:
                # La redacción tiene color blanco (tapa el fondo escaneado base)
                page.add_redact_annot(bbox, fill=(1, 1, 1), cross_out=False)
                page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

            rect = fitz.Rect(bbox)
            rect.normalize()
            box_width = rect.width
            box_height = rect.height
            
            is_single_line = box_height <= (block['font_size'] * 1.8)

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

            if is_single_line:
                len_1pt = font_obj.text_length(new_text, fontsize=1) if font_obj else 0
                final_size = min(box_width / len_1pt, block['font_size'] * 1.15) if len_1pt > 0 else block['font_size']
                page.insert_text(fitz.Point(rect.x0, rect.y0 + (final_size * 0.85)), new_text, fontsize=final_size, fontname=target_fontname, color=(0, 0, 0))
            else:
                current_size = float(block['font_size'])
                best_lines = []
                best_size = current_size

                while current_size >= 6.0:
                    lines = self._wrap_text_math(new_text, font_obj, current_size, box_width)
                    if (len(lines) * (current_size * 1.2)) <= box_height * 1.1:
                        best_lines = lines
                        best_size = current_size
                        break
                    current_size -= 0.5
                
                if not best_lines:
                    best_size = 6.0
                    best_lines = self._wrap_text_math(new_text, font_obj, best_size, box_width)

                N = len(best_lines)
                if N == 1:
                    page.insert_text(fitz.Point(rect.x0, rect.y0 + (best_size * 0.85)), best_lines[0], fontsize=best_size, fontname=target_fontname, color=(0, 0, 0))
                else:
                    gap = min((box_height - (N * best_size)) / (N - 1), best_size * 0.6)
                    if gap < best_size * 0.15: gap = best_size * 0.15
                    y_cursor = rect.y0 + (best_size * 0.85)
                    for line in best_lines:
                        page.insert_text(fitz.Point(rect.x0, y_cursor), line, fontsize=best_size, fontname=target_fontname, color=(0, 0, 0))
                        y_cursor += best_size + gap

    def save(self):
        """Guarda los cambios estructurales en el PDF final."""
        self.doc.save(self.output_pdf, garbage=4, deflate=True)
        self.doc.close()