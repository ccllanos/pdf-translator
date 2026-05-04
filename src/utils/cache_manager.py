import os
import json
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class ProjectCacheManager:
    """Gestiona el ecosistema de carpetas y el estado del proyecto."""
    def __init__(self, pdf_path: str):
        self.original_pdf_path = os.path.abspath(pdf_path)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        # Estructura del Proyecto en la raíz del software
        self.project_dir = os.path.join(os.getcwd(), "projects", base_name)
        self.bg_dir = os.path.join(self.project_dir, "fondos")
        self.out_dir = os.path.join(self.project_dir, "salida")
        
        # Crear directorios si no existen
        os.makedirs(self.bg_dir, exist_ok=True)
        os.makedirs(self.out_dir, exist_ok=True)
        
        self.cache_path = os.path.join(self.project_dir, "estado_sesion.json")
        self.data: Dict[str, Any] = self._load_or_create()

    def _load_or_create(self) -> Dict[str, Any]:
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    logging.info(f"Cargando sesión desde: {self.cache_path}")
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error leyendo caché: {e}. Creando una nueva.")
        
        return {
            "pdf_path": self.original_pdf_path,
            "font_mappings": {},
            "pages": {} 
        }

    def save(self):
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error guardando la sesión: {e}")

    def update_font_mapping(self, font_mappings: Dict[str, Any]):
        self.data["font_mappings"] = font_mappings
        self.save()

    def get_font_mapping(self) -> Dict[str, Any]:
        return self.data.get("font_mappings", {})

    def save_page_translation(self, page_num: int, mode: str, bg_path: Optional[str], blocks: list):
        self.data["pages"][str(page_num)] = {
            "mode": mode,
            "bg_path": bg_path,
            "blocks": blocks
        }
        self.save()

    def get_page_cache(self, page_num: int) -> Optional[Dict[str, Any]]:
        return self.data["pages"].get(str(page_num))

    def get_all_page_modes(self) -> Dict[int, Dict]:
        """Retorna la configuración de todas las páginas para precargarlas en la GUI."""
        return {int(k): {"mode": v["mode"], "bg_path": v["bg_path"]} for k, v in self.data["pages"].items()}

    def is_page_translated(self, page_num: int) -> bool:
        return str(page_num) in self.data["pages"]

    def get_translated_pages_count(self) -> int:
        return len(self.data["pages"])