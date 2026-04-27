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
        """
        1. Destruye el texto viejo (Redacción).
        2. Inyecta el texto nuevo.
        3. Guarda el documento.
        """
        logging.info("Iniciando fase de DESTRUCCIÓN y RECONSTRUCCIÓN...")

        for block in translated_blocks:
            page = self.doc[block['page_num'] - 1] # PyMuPDF usa índice 0
            bbox = block['bbox']
            new_text = block['translated_text']
            
            # --- FASE 1: DESTRUCCIÓN ABSOLUTA ---
            # add_redact_annot marca la zona. fill=(1,1,1) pinta de blanco el fondo 
            # para tapar escaneos (Escenario B y C).
            page.add_redact_annot(bbox, fill=(1, 1, 1))
            
            # apply_redactions() purga físicamente el texto y la imagen de esa coordenada
            page.apply_redactions()

            # --- FASE 2: INYECCIÓN DE TRADUCCIÓN ---
            # Insertamos el texto nuevo en la misma caja delimitadora.
            # Usamos un tamaño de fuente que se auto-ajuste (fontsize=-1) o uno aproximado
            try:
                page.insert_textbox(
                    fitz.Rect(bbox), 
                    new_text, 
                    fontsize=11, # En futuras iteraciones lo extraeremos del original
                    fontname="helv", 
                    color=(0, 0, 0),
                    align=0 # Alineación a la izquierda
                )
            except Exception as e:
                logging.error(f"Error inyectando texto en caja {bbox}: {e}")

        # Guardar el PDF resultante
        self.doc.save(self.output_pdf, garbage=4, deflate=True) # garbage=4 limpia recursos huérfanos
        self.doc.close()
        logging.info(f"✅ Documento final generado exitosamente en: {self.output_pdf}")