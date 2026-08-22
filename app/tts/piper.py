import os
import sys
import io
import wave
import asyncio
import logging
import subprocess
import tempfile
from app.tts.base import TTSProvider
from app.config import settings

logger = logging.getLogger(__name__)

class PiperTTSProvider(TTSProvider):
    def __init__(self, voice: str = None):
        self.voice = voice or settings.PIPER_VOICE

    @property
    def name(self) -> str:
        return "piper"

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text using Piper TTS (via CLI or python module)."""
        if not text.strip():
            return b""

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._synthesize_sync, text)

    def _synthesize_sync(self, text: str) -> bytes:
        # Check if piper executable is in PATH or python piper-tts package is available
        piper_cmd = "piper"
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as out_wav:
                wav_path = out_wav.name

            # Try python -m piper or piper CLI
            cmd = [sys.executable, "-m", "piper", "--model", self.voice, "--output_file", wav_path]
            proc = subprocess.run(cmd, input=text.encode("utf-8"), capture_output=True, timeout=30)

            if proc.returncode != 0:
                # Try standalone executable
                cmd = ["piper", "--model", self.voice, "--output_file", wav_path]
                proc = subprocess.run(cmd, input=text.encode("utf-8"), capture_output=True, timeout=30)

            if proc.returncode == 0 and os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
                with open(wav_path, "rb") as f:
                    audio_bytes = f.read()
                os.unlink(wav_path)
                return audio_bytes
            else:
                raise RuntimeError(f"Piper execution failed: {proc.stderr.decode('utf-8', errors='ignore')}")
        except Exception as e:
            logger.warning(f"Piper TTS failed ({e}). Falling back to Edge TTS.")
            # Fallback inline
            from app.tts.edge import EdgeTTSProvider
            edge = EdgeTTSProvider()
            return asyncio.run(edge.synthesize(text))
