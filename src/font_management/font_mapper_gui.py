import tkinter as tk
from tkinter import ttk, messagebox
from typing import Set, Dict

class FontMapperGUI:
    def __init__(self, pdf_fonts: Set[str]):
        self.pdf_fonts = self._clean_font_names(pdf_fonts)
        self.final_mapping = {}
        
        # Fuentes seguras que PyMuPDF puede inyectar nativamente (Base 14)
        # En el futuro, aquí cargaremos las fuentes .ttf de tu Windows.
        self.available_system_fonts = [
            "Helvetica (Sans-Serif)", 
            "Times-Roman (Serif)", 
            "Courier (Mono)", 
            "Symbol", 
            "ZapfDingbats"
        ]
        
        self.font_to_pdf_code = {
            "Helvetica (Sans-Serif)": "helv",
            "Times-Roman (Serif)": "tiro",
            "Courier (Mono)": "cour",
            "Symbol": "symb",
            "ZapfDingbats": "zadb"
        }

    def _clean_font_names(self, raw_fonts: Set[str]) -> Set[str]:
        """Limpia los nombres internos del PDF (ej. 'AAAAAA+Arial-Bold' -> 'Arial-Bold')"""
        clean_fonts = set()
        for font in raw_fonts:
            name = font.split('+')[-1] if '+' in font else font
            clean_fonts.add(name)
        return clean_fonts

    def show(self) -> Dict[str, str]:
        """Abre la ventana gráfica y pausa la ejecución hasta que el usuario confirme."""
        self.root = tk.Tk()
        self.root.title("Inspector de Fuentes - PDF Translator")
        self.root.geometry("600x400")
        
        # Estilos
        style = ttk.Style()
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
        
        # Encabezado
        header_frame = ttk.Frame(self.root, padding=15)
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text="🎨 Mapeo de Tipografías (Estilo 'Reemplazar Color')", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(header_frame, text="Se han detectado las siguientes fuentes en el documento.\nSelecciona con cuál deseas reemplazarlas en el PDF traducido:").pack(anchor=tk.W, pady=(5,0))

        # Contenedor principal
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Crear tabla de mapeo
        self.comboboxes = {}
        
        # Encabezados de tabla
        ttk.Label(main_frame, text="Fuente Original (En el PDF)", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text="Fuente de Reemplazo (Destino)", font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky=tk.W, pady=5, padx=20)

        for idx, font in enumerate(self.pdf_fonts, start=1):
            # Nombre de la fuente original
            ttk.Label(main_frame, text=f"• {font}").grid(row=idx, column=0, sticky=tk.W, pady=5)
            
            # Dropdown para elegir el reemplazo
            cb = ttk.Combobox(main_frame, values=self.available_system_fonts, state="readonly", width=30)
            
            # Pre-seleccionar inteligentemente
            if "times" in font.lower() or "serif" in font.lower():
                cb.set("Times-Roman (Serif)")
            elif "cour" in font.lower() or "mono" in font.lower():
                cb.set("Courier (Mono)")
            else:
                cb.set("Helvetica (Sans-Serif)") # Por defecto
                
            cb.grid(row=idx, column=1, sticky=tk.W, pady=5, padx=20)
            self.comboboxes[font] = cb

        # Botones inferiores
        btn_frame = ttk.Frame(self.root, padding=15)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(btn_frame, text="Cancelar y Abortar", command=self._abort).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Confirmar y Traducir ➔", command=self._confirm).pack(side=tk.RIGHT)

        # Iniciar el bucle de la GUI (Bloquea la consola hasta cerrarse)
        self.root.mainloop()
        
        return self.final_mapping

    def _confirm(self):
        # Recolectar las selecciones del usuario
        for original_font, cb in self.comboboxes.items():
            selected_display_name = cb.get()
            # Mapear el nombre visual ("Helvetica") al código que usa PyMuPDF ("helv")
            self.final_mapping[original_font] = self.font_to_pdf_code[selected_display_name]
        
        self.root.destroy()

    def _abort(self):
        if messagebox.askyesno("Abortar", "¿Estás seguro de que quieres cancelar la traducción?"):
            self.final_mapping = None
            self.root.destroy()