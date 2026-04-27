import fitz
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class PDFRebuilder:
    """Se encarga de destruir el texto original y generar el nuevo PDF traducido."""
    
    def __init__(self, input_pdf: str, output_pdf: str):
        self.input_pdf = input_pdf
        self.output_pdf = output_pdf
        self.doc = fitz.open(self.input_pdf)

    def destroy_and_rebuild(self, translated_blocks: List[Dict]):
        logging.info("Iniciando fase de DESTRUCCIÓN y RECONSTRUCCIÓN FÍSICA...")

        for block in translated_blocks:
            page = self.doc[block['page_num'] - 1]
            bbox = block['bbox']
            new_text = block['translated_text']
            
            if not new_text or new_text.isspace():
                continue

            logging.info(f"Caja detectada en coords: {bbox} | Inyectando: '{new_text}'")

            # --- FASE 1: DESTRUCCIÓN ESTRUCTURAL ABSOLUTA ---
            # El fill (1,1,1) pinta de blanco el fondo para eliminar restos visuales
            page.add_redact_annot(bbox, fill=(1, 1, 1))
            page.apply_redactions()

            # --- FASE 2: INYECCIÓN INFALIBLE (PUNTO BASE) ---
            # bbox es (x_izq, y_arriba, x_der, y_abajo)
            # Para insertar texto libremente, PyMuPDF usa la esquina inferior izquierda 
            # como la "línea base" sobre la cual descansan las letras.
            # Tomamos la X izquierda, y la Y inferior, y le restamos 2 puntitos para afinar.
            punto_base = fitz.Point(bbox[0], bbox[3] - 2)
            
            try:
                # Escribimos el texto libremente sin forzarlo a encerrarse en una caja
                page.insert_text(
                    punto_base, 
                    new_text, 
                    fontsize=12, 
                    fontname="helv", 
                    color=(0, 0, 0)
                )
                
                # --- GUÍA VISUAL PARA DEBUGGING (Opcional) ---
                # Dibujamos un marco azul semitransparente para ver dónde está actuando el sistema
                marco = fitz.Rect(bbox)
                page.draw_rect(marco, color=(0, 0, 1), width=0.5)

            except Exception as e:
                logging.error(f"Error inyectando texto en {bbox}: {e}")

        # Guardar el PDF resultante
        self.doc.save(self.output_pdf, garbage=4, deflate=True)
        self.doc.close()
        logging.info(f"✅ Documento final generado exitosamente en: {self.output_pdf}")