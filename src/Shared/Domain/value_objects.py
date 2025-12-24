from dataclasses import dataclass

@dataclass(frozen=True)
class WorldID:
    """
    Value Object que representa el Identificador de un Mundo o Entidad.
    Se utiliza tanto para los J-ID (Jerárquicos) como para los NanoID (Públicos).
    Al ser frozen=True, garantiza la inmutabilidad de la identidad del objeto.
    """
    value: str

    @staticmethod
    def from_string(val: str):
        """Crea una instancia de WorldID a partir de una cadena de texto."""
        return WorldID(val)

    @staticmethod
    def next_nanoid():
        """
        Genera un nuevo Identificador Público (NanoID) aleatorio y corto.
        Utiliza un alfabeto de 64 caracteres para URLs seguras.
        """
        import nanoid
        # Alfabeto optimizado para legibilidad en URLs
        return WorldID(nanoid.generate('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz-', 10))
    
    def __str__(self):
        """Representación textual del ID para operaciones de log y templates."""
        return self.value