import sys
import os
import argparse
import colorama
from colorama import Fore, Style

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pdf_processing.pdf_analyzer import PDFAnalyzer
from font_matching.matcher_service import FontMatcherService
from translation.translation_service import TranslationService

def main():
    colorama.init()
    
    parser = argparse.ArgumentParser(description="PDF Translator v1.2")
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--generate-font-report', action='store_true')
    
    args = parser.parse_args()

    print(Fore.CYAN + "="*65)
    print(Style.BRIGHT + " PDF TRANSLATOR V1.2 - TRADUCCIÓN SEMÁNTICA POR BLOQUES")
    print(Fore.CYAN + "="*65 + Style.RESET_ALL)
    
    print(f"\n{Fore.YELLOW}>>> FASE 1: ANÁLISIS DEL LAYOUT (PÁRRAFOS Y CAJAS){Style.RESET_ALL}")
    analyzer = PDFAnalyzer(args.input)
    analyzer.analyze()
    
    print(f"\n{Fore.YELLOW}>>> FASE 2: TRADUCCIÓN SEMÁNTICA (SPATIAL 1:1){Style.RESET_ALL}")
    translator = TranslationService()
    
    # Procesamos los bloques lógicos detectados en lugar de palabras sueltas
    for idx, block in enumerate(analyzer.elements):
        print(f"\n{Fore.CYAN}--- PROCESANDO BLOQUE {idx+1} (Página {block.page_num}) ---{Style.RESET_ALL}")
        print(f"Texto Original: {Style.DIM}{block.text}{Style.RESET_ALL}")
        print(f"Fuente Primaria: {block.primary_font} | Bounding Box: {block.bbox}")
        
        resultado = translator.translate_block(block.text, args.source, args.target)
        
        print(f"{Fore.GREEN}Texto Traducido:{Style.RESET_ALL} {Style.BRIGHT}{resultado}{Style.RESET_ALL}")

    print("\n" + Fore.GREEN + Style.BRIGHT + "[OK] Pipeline de Traducción por Bloques Finalizado." + Style.RESET_ALL)

if __name__ == "__main__":
    main()