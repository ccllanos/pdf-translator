import sys
import os
import argparse
import colorama
from colorama import Fore, Style

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from validation_pipeline.translation_checker import enforce_translation
from pdf_processing.pdf_analyzer import PDFAnalyzer

def main():
    colorama.init()
    
    parser = argparse.ArgumentParser(description="PDF Translator v1.2")
    parser.add_argument('--input', required=True, help="Ruta del PDF original")
    parser.add_argument('--output', required=True, help="Ruta del PDF traducido")
    parser.add_argument('--source', required=True, help="Idioma origen")
    parser.add_argument('--target', required=True, help="Idioma destino")
    parser.add_argument('--generate-font-report', action='store_true')
    
    args = parser.parse_args()

    print(Fore.CYAN + "="*60)
    print(Style.BRIGHT + " PDF TRANSLATOR V1.2 - INICIANDO PROCESAMIENTO")
    print(Fore.CYAN + "="*60 + Style.RESET_ALL)
    
    # 1. Fase de Análisis y Extracción
    print(f"\n{Fore.YELLOW}>>> FASE 1: ANÁLISIS ESTRUCTURAL Y TIPOGRÁFICO{Style.RESET_ALL}")
    analyzer = PDFAnalyzer(args.input)
    analyzer.analyze()
    
    if args.generate_font_report:
        print("\n" + Fore.MAGENTA + analyzer.get_font_report() + Style.RESET_ALL)

    # 2. Fase de Traducción (con validación 1:1)
    print(f"\n{Fore.YELLOW}>>> FASE 2: TRADUCCIÓN Y RESTRICCIÓN DE LONGITUD (1:1){Style.RESET_ALL}")
    
    # Extraemos solo las primeras palabras detectadas para la demostración
    palabras_extraidas = [elem.text.split()[0] for elem in analyzer.elements if elem.text]
    
    for palabra in palabras_extraidas:
        # Simulamos una traducción cruda desde un LLM
        traduccion_simulada_llm = palabra + "x" if len(palabra) % 2 == 0 else palabra 
        
        print(f"\nProcesando Caja de Texto original: '{palabra}'")
        enforce_translation(palabra, traduccion_simulada_llm)

    print("\n" + Fore.GREEN + "[OK] Análisis y validación finalizados con éxito." + Style.RESET_ALL)

if __name__ == "__main__":
    main()