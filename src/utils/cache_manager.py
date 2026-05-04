import os
import json
import logging
import shutil
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class ProjectCacheManager:
    def __init__(self, project_dir: str, source_pdf_path: str = None):
        """
        Si source_pdf_path existe, estamos creando un proyecto nuevo.
        Si solo damos project_dir, estamos cargando un proyecto existente.
        """
        self.project_dir = os.path.abspath(project_dir)
        self.bg_dir = os.path.join(self.project_dir, "fondos")
        self.out_dir = os.path.join(self.project_dir, "salida")
        self.cache_path = os.path.join(self.project_dir, "estado_sesion.json")
        
        os.makedirs(self.bg_dir, exist_ok=True)
        os.makedirs(self.out_dir, exist_ok=True)
        
        # Archivo PDF interno (Inmutable)
        self.internal_pdf_path = os.path.join(self.project_dir, "source_document.pdf")

        if source_pdf_path and not os.path.exists(self.internal_pdf_path):
            # Proyecto Nuevo: Copiamos el PDF adentro para aislarlo
            logging.info("Copiando PDF al ecosistema del proyecto...")
            shutil.copy2(source_pdf_path, self.internal_pdf_path)

        self.data: Dict[str, Any] = self._load_or_create()

    def _load_or_create(self) -> Dict[str, Any]:
        if os.path.exists(self.cache_path):
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"font_mappings": {}, "pages": {}}

    def save(self):
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def import_background(self, page_num: int, ext_path: str) -> str:
        """Copia el fondo externo a la carpeta interna del proyecto y retorna la nueva ruta."""
        if not ext_path or not os.path.exists(ext_path): return None
        
        # Si la imagen ya está dentro de la carpeta fondos, no hacer nada
        if os.path.abspath(os.path.dirname(ext_path)) == os.path.abspath(self.bg_dir):
            return ext_path
            
        ext = os.path.splitext(ext_path)[1]
        internal_path = os.path.join(self.bg_dir, f"page_{page_num}{ext}")
        shutil.copy2(ext_path, internal_path)
        return internal_path

    def update_font_mapping(self, font_mappings: Dict[str, Any]):
        self.data["font_mappings"] = font_mappings
        self.save()

    def get_font_mapping(self) -> Dict[str, Any]:
        return self.data.get("font_mappings", {})

    def save_page_translation(self, page_num: int, mode: str, bg_path: Optional[str], blocks: list):
        # Aseguramos que la imagen se guarde en el ecosistema
        internal_bg = self.import_background(page_num, bg_path) if mode == "editorial" else None
        
        self.data["pages"][str(page_num)] = {
            "mode": mode,
            "bg_path": internal_bg,
            "blocks": blocks
        }
        self.save()

    def get_page_cache(self, page_num: int) -> Optional[Dict[str, Any]]:
        return self.data["pages"].get(str(page_num))

    def get_all_page_modes(self) -> Dict[int, Dict]:
        return {int(k): {"mode": v["mode"], "bg_path": v.get("bg_path")} for k, v in self.data["pages"].items()}

    def is_page_translated(self, page_num: int) -> bool:
        return str(page_num) in self.data["pages"]

    def get_translated_pages_count(self) -> int:
        return len(self.data["pages"])