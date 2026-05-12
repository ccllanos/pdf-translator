import logging
import re
from deep_translator import GoogleTranslator
from lm_studio_integration.client import LMStudioClient
from validation_pipeline.translation_checker import validate_spatial_fit, SpatialOverflowError

class TranslationService:
    def __init__(self):
        self.llm_client = LMStudioClient()
        self.max_retries = 2

    def _clean_chatty_llm(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith('"') and cleaned.endswith('"'): cleaned = cleaned[1:-1]
        chatty_patterns = [r"(?i)^here is the translation:?\s*", r"(?i)^translation:?\s*", r"(?i)^sure[,!]\s*here.+:?\s*"]
        for pattern in chatty_patterns:
            cleaned = re.sub(pattern, "", cleaned).strip()
        return cleaned

    def translate_block(self, text_block: str, source: str, target: str, engine: str = "llm") -> str:
        if not text_block or text_block.isspace():
            return text_block

        # RUTA 1: GOOGLE TRANSLATE (Rápido, sin restricciones)
        if engine == "google":
            logging.info("Usando Google Translate (Modo rápido)...")
            try:
                # Target.lower() convierte "Spanish" a "spanish", formato que deep-translator acepta
                translated = GoogleTranslator(source='auto', target=target.lower()).translate(text_block)
                return translated
            except Exception as e:
                logging.error(f"Error con Google Translate: {e}. Usando texto original.")
                return text_block

        # RUTA 2: LLM LOCAL (Lento, controlado semánticamente)
        current_prompt_constraint = "Translate the text exactly."
        max_chars = int(len(text_block) * 1.15) + (5 if len(text_block) < 20 else 0)

        for attempt in range(1, self.max_retries + 1):
            logging.info(f"Traduciendo con LLM Local - Intento {attempt}")
            
            system_prompt = (
                f"You are a strict Translation API. Translate from {source} to {target}. "
                f"{current_prompt_constraint} "
                f"IMPORTANT: Respond ONLY with the final translated text."
            )

            try:
                response = self.llm_client.client.chat.completions.create(
                    model=self.llm_client.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Text:\n{text_block}"}
                    ],
                    temperature=0.1, max_tokens=250
                )
                
                llm_output = self._clean_chatty_llm(response.choices[0].message.content)
                validate_spatial_fit(text_block, llm_output)
                return llm_output
                
            except SpatialOverflowError as e:
                logging.warning(f"❌ FALLO ESPACIAL: {e}")
                current_prompt_constraint = f"Summarize translation so it is LESS THAN {max_chars} characters!"
            except Exception as e:
                logging.error(f"Error LLM: {e}")
                return "<ERROR_LLM>"
                
        logging.error("LLM falló reiteradamente. Forzando longitud.")
        return llm_output[:max_chars]