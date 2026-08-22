import io
import logging
import edge_tts
from app.tts.base import TTSProvider
from app.config import settings

logger = logging.getLogger(__name__)

class EdgeTTSProvider(TTSProvider):
    def __init__(self, voice: str = None):
        self.voice = voice or settings.EDGE_TTS_VOICE

    @property
    def name(self) -> str:
        return "edge"

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text using Microsoft Edge TTS."""
        if not text.strip():
            return b""
        
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            buf = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buf.write(chunk["data"])
            buf.seek(0)
            return buf.read()
        except Exception as e:
            logger.error(f"EdgeTTS synthesis error: {e}")
            raise RuntimeError(f"EdgeTTS failed: {e}")
