import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class SpatialOverflowError(Exception):
    """Excepción cuando el texto traducido es demasiado largo y desbordará la caja del PDF."""
    pass

def validate_spatial_fit(original_text: str, translated_text: str) -> bool:
    """
    Valida que la traducción quepa visualmente en el mismo bloque que el original.
    Permite un margen de expansión lógica antes de considerar que "rompe el diseño".
    """
    len_orig = len(original_text)
    len_trans = len(translated_text)
    
    # Tolerancia: Permitimos que la traducción sea hasta un 15% más larga 
    # (muy común al pasar de Inglés a Español) o que se reduzca libremente.
    max_allowed_length = int(len_orig * 1.15)
    
    # Para bloques muy cortos (ej: títulos), damos un margen fijo extra de 5 caracteres
    if len_orig < 20:
        max_allowed_length += 5

    if len_trans > max_allowed_length:
        error_msg = (
            f"DESBORDAMIENTO DE CAJA -> "
            f"Límite visual: {max_allowed_length} chars | "
            f"Generado: {len_trans} chars. Se requiere resumen."
        )
        raise SpatialOverflowError(error_msg)
    
    return True