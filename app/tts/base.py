from abc import ABC, abstractmethod

class TTSProvider(ABC):
    """Abstract Base Class for TTS Providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the provider name."""
        pass

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Convert text to WAV or MP3 audio bytes. Returns audio bytes."""
        pass
