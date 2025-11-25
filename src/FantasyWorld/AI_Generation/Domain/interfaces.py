from abc import ABC, abstractmethod

class LoreGenerator(ABC):
    @abstractmethod
    def generate_description(self, prompt: str) -> str:
        pass

class ImageGenerator(ABC):
    @abstractmethod
    def generate_concept_art(self, prompt: str) -> str:
        pass