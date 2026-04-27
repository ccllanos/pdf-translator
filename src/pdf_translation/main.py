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
    print(Style.BRIGHT + " PDF TRANSLATOR V1.2 - CONEXIÓN LLM LOCAL")
    print(Fore.CYAN + "="*65 + Style.RESET_ALL)
    
    print(f"\n{Fore.YELLOW}>>> FASE 1: ANÁLISIS DE PDF{Style.RESET_ALL}")
    analyzer = PDFAnalyzer(args.input)
    analyzer.analyze()
    
    print(f"\n{Fore.YELLOW}>>> FASE 2: MOTOR LLM Y VALIDACIÓN 1:1{Style.RESET_ALL}")
    translator = TranslationService()
    
    # Extraemos solo las primeras 3 palabras para no saturar el servidor en las pruebas
    palabras = [elem.text for elem in analyzer.elements if elem.text]
    # Si la caja tiene muchas palabras, las separamos y cogemos algunas
    palabras_sueltas = " ".join(palabras).split()[:3]
    
    for palabra in palabras_sueltas:
        if len(palabra) > 2: # Ignorar artículos cortos en la prueba
            print(f"\n{Fore.CYAN}--- PROCESANDO: '{palabra}' ---{Style.RESET_ALL}")
            resultado = translator.translate_with_constraints(palabra, args.source, args.target)
            print(f"Resultado final a inyectar en PDF: {Style.BRIGHT}{resultado}{Style.RESET_ALL}")

    print("\n" + Fore.GREEN + Style.BRIGHT + "[OK] Pipeline de Traducción Finalizado." + Style.RESET_ALL)

if __name__ == "__main__":
    main()