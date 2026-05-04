import os
import json
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class ProjectCacheManager:
    """Gestiona el estado persistente, modos de página y traducciones del proyecto."""
    def __init__(self, pdf_path: str):
        self.pdf_path = os.path.abspath(pdf_path)
        # El archivo de caché vivirá al lado del PDF con la extensión .cache.json
        self.cache_path = self.pdf_path + ".cache.json"
        self.data: Dict[str, Any] = self._load_or_create()

    def _load_or_create(self) -> Dict[str, Any]:
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    logging.info(f"Caché cargada exitosamente desde: {self.cache_path}")
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error leyendo archivo de caché corrupto: {e}. Creando uno nuevo.")
        
        return {
            "pdf_path": self.pdf_path,
            "font_mappings": {},
            "pages": {} # Almacenará: "1": {"mode": "editorial", "bg_path": "...", "blocks": [...]}
        }

    def save(self):
        """Guarda el estado actual del proyecto en el archivo JSON."""
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error guardando la caché: {e}")

    def update_font_mapping(self, font_mappings: Dict[str, Any]):
        self.data["font_mappings"] = font_mappings
        self.save()

    def get_font_mapping(self) -> Dict[str, Any]:
        return self.data.get("font_mappings", {})

    def save_page_translation(self, page_num: int, mode: str, bg_path: Optional[str], blocks: list):
        """Guarda el modo de procesamiento, fondo limpio y bloques traducidos de una página."""
        self.data["pages"][str(page_num)] = {
            "mode": mode,
            "bg_path": bg_path,
            "blocks": blocks
        }
        self.save()

    def get_page_cache(self, page_num: int) -> Optional[Dict[str, Any]]:
        """Retorna la traducción guardada de una página si existe."""
        return self.data["pages"].get(str(page_num))

    def is_page_translated(self, page_num: int) -> bool:
        return str(page_num) in self.data["pages"]

    def get_translated_pages_count(self) -> int:
        return len(self.data["pages"])