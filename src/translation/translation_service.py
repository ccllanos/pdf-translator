import logging
from lm_studio_integration.client import LMStudioClient
from validation_pipeline.translation_checker import validate_spatial_fit, SpatialOverflowError

class TranslationService:
    def __init__(self):
        self.llm_client = LMStudioClient()
        self.max_retries = 2

    def translate_block(self, text_block: str, source: str, target: str) -> str:
        """Traduce un bloque completo (párrafo) respetando el espacio visual."""
        
        if not text_block or text_block.isspace():
            return text_block

        current_prompt_constraint = "Translate accurately, keeping a natural tone."
        max_chars = int(len(text_block) * 1.15) + (5 if len(text_block) < 20 else 0)

        for attempt in range(1, self.max_retries + 1):
            logging.info(f"Traduciendo Bloque ({len(text_block)} chars) - Intento {attempt}")
            
            # Ajustamos el cliente (no necesitamos required_length exacto, solo pasamos el prompt modificado)
            system_prompt = (
                f"You are a professional document translator. Translate from {source} to {target}. "
                f"CRITICAL CONSTRAINT: {current_prompt_constraint} "
                f"Output ONLY the translation. No thinking process, no reasoning, no quotes."
            )

            try:
                response = self.llm_client.client.chat.completions.create(
                    model=self.llm_client.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Text to translate:\n\n{text_block}"}
                    ],
                    temperature=0.3,
                    max_tokens=500  # Espacio amplio para traducir párrafos enteros
                )
                
                llm_output = response.choices[0].message.content.strip()
                
                # Validación Espacial
                validate_spatial_fit(text_block, llm_output)
                logging.info("✅ TRADUCCIÓN ACEPTADA (Encaja en la caja delimitadora)")
                return llm_output
                
            except SpatialOverflowError as e:
                logging.warning(f"❌ FALLO ESPACIAL: {e}")
                # Modificamos la restricción para el siguiente intento
                current_prompt_constraint = f"Summarize the translation to be STRICTLY LESS THAN {max_chars} characters. Be concise!"
            except Exception as e:
                logging.error(f"Error de conexión LLM: {e}")
                return "<ERROR_LLM>"
                
        logging.error("Se agotaron los intentos. Forzando ajuste de texto en la caja.")
        return llm_output[:max_chars] + "..." # Truncamiento suave al final del bloque