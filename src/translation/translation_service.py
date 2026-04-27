import logging

# IMPORTACIONES ABSOLUTAS (Sin los "..")
from lm_studio_integration.client import LMStudioClient
from validation_pipeline.translation_checker import validate_translation_length, LengthValidationError

class TranslationService:
    def __init__(self):
        self.llm_client = LMStudioClient()
        self.max_retries = 3

    def translate_with_constraints(self, word: str, source: str, target: str) -> str:
        """
        Traduce una palabra asegurando que cumple la regla 1:1.
        Implementa un bucle de reintento si el LLM falla la validación de longitud.
        """
        required_length = len(word)
        
        # Ignorar puntuación simple o espacios vacíos
        if required_length == 0 or word.isspace():
            return word

        for attempt in range(1, self.max_retries + 1):
            logging.info(f"Pidiendo traducción al LLM: '{word}' (Req: {required_length} chars) - Intento {attempt}/{self.max_retries}")
            
            # 1. Solicitar al LLM
            llm_output = self.llm_client.generate_translation(word, source, target, required_length)
            
            if not llm_output:
                return "<ERROR_LLM>"
                
            # 2. Validar a través del pipeline crítico
            try:
                validate_translation_length(word, llm_output)
                logging.info(f"✅ TRADUCCIÓN ACEPTADA: '{word}' -> '{llm_output}'")
                return llm_output
            except LengthValidationError as e:
                logging.warning(f"❌ FALLO DE LONGITUD: El LLM generó '{llm_output}' (len {len(llm_output)}). Esperado: {required_length}")
                
        # Si agota los intentos, forzamos un truncamiento o padding visual
        logging.error(f"Se agotaron los intentos para '{word}'. Forzando longitud.")
        return self._force_length(llm_output, required_length)

    def _force_length(self, text: str, required_length: int) -> str:
        """Medida de contingencia drástica si el LLM es incapaz de cumplir la regla."""
        if len(text) > required_length:
            return text[:required_length]  # Recorta
        else:
            return text.ljust(required_length, '-') # Rellena (padding)