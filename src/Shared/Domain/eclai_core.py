# src/Shared/Domain/eclai_core.py
# Sistema de identificación ECLAI v4.0 (Jerarquía Espacial Pura)

ALPHABET = "AEIOUaeiouBCDFGHJKLMNPQRSTVWXYZbcdfghjklmnpqrstvwxyz0123456789"
BASE = len(ALPHABET)

def get_level_from_jid_length(jid_len: int) -> int:
    # TABLA DE NIVELES ACTUALIZADA (Sin Época)
    if jid_len == 2: return 1    # Caos
    if jid_len == 4: return 2    # Abismos
    if jid_len == 6: return 3    # Realidad
    # SALTO: Época (antiguo 4) desaparece.
    if jid_len == 8: return 4    # Galaxia (Antes 5)
    if jid_len == 10: return 5   # Sistema Estelar
    if jid_len == 12: return 6   # Planeta
    if jid_len == 14: return 7   # Hemisferio
    if jid_len == 16: return 8   # Continente
    if jid_len == 18: return 9   # Territorio
    if jid_len == 20: return 10  # Subterritorio
    if jid_len == 22: return 11  # Asentamiento
    if jid_len == 24: return 12  # Lugar
    if jid_len == 26: return 13  # Raza
    if jid_len == 28: return 14  # Subraza
    if jid_len == 30: return 15  # Clase
    # La entidad final ahora es Nivel 16 (34 caracteres)
    if jid_len == 34: return 16  # Entidad (4 dígitos)
    
    raise ValueError(f"Longitud de J-ID no válida para v4.0: {jid_len}")

def split_nid(nid: str):
    i = 0
    while i < len(nid) and nid[i].isdigit(): i += 1
    return nid[:i], nid[i:]

def encode_eclai126(text: str) -> str:
    if not text: return ""
    num = int.from_bytes(text.encode("ascii"), "big")
    if num == 0: return ALPHABET[0]
    out = []
    while num:
        num, r = divmod(num, BASE)
        out.append(ALPHABET[r])
    return "".join(reversed(out))

def decode_eclai126(encoded: str) -> str:
    if not encoded: return ""
    num = 0
    for c in encoded: num = num * BASE + ALPHABET.index(c)
    byte_len = (num.bit_length() + 7) // 8
    return num.to_bytes(byte_len or 1, "big").decode("ascii")

def nid_to_encoded(nid: str) -> str:
    return encode_eclai126(nid)

def construir_jid(ruta_base: str, nivel: int, segmento_final: str) -> str:
    # Validación de Nivel 1
    if nivel == 1:
        if len(segmento_final) != 2: raise ValueError("Nivel 1 requiere 2 dígitos")
        return segmento_final

    # Validación base
    if len(ruta_base) % 2 != 0 or not ruta_base.isdigit():
        raise ValueError("ruta_base debe ser par y dígitos")
    
    niveles_base = len(ruta_base) // 2
    if nivel <= niveles_base:
        raise ValueError(f"El nivel objetivo ({nivel}) debe ser mayor que la base ({niveles_base})")

    # NIVEL FINAL (ENTIDAD) - Ahora es el 16
    if nivel == 16:
        if len(segmento_final) != 4: 
            raise ValueError("Nivel 16 (Entidad) requiere 4 dígitos numéricos")
        # Relleno hasta llegar al nivel 16 desde donde estemos
        # Objetivo: 2 chars * 15 niveles + 4 chars = 34 chars total
        # ruta_base tiene (niveles_base * 2)
        # ceros necesarios = (15 - niveles_base) * 2
        ceros = "00" * (15 - niveles_base)
        return ruta_base + ceros + segmento_final
    else:
        # Niveles intermedios (2 dígitos)
        if len(segmento_final) != 2: 
            raise ValueError(f"Nivel {nivel} requiere segmento de 2 dígitos")
        ceros_intermedios = "00" * (nivel - niveles_base - 1)
        return ruta_base + ceros_intermedios + segmento_final

def generar_nid(jid: str, tipo: str, numero: int) -> str:
    return f"{jid}{tipo}{numero:02d}"