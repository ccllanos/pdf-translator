import sys
import os
import argparse
import colorama
from colorama import Fore, Style

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pdf_processing.pdf_analyzer import PDFAnalyzer
from translation.translation_service import TranslationService
from reconstruction.pdf_rebuilder import PDFRebuilder

def main():
    colorama.init()
    
    parser = argparse.ArgumentParser(description="PDF Translator v1.2")
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--target', required=True)
    
    args = parser.parse_args()

    print(Fore.CYAN + "="*65)
    print(Style.BRIGHT + " PDF TRANSLATOR V1.2 - PIPELINE COMPLETO")
    print(Fore.CYAN + "="*65 + Style.RESET_ALL)
    
    print(f"\n{Fore.YELLOW}>>> FASE 1: ANÁLISIS DEL LAYOUT{Style.RESET_ALL}")
    analyzer = PDFAnalyzer(args.input)
    analyzer.analyze()
    
    print(f"\n{Fore.YELLOW}>>> FASE 2: TRADUCCIÓN SEMÁNTICA (SPATIAL 1:1){Style.RESET_ALL}")
    translator = TranslationService()
    
    # Lista para almacenar los datos listos para inyectar
    datos_para_reconstruir = []

    for idx, block in enumerate(analyzer.elements):
        print(f"\n{Fore.CYAN}Procesando Bloque {idx+1}...{Style.RESET_ALL}")
        
        # 1. Traducir
        resultado = translator.translate_block(block.text, args.source, args.target)
        
        # 2. Guardar estructura
        datos_para_reconstruir.append({
            'page_num': block.page_num,
            'bbox': block.bbox,
            'translated_text': resultado
        })
        
        print(f"{Fore.GREEN}Traducido:{Style.RESET_ALL} {resultado}")

    print(f"\n{Fore.YELLOW}>>> FASE 3: DESTRUCCIÓN Y RECONSTRUCCIÓN FÍSICA{Style.RESET_ALL}")
    
    rebuilder = PDFRebuilder(args.input, args.output)
    rebuilder.destroy_and_rebuild(datos_para_reconstruir)

    print("\n" + Fore.GREEN + Style.BRIGHT + f"[OK] Proceso Finalizado. Archivo generado: {args.output}" + Style.RESET_ALL)

if __name__ == "__main__":
    main()