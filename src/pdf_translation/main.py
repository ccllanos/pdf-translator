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

from PySide6.QtWidgets import QApplication, QFileDialog

def main():
    colorama.init()
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=False)
    parser.add_argument('--output', required=False)
    parser.add_argument('--source', default="English")
    parser.add_argument('--target', default="Spanish")
    args = parser.parse_args()

    app = QApplication(sys.argv)

    print(Fore.CYAN + "="*65)
    print(Style.BRIGHT + " PDF TRANSLATOR V1.2 - GESTIÓN DE PROYECTOS")
    print(Fore.CYAN + "="*65 + Style.RESET_ALL)

    pdf_path = args.input
    if not pdf_path:
        file_path, _ = QFileDialog.getOpenFileName(None, "Seleccionar documento PDF a traducir", "", "Documentos PDF (*.pdf)")
        if not file_path:
            sys.exit(0)
        pdf_path = file_path

    # Inicializar el Proyecto
    cache = ProjectCacheManager(pdf_path)
    
    # El archivo de salida ahora se guarda automáticamente en la carpeta /projects/.../salida/
    output_path = args.output
    if not output_path:
        base_name = os.path.basename(pdf_path)
        output_path = os.path.join(cache.out_dir, f"{os.path.splitext(base_name)[0]}_translated.pdf")

    print(f"\n{Fore.GREEN}[CARPETA DEL PROYECTO]: {cache.project_dir}{Style.RESET_ALL}")

    doc_temp = fitz.open(pdf_path)
    total_pages = len(doc_temp)
    doc_temp.close()
    
    print(f"\n{Fore.YELLOW}>>> FASE 1: ANÁLISIS DEL LAYOUT{Style.RESET_ALL}")
    analyzer = PDFAnalyzer(pdf_path)
    analyzer.analyze()
    
    matcher = FontMatcherService()
    font_cloud_report = matcher.analyze_fonts(analyzer.fonts)
    
    # Pasamos las configuraciones previas (fuentes y modos de página)
    gui = SessionSettingsGUI(
        analyzer.fonts, 
        font_cloud_report, 
        total_pages, 
        cache.get_font_mapping(),
        cache.get_all_page_modes()  # NUEVO: Precarga los fondos anteriores
    )
    
    config = gui.get_results()
    if not config:
        print(f"\n{Fore.RED}[ABORTADO] Sesión cancelada.{Style.RESET_ALL}")
        sys.exit(0)

    cache.update_font_mapping(config["font_mappings"])

    rebuilder = PDFRebuilder(pdf_path, output_path, config["font_mappings"])
    translator = TranslationService()

    print(f"\n{Fore.YELLOW}>>> FASE 2: PROCESANDO SESIÓN{Style.RESET_ALL}")
    
    for page_num in range(1, total_pages + 1):
        if page_num in config["selected_pages"]:
            print(f"\n{Fore.CYAN}Trabajando en Página {page_num}/{total_pages}...{Style.RESET_ALL}")
            
            mode_config = config["page_modes"].get(page_num, {"mode": "standard", "bg_path": None})
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

            cache.save_page_translation(page_num, mode_config["mode"], mode_config["bg_path"], translated_blocks)
            rebuilder.apply_page_rendering(page_num, mode_config["mode"], mode_config["bg_path"], translated_blocks)

        elif cache.is_page_translated(page_num):
            print(f"\n{Fore.GREEN}[REUTILIZANDO CACHÉ] Página {page_num}.{Style.RESET_ALL}")
            saved_page = cache.get_page_cache(page_num)
            rebuilder.apply_page_rendering(page_num, saved_page["mode"], saved_page["bg_path"], saved_page["blocks"])

    rebuilder.save()
    
    print(Fore.GREEN + "="*65)
    print(f" PROCESO COMPLETADO")
    print(f" Archivo guardado en: {output_path}")
    print("="*65 + Style.RESET_ALL)

if __name__ == "__main__":
    main()