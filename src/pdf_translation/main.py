import sys
import os
import colorama
from colorama import Fore, Style
import fitz

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pdf_processing.pdf_analyzer import PDFAnalyzer
from font_matching.matcher_service import FontMatcherService
from translation.translation_service import TranslationService
from reconstruction.pdf_rebuilder import PDFRebuilder
from font_management.session_manager_gui import SessionSettingsGUI, LauncherGUI
from utils.cache_manager import ProjectCacheManager
from PySide6.QtWidgets import QApplication

def main():
    colorama.init()
    app = QApplication(sys.argv)

    print(Fore.CYAN + "="*65)
    print(Style.BRIGHT + " PDF TRANSLATOR V1.2 - GESTOR DE PROYECTOS")
    print(Fore.CYAN + "="*65 + Style.RESET_ALL)

    # 1. PANTALLA DE INICIO (LAUNCHER)
    launcher = LauncherGUI()
    action, project_path, source_pdf = launcher.get_result()

    if not action:
        sys.exit(0)

    # 2. INICIALIZAR CACHÉ DEL PROYECTO
    cache = ProjectCacheManager(project_path, source_pdf)
    internal_pdf = cache.internal_pdf_path
    output_pdf = os.path.join(cache.out_dir, f"{os.path.basename(project_path)}_translated.pdf")

    print(f"\n{Fore.GREEN}[PROYECTO]: {project_path}{Style.RESET_ALL}")

    doc_temp = fitz.open(internal_pdf)
    total_pages = len(doc_temp)
    doc_temp.close()
    
    print(f"\n{Fore.YELLOW}>>> FASE 1: ANÁLISIS DEL LAYOUT{Style.RESET_ALL}")
    analyzer = PDFAnalyzer(internal_pdf)
    analyzer.analyze()
    
    matcher = FontMatcherService()
    font_cloud_report = matcher.analyze_fonts(analyzer.fonts)
    
    print(f"\n{Fore.MAGENTA}>>> FASE INTERMEDIA: Abriendo Configuración de Sesión...{Style.RESET_ALL}")
    gui = SessionSettingsGUI(
        analyzer.fonts, 
        font_cloud_report, 
        total_pages, 
        cache.get_font_mapping(),
        cache.get_all_page_modes()
    )
    
    config = gui.get_results()
    if not config: sys.exit(0)

    cache.update_font_mapping(config["font_mappings"])

    rebuilder = PDFRebuilder(internal_pdf, output_pdf, config["font_mappings"])
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
                # Aquí forzamos de Inglés a Español internamente, en el futuro se podrá pedir en el launcher
                resultado = translator.translate_block(block.text, "English", "Spanish")
                translated_blocks.append({
                    'bbox': block.bbox,
                    'translated_text': resultado,
                    'font_name': block.primary_font,
                    'font_size': block.font_size
                })

            # Guardar bloques (esto también copia el fondo .png a la carpeta interna /fondos)
            cache.save_page_translation(page_num, mode_config["mode"], mode_config["bg_path"], translated_blocks)
            
            # Leemos la ruta interna que el caché acaba de generar
            internal_bg_path = cache.get_page_cache(page_num)["bg_path"]
            rebuilder.apply_page_rendering(page_num, mode_config["mode"], internal_bg_path, translated_blocks)

        elif cache.is_page_translated(page_num):
            print(f"\n{Fore.GREEN}[REUTILIZANDO CACHÉ] Página {page_num}.{Style.RESET_ALL}")
            saved_page = cache.get_page_cache(page_num)
            rebuilder.apply_page_rendering(page_num, saved_page["mode"], saved_page["bg_path"], saved_page["blocks"])

    rebuilder.save()
    
    print(Fore.GREEN + "="*65)
    print(f" PROCESO COMPLETADO")
    print(f" Archivo final generado en: {output_path}")
    print("="*65 + Style.RESET_ALL)

if __name__ == "__main__":
    main()