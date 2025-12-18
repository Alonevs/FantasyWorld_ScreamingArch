import uuid
from dataclasses import dataclass

@dataclass(frozen=True)
class WorldID:
    value: str

    @staticmethod
    def from_string(val: str):
        return WorldID(val)

    @staticmethod
    def next_nanoid():
        import nanoid
        return WorldID(nanoid.generate('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz-', 10))
    
    def __str__(self):
        return self.value