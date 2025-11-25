# src/Shared/Domain/eclai_core.py
# Fusión de ids.py e id_generator.py para ECLAI v3.0

"""
Módulo Core de ECLAI v3.0 (Enhanced Code for Logical and Architectural Identification).

Este módulo gestiona la lógica de generación, codificación y decodificación de identificadores
jerárquicos (J-ID) y narrativos (N-ID) utilizados en todo el sistema.
"""

ALPHABET = "AEIOUaeiouBCDFGHJKLMNPQRSTVWXYZbcdfghjklmnpqrstvwxyz0123456789"
BASE = len(ALPHABET)

def get_level_from_jid_length(jid_len: int) -> int:
    """
    Determina el nivel jerárquico basado en la longitud del J-ID.
    
    Args:
        jid_len (int): Longitud del string del J-ID.
        
    Returns:
        int: El nivel jerárquico (1-17).
        
    Raises:
        ValueError: Si la longitud no corresponde a un nivel válido.
    """
    if jid_len == 2: return 1
    if jid_len == 4: return 2
    if jid_len == 6: return 3
    if jid_len == 8: return 4
    if jid_len == 10: return 5
    if jid_len == 12: return 6
    if jid_len == 14: return 7
    if jid_len == 16: return 8
    if jid_len == 18: return 9
    if jid_len == 20: return 10
    if jid_len == 22: return 11
    if jid_len == 24: return 12
    if jid_len == 26: return 13
    if jid_len == 28: return 14
    if jid_len == 30: return 15
    if jid_len == 32: return 16
    if jid_len == 36: return 17
    raise ValueError(f"Longitud de J-ID no válida: {jid_len}")

def split_nid(nid: str):
    """
    Separa un N-ID en su parte jerárquica (J-ID) y su sufijo narrativo.
    
    Args:
        nid (str): El N-ID completo (ej. "01L01").
        
    Returns:
        tuple: (jid, suffix) donde jid son los dígitos iniciales y suffix el resto.
    """
    i = 0
    while i < len(nid) and nid[i].isdigit():
        i += 1
    return nid[:i], nid[i:]

def to_compact_key(jid: str, suffix: str) -> str:
    """
    Convierte un J-ID y sufijo en una clave compacta para codificación.
    Elimina los ceros redundantes de los niveles intermedios.
    """
    level = get_level_from_jid_length(len(jid))
    if level == 1:
        return f"{level:02d}{jid}{suffix}"
    elif level == 17:
        return f"{level:02d}{jid[:2]}{jid[-4:]}{suffix}"
    else:
        return f"{level:02d}{jid[:2]}{jid[-2:]}{suffix}"

def from_compact_key(compact: str) -> str:
    """
    Reconstruye el J-ID completo a partir de una clave compacta.
    Reinserta los ceros estructurales según el nivel.
    """
    level = int(compact[:2])
    if level == 1:
        jid = compact[2:4]
        suffix = compact[4:]
    elif level == 17:
        raiz = compact[2:4]
        final = compact[4:8]
        suffix = compact[8:]
        jid = raiz + "00" * 15 + final
    else:
        raiz = compact[2:4]
        final = compact[4:6]
        suffix = compact[6:]
        jid = raiz + "00" * (level - 2) + final
    return jid + suffix

def encode_eclai126(text: str) -> str:
    """
    Codifica un string arbitrario en Base62 (Alfabeto personalizado ECLAI).
    """
    if not text: return ""
    num = int.from_bytes(text.encode("ascii"), "big")
    if num == 0: return ALPHABET[0]
    out = []
    while num:
        num, r = divmod(num, BASE)
        out.append(ALPHABET[r])
    return "".join(reversed(out))

def decode_eclai126(encoded: str) -> str:
    """
    Decodifica un string Base62 ECLAI a su representación original.
    """
    if not encoded: return ""
    num = 0
    for c in encoded:
        num = num * BASE + ALPHABET.index(c)
    byte_len = (num.bit_length() + 7) // 8
    return num.to_bytes(byte_len or 1, "big").decode("ascii")

def nid_to_encoded(nid: str) -> str:
    """
    Flujo completo: N-ID -> Clave Compacta -> Código Base62.
    """
    jid, suffix = split_nid(nid)
    compact = to_compact_key(jid, suffix)
    return encode_eclai126(compact)

def encoded_to_nid(encoded: str) -> str:
    """
    Flujo inverso: Código Base62 -> Clave Compacta -> N-ID Completo.
    """
    compact = decode_eclai126(encoded)
    return from_compact_key(compact)

def construir_jid(ruta_base: str, nivel: int, segmento_final: str) -> str:
    """
    Construye un nuevo J-ID hijo a partir de un padre (ruta_base).
    
    Args:
        ruta_base (str): J-ID del padre (o raíz).
        nivel (int): Nivel objetivo del nuevo ID.
        segmento_final (str): Los dígitos identificadores del nuevo nodo.
    """
    if nivel == 1:
        if len(segmento_final) != 2: raise ValueError("Nivel 1 requiere 2 dígitos")
        return segmento_final
    if len(ruta_base) % 2 != 0 or not ruta_base.isdigit():
        raise ValueError("ruta_base inválida")
    niveles_base = len(ruta_base) // 2
    if nivel <= niveles_base: raise ValueError("Nivel objetivo debe ser mayor")
    if nivel == 17:
        if len(segmento_final) != 4: raise ValueError("Nivel 17 requiere 4 dígitos")
        return ruta_base + "00" * 15 + segmento_final
    else:
        if len(segmento_final) != 2: raise ValueError("Requiere 2 dígitos")
        ceros_intermedios = "00" * (nivel - niveles_base - 1)
        return ruta_base + ceros_intermedios + segmento_final

def generar_nid(jid: str, tipo: str, numero: int, capitulo: int = None) -> str:
    """
    Genera un N-ID (Narrativo) estandarizado.
    
    Args:
        jid (str): J-ID de la entidad a la que pertenece.
        tipo (str): Tipo de contenido (H=Historia, L=Lore, R=Regla, E=Evento, N=NPC).
        numero (int): Número secuencial.
        capitulo (int, optional): Número de capítulo (solo para Historias).
    """
    if tipo not in "HLREN": raise ValueError("Tipo inválido")
    base = f"{jid}{tipo}{numero:02d}"
    if capitulo is not None:
        if tipo != "H": raise ValueError("Solo historias tienen capítulos")
        return f"{base}C{capitulo:02d}"
    return base