import logging
import re
from lm_studio_integration.client import LMStudioClient
from validation_pipeline.translation_checker import validate_spatial_fit, SpatialOverflowError

class TranslationService:
    def __init__(self):
        self.llm_client = LMStudioClient()
        self.max_retries = 3

    def _clean_chatty_llm(self, text: str) -> str:
        """Limpiador de formato avanzado para modelos grandes."""
        cleaned = text.strip()
        
        # Eliminar bloques de código Markdown (ej: ```spanish ... ```)
        cleaned = re.sub(r"```[a-zA-Z]*\n(.*?)\n```", r"\1", cleaned, flags=re.DOTALL)
        cleaned = cleaned.replace("```", "")
        
        # Eliminar comillas externas
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
            
        chatty_patterns = [
            r"(?i)^here is the translation:?\s*",
            r"(?i)^translation:?\s*",
            r"(?i)^sure[,!]\s*here.+:?\s*",
            r"(?i)^the translated text is:?\s*"
        ]
        for pattern in chatty_patterns:
            cleaned = re.sub(pattern, "", cleaned).strip()
            
        return cleaned.strip()

    def translate_block(self, text_block: str, source: str, target: str) -> str:
        if not text_block or text_block.isspace():
            return text_block

        current_prompt_constraint = "Translate the text directly and precisely."
        max_chars = int(len(text_block) * 1.15) + (5 if len(text_block) < 20 else 0)

        for attempt in range(1, self.max_retries + 1):
            logging.info(f"Traduciendo Bloque - Intento {attempt}/{self.max_retries}")
            
            # Prompt más estructurado para modelos 20B+
            system_prompt = (
                f"You are a strict translation engine. Translate from {source} to {target}. "
                f"{current_prompt_constraint} "
                f"RULES: "
                f"1. Output ONLY the translated text. "
                f"2. NO explanations, NO markdown, NO formatting. "
                f"3. Do NOT copy the original text."
            )

            try:
                response = self.llm_client.client.chat.completions.create(
                    model=self.llm_client.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Text:\n{text_block}"}
                    ],
                    temperature=0.1,
                    max_tokens=250
                )
                
                llm_output = self._clean_chatty_llm(response.choices[0].message.content)
                
                # ¡DETECTOR DE IMITADORES!
                if llm_output.lower() == text_block.lower():
                    logging.warning("⚠️ El modelo devolvió el texto original. Forzando reintento.")
                    current_prompt_constraint = f"TRANSLATE TO {target.upper()}! Do not return English!"
                    continue # Saltamos al siguiente intento
                
                validate_spatial_fit(text_block, llm_output)
                logging.info(f"✅ TRADUCCIÓN ACEPTADA: {llm_output[:30]}...")
                return llm_output
                
            except SpatialOverflowError as e:
                logging.warning(f"❌ FALLO ESPACIAL: {e}")
                current_prompt_constraint = f"Summarize to LESS THAN {max_chars} characters!"
            except Exception as e:
                logging.error(f"Error de conexión LLM: {e}")
                return "<ERROR_LLM>"
                
        logging.error("Se agotaron los intentos. Forzando longitud visual.")
        return llm_output[:max_chars]