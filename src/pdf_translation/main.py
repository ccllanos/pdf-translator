import sys
import os
import argparse
import colorama
from colorama import Fore, Style
import fitz

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pdf_processing.pdf_analyzer import PDFAnalyzer
from font_matching.matcher_service import FontMatcherService
from translation.translation_service import TranslationService
from reconstruction.pdf_rebuilder import PDFRebuilder
from font_management.session_manager_gui import SessionSettingsGUI
from utils.cache_manager import ProjectCacheManager
from PySide6.QtWidgets import QApplication

def main():
    colorama.init()
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--target', required=True)
    args = parser.parse_args()

    # Inicializar el gestor de caché persistente
    cache = ProjectCacheManager(args.input)

    app = QApplication(sys.argv)
    doc_temp = fitz.open(args.input)
    total_pages = len(doc_temp)
    doc_temp.close()

    print(Fore.CYAN + "="*65)
    print(Style.BRIGHT + " PDF TRANSLATOR V1.2 - PROYECTO Y PROCESAMIENTO PARCIAL")
    print(Fore.CYAN + "="*65 + Style.RESET_ALL)
    
    # 1. Análisis tipográfico
    analyzer = PDFAnalyzer(args.input)
    analyzer.analyze()
    
    matcher = FontMatcherService()
    font_cloud_report = matcher.analyze_fonts(analyzer.fonts)
    
    # 2. Interfaz Avanzada de Sesión
    print(f"\n{Fore.MAGENTA}>>> Abriendo Configuración de Sesión...{Style.RESET_ALL}")
    gui = SessionSettingsGUI(
        analyzer.fonts, 
        font_cloud_report, 
        total_pages, 
        cache.get_font_mapping()
    )
    
    config = gui.get_results()
    if not config:
        print(f"\n{Fore.RED}[ABORTADO] Sesión cancelada por el usuario.{Style.RESET_ALL}")
        sys.exit(0)

    # Actualizar las fuentes mapeadas en caché
    cache.update_font_mapping(config["font_mappings"])

    # 3. Reconstructor de PDF
    rebuilder = PDFRebuilder(args.input, args.output, config["font_mappings"])
    translator = TranslationService()

    print(f"\n{Fore.YELLOW}>>> FASE 2: PROCESANDO SESIÓN DE TRADUCCIÓN{Style.RESET_ALL}")
    
    # Iteramos sobre todas las páginas del documento
    for page_num in range(1, total_pages + 1):
        
        # CASO A: La página fue seleccionada para traducirse en esta sesión
        if page_num in config["selected_pages"]:
            print(f"\n{Fore.CYAN}Trabajando en Página {page_num}/{total_pages}...{Style.RESET_ALL}")
            
            # Obtener el modo configurado por el usuario en esta sesión
            mode_config = config["page_modes"].get(page_num, {"mode": "standard", "bg_path": None})
            
            # Filtrar bloques que pertenecen a esta página
            page_blocks = [b for b in analyzer.elements if b.page_num == page_num]
            translated_blocks = []

            for idx, block in enumerate(page_blocks):
                print(f" -> Traduciendo bloque {idx+1}/{len(page_blocks)}...")
                resultado = translator.translate_block(block.text, args.source, args.target)
                translated_blocks.append({
                    'bbox': block.bbox,
                    'translated_text': resultado,
                    'font_name': block.primary_font,
                    'font_size': block.font_size
                })

            # Guardar la página traducida en la caché persistente
            cache.save_page_translation(page_num, mode_config["mode"], mode_config["bg_path"], translated_blocks)
            
            # Inyectar en el PDF en tiempo real
            rebuilder.apply_page_rendering(page_num, mode_config["mode"], mode_config["bg_path"], translated_blocks)

        # CASO B: La página ya fue traducida en sesiones pasadas (Caché persistente)
        elif cache.is_page_translated(page_num):
            print(f"\n{Fore.GREEN}[REUTILIZANDO CACHÉ] Cargando traducción previa para Página {page_num}.{Style.RESET_ALL}")
            saved_page = cache.get_page_cache(page_num)
            rebuilder.apply_page_rendering(page_num, saved_page["mode"], saved_page["bg_path"], saved_page["blocks"])

        # CASO C: La página no ha sido traducida aún. Se mantiene el original (Untouched)
        else:
            print(f"\n{Fore.WHITE}Página {page_num} se mantiene intacta en su estado original.{Style.RESET_ALL}")

    # 4. Guardar los resultados en el PDF final
    rebuilder.save()
    
    print(Fore.GREEN + "="*65)
    print(f" PROCESO COMPLETADO")
    print(f" Páginas traducidas en total: {cache.get_translated_pages_count()} de {total_pages}")
    print(f" Archivo guardado: {args.output}")
    print("="*65 + Style.RESET_ALL)

if __name__ == "__main__":
    main()