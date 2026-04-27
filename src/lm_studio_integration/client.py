import logging
from openai import OpenAI
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class LMStudioClient:
    """Cliente para interactuar con un LLM local a través de LM-Studio (API compatible con OpenAI)."""
    
    def __init__(self, base_url: str = "http://localhost:1234/v1", api_key: str = "lm-studio"):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = "local-model" # LM-Studio ignora esto y usa el que esté cargado

    def generate_translation(self, word: str, source_lang: str, target_lang: str, required_length: int) -> Optional[str]:
        """
        Pide al LLM que traduzca una palabra obligándolo a respetar una longitud exacta.
        """
        system_prompt = (
            f"You are a strict translation engine. Translate the word from {source_lang} to {target_lang}. "
            f"RULE: The translation MUST be EXACTLY {required_length} characters long. "
            f"If you can't find a direct translation of that length, use a synonym or abbreviation "
            f"that fits the {required_length} characters constraint perfectly. "
            f"Output ONLY the translated word, no punctuation, no explanations."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Translate this word to exactly {required_length} characters: '{word}'"}
                ],
                temperature=0.3, # Baja temperatura para que sea más determinista
                max_tokens=20
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"Error conectando a LM-Studio: {e}")
            logging.error("Asegúrate de que LM-Studio está abierto y el servidor local está corriendo (Start Server).")
            return None