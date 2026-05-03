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

    def _clean_font_name(self, raw_font: str) -> str:
        return raw_font.split('+')[-1] if '+' in raw_font else raw_font

    def destroy_and_rebuild(self, translated_blocks: List[Dict]):
        logging.info("Iniciando reconstrucción tipográfica de alta precisión...")

        for block in translated_blocks:
            page = self.doc[block['page_num'] - 1]
            bbox = block['bbox']
            new_text = block['translated_text']
            raw_font = block['font_name']
            
            if not new_text or new_text.isspace():
                continue

            # FASE 1: Destrucción
            page.add_redact_annot(bbox, fill=(1, 1, 1))
            page.apply_redactions()

            rect = fitz.Rect(bbox)
            rect.normalize()
            box_width = rect.width
            box_height = rect.height
            
            # Determinamos si es un título/frase corta (1 línea) o un párrafo
            is_single_line = box_height <= (block['font_size'] * 1.8)

            # FASE 2: Carga e Incrustación de Fuente
            mapping_info = self.user_font_mapping.get(raw_font, {"type": "base", "value": "helv"})
            target_fontname = "helv"
            font_obj = None # Objeto para medir matemáticamente la fuente

            if mapping_info["type"] == "custom":
                ttf_path = mapping_info["value"]
                if os.path.exists(ttf_path):
                    target_fontname = f"cfont_{self.custom_font_counter}"
                    try:
                        page.insert_font(fontname=target_fontname, fontfile=ttf_path)
                        font_obj = fitz.Font(fontfile=ttf_path) # Cargamos métricas
                        self.custom_font_counter += 1
                    except Exception as e:
                        logging.error(f"Error cargando fuente física: {e}")
                        target_fontname = "helv"
                else:
                    target_fontname = "helv"
            else:
                target_fontname = mapping_info["value"]
                font_obj = fitz.Font(fontname=target_fontname)

            # FASE 3: Inyección Inteligente (Headline vs Paragraph)
            if is_single_line:
                # === ALGORITMO ESTEQUIOMÉTRICO (ANCHO PERFECTO) ===
                if font_obj:
                    # Medimos cuánto ocupa el texto a tamaño 1pt
                    len_1pt = font_obj.text_length(new_text, fontsize=1)
                    if len_1pt > 0:
                        # Regla de 3: ¿Qué tamaño necesitamos para llenar el ancho de la caja?
                        perfect_size = box_width / len_1pt
                        
                        # Ponemos un límite: Que no crezca más de un 10% del original si el texto es muy corto
                        final_size = min(perfect_size, block['font_size'] * 1.1)
                    else:
                        final_size = block['font_size']
                else:
                    final_size = block['font_size']

                # Calculamos la línea base visual (aprox. 85% de la altura de la fuente)
                baseline_y = rect.y0 + (final_size * 0.85)
                punto_base = fitz.Point(rect.x0, baseline_y)
                
                # Usamos insert_text para ignorar los límites verticales de la caja
                page.insert_text(punto_base, new_text, fontsize=final_size, fontname=target_fontname, color=(0, 0, 0))
                logging.info(f"Línea Única: Ajuste exacto de ancho a {final_size:.1f}pt")
                
            else:
                # === ALGORITMO PÁRRAFOS (SHRINK-TO-FIT) ===
                rect.y1 += 30 # Le damos mucho espacio vertical para que respire y haga Word Wrap
                rect.x1 += 5
                
                current_size = float(block['font_size'])
                texto_insertado = False

                while current_size >= 6.0:
                    resultado = page.insert_textbox(
                        rect, new_text, fontsize=current_size, 
                        fontname=target_fontname, color=(0, 0, 0), align=0
                    )
                    
                    if resultado >= 0:
                        texto_insertado = True
                        logging.info(f"Párrafo: Ajustado con saltos de línea a {current_size:.1f}pt")
                        break
                    else:
                        current_size -= 0.5

                if not texto_insertado:
                    punto_seguro = fitz.Point(rect.x0, rect.y0 + 8)
                    page.insert_text(punto_seguro, new_text, fontsize=8, fontname=target_fontname, color=(0, 0, 0))

        self.doc.save(self.output_pdf, garbage=4, deflate=True)
        self.doc.close()
        logging.info(f"✅ Documento generado en: {self.output_pdf}")