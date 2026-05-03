import sys
import os
import argparse
import colorama
from colorama import Fore, Style

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pdf_processing.pdf_analyzer import PDFAnalyzer
from font_matching.matcher_service import FontMatcherService
from translation.translation_service import TranslationService
from reconstruction.pdf_rebuilder import PDFRebuilder
from font_management.font_mapper_gui import FontMapperGUI
from PySide6.QtWidgets import QApplication

def main():
    colorama.init()
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--target', required=True)
    # NUEVO: Argumento opcional para carpeta de fondos
    parser.add_argument('--bg-folder', required=False, help="Carpeta con imágenes de fondo limpio (ej. page_1.png)")
    
    args = parser.parse_args()

    app = QApplication(sys.argv)

    print(Fore.CYAN + "="*65)
    print(Style.BRIGHT + " PDF TRANSLATOR V1.2 - MODO EDITORIAL")
    print(Fore.CYAN + "="*65 + Style.RESET_ALL)
    
    if args.bg_folder:
        print(f"{Fore.GREEN}[INFO] Modo Editorial Activado. Se usarán fondos de: {args.bg_folder}{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}>>> FASE 1: ANÁLISIS DEL LAYOUT{Style.RESET_ALL}")
    analyzer = PDFAnalyzer(args.input)
    analyzer.analyze()
    
    matcher = FontMatcherService()
    font_cloud_report = matcher.analyze_fonts(analyzer.fonts)
    
    print(f"\n{Fore.MAGENTA}>>> FASE INTERMEDIA: Abriendo Inspector...{Style.RESET_ALL}")
    gui = FontMapperGUI(font_cloud_report)
    user_mapping = gui.get_mapping() 
    
    if not user_mapping:
        sys.exit(0)
    
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

    print(f"\n{Fore.YELLOW}>>> FASE 3: RECONSTRUCCIÓN{Style.RESET_ALL}")
    # Pasamos la carpeta de fondos al reconstructor
    rebuilder = PDFRebuilder(args.input, args.output, user_mapping, args.bg_folder)
    rebuilder.destroy_and_rebuild(datos_para_reconstruir)
    print("\n" + Fore.GREEN + Style.BRIGHT + f"[OK] Proceso Finalizado. Archivo: {args.output}" + Style.RESET_ALL)

if __name__ == "__main__":
    main()