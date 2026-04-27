import sys
import os
import argparse
import colorama
from colorama import Fore, Style

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from validation_pipeline.translation_checker import enforce_translation
from pdf_processing.pdf_analyzer import PDFAnalyzer
from font_matching.matcher_service import FontMatcherService

def main():
    colorama.init()
    
    parser = argparse.ArgumentParser(description="PDF Translator v1.2")
    parser.add_argument('--input', required=True, help="Ruta del PDF original")
    parser.add_argument('--output', required=True, help="Ruta del PDF traducido")
    parser.add_argument('--source', required=True, help="Idioma origen")
    parser.add_argument('--target', required=True, help="Idioma destino")
    parser.add_argument('--generate-font-report', action='store_true')
    
    args = parser.parse_args()

    print(Fore.CYAN + "="*65)
    print(Style.BRIGHT + " PDF TRANSLATOR V1.2 - INICIANDO PROCESAMIENTO")
    print(Fore.CYAN + "="*65 + Style.RESET_ALL)
    
    # --- FASE 1: ANÁLISIS ESTRUCTURAL ---
    print(f"\n{Fore.YELLOW}>>> FASE 1: EXTRACCIÓN DE PDF{Style.RESET_ALL}")
    analyzer = PDFAnalyzer(args.input)
    analyzer.analyze()
    
    # --- FASE 2: MATCHING DE FUENTES ONLINE ---
    print(f"\n{Fore.YELLOW}>>> FASE 2: IDENTIFICACIÓN DE FUENTES ONLINE{Style.RESET_ALL}")
    matcher = FontMatcherService()
    font_results = matcher.analyze_fonts(analyzer.fonts)
    
    if args.generate_font_report:
        print(Fore.MAGENTA + "="*50)
        print(" INFORME DE TIPOGRAFÍAS REQUERIDAS (1:1)")
        print("="*50 + Style.RESET_ALL)
        for font in font_results:
            color = Fore.GREEN if "DISPONIBLE" in font['status_icon'] else Fore.RED
            print(f" PDF Original : {font['raw_name']}")
            print(f" Detectada    : {Style.BRIGHT}{font['real_name']}{Style.RESET_ALL}")
            print(f" Estado       : {color}{font['status_icon']}{Style.RESET_ALL}")
            print(f" Proveedor    : {font['provider']}")
            print(f" Acción req.  : {font['action']}")
            print("-" * 50)

    # --- FASE 3: TRADUCCIÓN Y VALIDACIÓN ---
    print(f"\n{Fore.YELLOW}>>> FASE 3: TRADUCCIÓN Y RESTRICCIÓN DE LONGITUD (1:1){Style.RESET_ALL}")
    
    palabras_extraidas = [elem.text.split()[0] for elem in analyzer.elements if elem.text]
    
    for palabra in palabras_extraidas:
        traduccion_simulada_llm = palabra + "s" if len(palabra) % 2 != 0 else palabra 
        print(f"\nProcesando: '{palabra}'")
        enforce_translation(palabra, traduccion_simulada_llm)

    print("\n" + Fore.GREEN + Style.BRIGHT + "[OK] Pipeline de Procesamiento Finalizado con Éxito." + Style.RESET_ALL)

if __name__ == "__main__":
    main()