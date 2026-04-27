import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class LengthValidationError(Exception):
    """Excepción lanzada cuando una traducción no cumple con la restricción de longitud 1:1."""
    pass

def validate_translation_length(original_word: str, translated_word: str) -> bool:
    """
    Valida estrictamente que la palabra traducida tenga la misma cantidad 
    de caracteres que la palabra original.
    
    :param original_word: La palabra extraída del PDF original.
    :param translated_word: La salida generada por el LLM.
    :return: True si es válida.
    :raises: LengthValidationError si las longitudes no coinciden.
    """
    len_orig = len(original_word)
    len_trans = len(translated_word)
    
    if len_orig != len_trans:
        error_msg = (
            f"VIOLACIÓN DE REGLA 1:1 -> "
            f"Original: '{original_word}' ({len_orig} chars) | "
            f"Generado: '{translated_word}' ({len_trans} chars)"
        )
        raise LengthValidationError(error_msg)
    
    return True

def enforce_translation(original_word: str, translated_word: str) -> str:
    """
    Simula el pipeline de enforcing. Si falla, el sistema debería reintentar (aquí lo simulamos).
    """
    try:
        validate_translation_length(original_word, translated_word)
        logging.info(f"✅ VALIDADO: '{original_word}' -> '{translated_word}' (Longitud: {len(original_word)})")
        return translated_word
    except LengthValidationError as e:
        logging.error(f"❌ REPROBADO: {e}")
        # Aquí iría la lógica de reintento contra el LLM (Constraint Decoding)
        return "<NECESITA_REINTENTO>"