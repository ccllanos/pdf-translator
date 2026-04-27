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
        logging.info("Iniciando fase de DESTRUCCIÓN y RECONSTRUCCIÓN...")

        for block in translated_blocks:
            page = self.doc[block['page_num'] - 1]
            bbox = block['bbox']
            new_text = block['translated_text']
            
            # --- FASE 1: DESTRUCCIÓN ESTRUCTURAL ---
            page.add_redact_annot(bbox, fill=(1, 1, 1))
            page.apply_redactions()

            # --- FASE 2: INYECCIÓN DE TRADUCCIÓN ---
            # Transformamos las coordenadas a un objeto Rectángulo manipulable
            rect = fitz.Rect(bbox)
            
            # MARGEN DE SEGURIDAD: Expandimos la caja virtualmente hacia la derecha y abajo
            # para dar espacio a traducciones que naturalmente ocupan más ancho (ej. Inglés a Español)
            rect.x1 += 30  # Expandir ancho
            rect.y1 += 15  # Expandir alto
            
            try:
                # Al poner fontsize=-1, PyMuPDF calcula el tamaño máximo de fuente
                # que permite que el texto quepa en el rectángulo sin cortarse.
                resultado_insercion = page.insert_textbox(
                    rect, 
                    new_text, 
                    fontsize=-1, 
                    fontname="helv", 
                    color=(0, 0, 0),
                    align=0
                )
                
                # Si insert_textbox devuelve un número < 0, significa que falló por falta de espacio
                if resultado_insercion < 0:
                    logging.warning(f"La caja es demasiado restrictiva. Usando inyección libre para: '{new_text[:10]}...'")
                    
                    # FALLBACK: Inyectar el texto directamente en el punto de inicio X, Y 
                    # sin forzarlo a encajar en una caja cerrada. (El +10 es para alinear la línea base).
                    punto_inicio = fitz.Point(bbox[0], bbox[1] + 10)
                    page.insert_text(punto_inicio, new_text, fontsize=10, fontname="helv", color=(0, 0, 0))
                    
            except Exception as e:
                logging.error(f"Error inyectando texto en caja {bbox}: {e}")

        # Guardar el PDF resultante
        self.doc.save(self.output_pdf, garbage=4, deflate=True)
        self.doc.close()
        logging.info(f"✅ Documento final generado exitosamente en: {self.output_pdf}")