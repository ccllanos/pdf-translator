import sys
import os
import argparse
import colorama
from colorama import Fore, Style

# Añadir el directorio src al path para permitir importaciones absolutas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from validation_pipeline.translation_checker import enforce_translation

def main():
    colorama.init()
    
    parser = argparse.ArgumentParser(description="PDF Translator v1.2 - Character-Preserving Translation System")
    parser.add_argument('--input', required=True, help="Ruta del PDF original")
    parser.add_argument('--output', required=True, help="Ruta del PDF traducido")
    parser.add_argument('--source', required=True, help="Idioma origen")
    parser.add_argument('--target', required=True, help="Idioma destino")
    parser.add_argument('--generate-font-report', action='store_true', help="Generar informe de fuentes")
    
    args = parser.parse_args()

    print(Fore.CYAN + "="*60)
    print(Style.BRIGHT + " PDF TRANSLATOR V1.2 - INICIANDO PROCESAMIENTO")
    print(Fore.CYAN + "="*60 + Style.RESET_ALL)
    print(f"[{Fore.GREEN}INFO{Style.RESET_ALL}] Archivo origen: {args.input}")
    print(f"[{Fore.GREEN}INFO{Style.RESET_ALL}] Archivo destino: {args.output}")
    print(f"[{Fore.GREEN}INFO{Style.RESET_ALL}] Traducción: {args.source} -> {args.target}")
    
    if args.generate_font_report:
        print(f"[{Fore.YELLOW}INFO{Style.RESET_ALL}] El informe de tipografías será generado.")

    print("\n" + Fore.CYAN + "--- INICIANDO PIPELINE DE VALIDACIÓN DE CARACTERES (1:1) ---" + Style.RESET_ALL)
    
    # Pruebas de concepto para demostrar el funcionamiento del pipeline crítico
    test_cases = [
        ("consecuencia", "consequence"),   # 12 -> 12 (Correcto)
        ("consecuencia", "consequences"),  # 12 -> 13 (Incorrecto)
        ("ley", "law"),                    # 3 -> 3 (Correcto)
        ("contrato", "contract"),          # 8 -> 8 (Correcto)
        ("contrato", "agreement"),         # 8 -> 9 (Incorrecto)
    ]

    for original, translated in test_cases:
        enforce_translation(original, translated)

    print("\n" + Fore.GREEN + "[OK] Simulación de procesamiento base finalizada." + Style.RESET_ALL)

if __name__ == "__main__":
    main()