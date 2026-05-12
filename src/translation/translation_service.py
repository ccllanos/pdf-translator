import logging
import re
from deep_translator import GoogleTranslator
from lm_studio_integration.client import LMStudioClient
from validation_pipeline.translation_checker import validate_spatial_fit, SpatialOverflowError, EmptyTranslationError

class TranslationService:
    def __init__(self):
        self.llm_client = LMStudioClient()
        self.max_retries = 3

    def _clean_chatty_llm(self, text: str) -> str:
        if not text: return ""
        
        # 1. Eliminar bloques de Markdown (ej: ```spanish ... ``` o ``` ... ```)
        # Esto es vital para modelos de 20B+ que gustan de formatear la salida
        text = re.sub(r"```[a-zA-Z]*\n(.*?)```", r"\1", text, flags=re.DOTALL)
        
        cleaned = text.strip()
        
        # 2. Quitar comillas iniciales y finales si el modelo las pone
        if cleaned.startswith('"') and cleaned.endswith('"'): 
            cleaned = cleaned[1:-1]
            
        # 3. Eliminar charla conversacional en MÚLTIPLES idiomas
        chatty_patterns = [
            r"(?i)^here is the translation[:\s]*",
            r"(?i)^translation[:\s]*",
            r"(?i)^sure[,!]\s*here.+[:\s]*",
            r"(?i)^aquí tienes.+[:\s]*",
            r"(?i)^aquí está.+[:\s]*",
            r"(?i)^la traducción.+[:\s]*",
            r"(?i)^traducción[:\s]*",
        ]
        
        for pattern in chatty_patterns:
            cleaned = re.sub(pattern, "", cleaned).strip()
            
        return cleaned.strip()

    def translate_block(self, text_block: str, source: str, target: str, engine: str = "llm") -> str:
        if not text_block or text_block.isspace():
            return text_block

        if engine == "google":
            logging.info("Usando Google Translate...")
            try:
                translated = GoogleTranslator(source='auto', target=target.lower()).translate(text_block)
                if translated and not translated.isspace():
                    return translated
            except Exception as e:
                logging.error(f"Error con Google Translate: {e}")
            return text_block

        current_prompt_constraint = "Translate the text exactly."
        max_chars = int(len(text_block) * 1.15) + (5 if len(text_block) < 20 else 0)
        llm_output = text_block # Fallback por defecto

        for attempt in range(1, self.max_retries + 1):
            logging.info(f"Traduciendo con LLM Local (20B+) - Intento {attempt}")
            
            # Prompt reforzado para modelos grandes
            system_prompt = (
                f"You are a strict Translation API. Translate from {source} to {target}. "
                f"{current_prompt_constraint} "
                f"IMPORTANT: Output ONLY the raw translated string. No markdown, no ticks, no conversational text."
            )

            try:
                response = self.llm_client.client.chat.completions.create(
                    model=self.llm_client.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text_block} # Enviamos el texto directo
                    ],
                    temperature=0.1, 
                    max_tokens=250
                )
                
                raw_response = response.choices[0].message.content
                llm_output = self._clean_chatty_llm(raw_response)
                
                # Pasamos por el validador reforzado
                validate_spatial_fit(text_block, llm_output)
                return llm_output
                
            except SpatialOverflowError as e:
                logging.warning(f"❌ FALLO ESPACIAL: {e}")
                current_prompt_constraint = f"Summarize translation so it is STRICTLY LESS THAN {max_chars} characters!"
            except EmptyTranslationError as e:
                logging.warning(f"❌ FALLO DE CONTENIDO: {e} El modelo probablemente se enredó con el formato. Reintentando...")
                current_prompt_constraint = "Translate exactly. DO NOT use markdown blocks like ```."
            except Exception as e:
                logging.error(f"Error LLM: {e}")
                return text_block # En caso de error severo, inyectamos el original en lugar de romper el PDF
                
        logging.error("LLM falló reiteradamente. Forzando longitud.")
        return llm_output[:max_chars] if llm_output else text_block