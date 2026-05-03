import sys
import os
import argparse
import colorama
from colorama import Fore, Style

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pdf_processing.pdf_analyzer import PDFAnalyzer
from translation.translation_service import TranslationService
from reconstruction.pdf_rebuilder import PDFRebuilder
from font_management.font_mapper_gui import FontMapperGUI

# Cambiado a PySide6
from PySide6.QtWidgets import QApplication

def main():
    colorama.init()
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--target', required=True)
    args = parser.parse_args()

    app = QApplication(sys.argv)

    print(Fore.CYAN + "="*65)
    print(Style.BRIGHT + " PDF TRANSLATOR V1.2 - CON GUI NATIVA PYSIDE6")
    print(Fore.CYAN + "="*65 + Style.RESET_ALL)
    
    print(f"\n{Fore.YELLOW}>>> FASE 1: ANÁLISIS DEL LAYOUT{Style.RESET_ALL}")
    analyzer = PDFAnalyzer(args.input)
    analyzer.analyze()
    
    print(f"\n{Fore.MAGENTA}>>> FASE INTERMEDIA: Esperando entrada del usuario en GUI...{Style.RESET_ALL}")
    
    gui = FontMapperGUI(analyzer.fonts)
    user_mapping = gui.get_mapping() 
    
    if not user_mapping:
        print(f"\n{Fore.RED}[ABORTADO] Traducción cancelada por el usuario.{Style.RESET_ALL}")
        sys.exit(0)

    print(f"{Fore.GREEN}[OK] Mapeo de fuentes confirmado. Procediendo con IA.{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}>>> FASE 2: TRADUCCIÓN SEMÁNTICA{Style.RESET_ALL}")
    translator = TranslationService()
    datos_para_reconstruir = []

    for idx, block in enumerate(analyzer.elements):
        print(f"Traduciendo Bloque {idx+1}...")
        resultado = translator.translate_block(block.text, args.source, args.target)
        datos_para_reconstruir.append({
            'page_num': block.page_num,
            'bbox': block.bbox,
            'translated_text': resultado,
            'font_name': block.primary_font,
            'font_size': block.font_size
        })

    print(f"\n{Fore.YELLOW}>>> FASE 3: RECONSTRUCCIÓN CON FUENTES MAPEADAS{Style.RESET_ALL}")
    rebuilder = PDFRebuilder(args.input, args.output, user_mapping)
    rebuilder.destroy_and_rebuild(datos_para_reconstruir)
    print("\n" + Fore.GREEN + Style.BRIGHT + f"[OK] Proceso Finalizado. Archivo: {args.output}" + Style.RESET_ALL)

if __name__ == "__main__":
    main()