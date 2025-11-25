import uuid
from dataclasses import dataclass

@dataclass(frozen=True)
class WorldID:
    value: str

    @staticmethod
    def next_id():
        return WorldID(str(uuid.uuid4()))
    
    def __str__(self):
        return self.value