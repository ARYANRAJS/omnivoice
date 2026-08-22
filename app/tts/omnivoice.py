import os
import io
import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Optional

from app.tts.base import TTSProvider
from app.config import settings

logger = logging.getLogger(__name__)

class OmniVoiceProvider(TTSProvider):
    """
    OmniVoice Zero-Shot Personal Voice Cloning Provider.
    Clones voice using reference audio (e.g., voices/my_voice.wav).
    Auto-transcribes reference audio if reference text is not provided.
    """
    def __init__(self, ref_audio_path: Optional[str] = None, ref_text: Optional[str] = None):
        self.ref_audio_path = ref_audio_path or settings.VOICE_REFERENCE_AUDIO
        self.ref_text = ref_text or settings.VOICE_REFERENCE_TEXT
        self.model = None
        self.resolved_ref_text = None

    @property
    def name(self) -> str:
        return "omnivoice"

    def _resolve_audio_path(self) -> Path:
        p = Path(self.ref_audio_path)
        if not p.is_absolute():
            p = settings.BASE_DIR / p
        return p

    async def _ensure_ref_text(self, abs_audio_path: Path) -> str:
        """Auto-transcribe reference audio if reference text is missing."""
        if self.ref_text and self.ref_text.strip():
            return self.ref_text.strip()

        if self.resolved_ref_text:
            return self.resolved_ref_text

        logger.info(f"Reference text not provided. Auto-transcribing reference audio '{abs_audio_path.name}' using local Whisper...")
        try:
            from app.stt.whisper import transcribe
            with open(abs_audio_path, "rb") as f:
                audio_bytes = f.read()
            text = await transcribe(audio_bytes)
            logger.info(f"Auto-transcribed reference text: '{text}'")
            self.resolved_ref_text = text
            return text
        except Exception as e:
            logger.warning(f"Auto-transcription of reference audio failed: {e}")
            return ""

    async def synthesize(self, text: str) -> bytes:
        if not text.strip():
            return b""

        abs_audio_path = self._resolve_audio_path()
        if not abs_audio_path.exists():
            msg = f"Reference voice audio file not found at '{abs_audio_path}'. Please upload or select a voice sample."
            logger.error(msg)
            raise FileNotFoundError(msg)

        ref_text = await self._ensure_ref_text(abs_audio_path)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._synthesize_sync, text, str(abs_audio_path), ref_text)

    def _synthesize_sync(self, text: str, ref_audio_str: str, ref_text: str) -> bytes:
        """Synchronous execution of zero-shot voice cloning with OmniVoice."""
        try:
            # Try importing OmniVoice library (k2-fsa/OmniVoice or omnivoice package)
            from omnivoice import OmniVoice
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Initializing OmniVoice engine on device '{device}'...")

            if self.model is None:
                self.model = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map=device)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as out_f:
                out_path = out_f.name

            # Generate cloned voice audio
            self.model.generate(
                text=text,
                reference_audio=ref_audio_str,
                reference_text=ref_text,
                output_path=out_path
            )

            if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                with open(out_path, "rb") as f:
                    audio_bytes = f.read()
                os.unlink(out_path)
                return audio_bytes
            else:
                raise RuntimeError("OmniVoice generated an empty output audio file.")

        except ImportError:
            logger.warning("OmniVoice package ('omnivoice') is not installed or dependencies missing.")
            raise RuntimeError("OmniVoice package is not installed. Run 'pip install omnivoice' or use Piper fallback.")
        except Exception as e:
            logger.error(f"OmniVoice synthesis failed ({e}). Check GPU VRAM/RAM hardware limitations.")
            raise RuntimeError(f"OmniVoice synthesis failed: {e}")
