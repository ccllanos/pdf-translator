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
    # Quitamos el 'required=True' del input y output para pedirlos gráficamente
    parser.add_argument('--input', required=False, help="Ruta del PDF original")
    parser.add_argument('--output', required=False, help="Ruta de guardado")
    parser.add_argument('--source', default="English", help="Idioma origen")
    parser.add_argument('--target', default="Spanish", help="Idioma destino")
    args = parser.parse_args()

    # Inicializamos la App gráfica primero
    app = QApplication(sys.argv)

    print(Fore.CYAN + "="*65)
    print(Style.BRIGHT + " PDF TRANSLATOR V1.2 - SISTEMA PROFESIONAL")
    print(Fore.CYAN + "="*65 + Style.RESET_ALL)

    # --- SELECCIÓN GRÁFICA DEL PDF ---
    pdf_path = args.input
    if not pdf_path:
        print(f"{Fore.MAGENTA}Esperando selección de archivo PDF...{Style.RESET_ALL}")
        # Abrimos el explorador nativo de Windows
        file_path, _ = QFileDialog.getOpenFileName(
            None, 
            "Seleccionar documento PDF a traducir", 
            "", 
            "Documentos PDF (*.pdf)"
        )
        
        if not file_path:
            print(f"{Fore.RED}[ABORTADO] No se seleccionó ningún archivo.{Style.RESET_ALL}")
            sys.exit(0)
            
        pdf_path = file_path

    # Generamos la ruta de salida automáticamente si no se especificó
    output_path = args.output
    if not output_path:
        base_name, ext = os.path.splitext(pdf_path)
        output_path = f"{base_name}_translated{ext}"

    print(f"\n{Fore.GREEN}[DOCUMENTO ACTIVO]: {pdf_path}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[RUTA DE SALIDA]: {output_path}{Style.RESET_ALL}")

    # Inicializar el gestor de caché persistente en la carpeta del PDF
    cache = ProjectCacheManager(pdf_path)

    doc_temp = fitz.open(pdf_path)
    total_pages = len(doc_temp)
    doc_temp.close()
    
    print(f"\n{Fore.YELLOW}>>> FASE 1: ANÁLISIS DEL LAYOUT{Style.RESET_ALL}")
    analyzer = PDFAnalyzer(pdf_path)
    analyzer.analyze()
    
    matcher = FontMatcherService()
    font_cloud_report = matcher.analyze_fonts(analyzer.fonts)
    
    print(f"\n{Fore.MAGENTA}>>> FASE INTERMEDIA: Abriendo Configuración de Sesión...{Style.RESET_ALL}")
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

    # Reconstructor de PDF
    rebuilder = PDFRebuilder(pdf_path, output_path, config["font_mappings"])
    translator = TranslationService()

    print(f"\n{Fore.YELLOW}>>> FASE 2: PROCESANDO SESIÓN DE TRADUCCIÓN{Style.RESET_ALL}")
    
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
            print(f"\n{Fore.GREEN}[REUTILIZANDO CACHÉ] Cargando traducción previa para Página {page_num}.{Style.RESET_ALL}")
            saved_page = cache.get_page_cache(page_num)
            rebuilder.apply_page_rendering(page_num, saved_page["mode"], saved_page["bg_path"], saved_page["blocks"])
        else:
            print(f"\n{Fore.WHITE}Página {page_num} se mantiene intacta en su estado original.{Style.RESET_ALL}")

    rebuilder.save()
    
    print(Fore.GREEN + "="*65)
    print(f" PROCESO COMPLETADO")
    print(f" Páginas traducidas en total: {cache.get_translated_pages_count()} de {total_pages}")
    print(f" Archivo guardado: {output_path}")
    print("="*65 + Style.RESET_ALL)

if __name__ == "__main__":
    main()