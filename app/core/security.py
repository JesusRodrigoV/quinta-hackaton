import hashlib
import json
from typing import Any, Dict
from app.core.config import settings


def calculate_block_hash(previous_hash: str, event_type: str, actor: str, payload: Dict[str, Any]) -> str:
    """
    Calcula un hash SHA-256 único y determinista para un registro de auditoría.
    
    Combina el hash del registro inmediatamente anterior con los datos clave 
    del evento actual y una sal secreta del sistema.
    """
    # 1. Serializar el payload JSON de forma estricta ordenando las llaves.
    # Esto garantiza que el mismo diccionario genere SIEMPRE el mismo string.
    serialized_payload = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    
    # 2. Construir la cadena del bloque de datos con un separador claro
    block_string = (
        f"{previous_hash}||"
        f"{event_type}||"
        f"{actor}||"
        f"{serialized_payload}||"
        f"{settings.SECRET_CRYPTO_SALT}"
    )
    
    # 3. Generar y retornar el hash en formato hexadecimal
    return hashlib.sha256(block_string.encode("utf-8")).hexdigest()