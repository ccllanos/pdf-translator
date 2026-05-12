import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class SpatialOverflowError(Exception):
    pass

class EmptyTranslationError(Exception):
    pass

def validate_spatial_fit(original_text: str, translated_text: str) -> bool:
    if not translated_text or translated_text.isspace():
        raise EmptyTranslationError("El LLM devolvió una cadena vacía o nula.")

    len_orig = len(original_text)
    len_trans = len(translated_text)
    
    max_allowed_length = int(len_orig * 1.15)
    if len_orig < 20:
        max_allowed_length += 5

    if len_trans > max_allowed_length:
        error_msg = f"Desbordamiento: Límite {max_allowed_length} chars | Generado {len_trans} chars."
        raise SpatialOverflowError(error_msg)
    
    return True