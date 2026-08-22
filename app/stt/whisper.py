import os
import io
import tempfile
import asyncio
import logging
from functools import lru_cache
from app.config import settings

logger = logging.getLogger(__name__)

_model_instance = None

def get_whisper_model():
    """Lazy load Whisper model instance using faster-whisper or openai-whisper fallback."""
    global _model_instance
    if _model_instance is not None:
        return _model_instance

    logger.info(f"Loading Whisper model '{settings.WHISPER_MODEL}' on device '{settings.WHISPER_DEVICE}' ({settings.WHISPER_COMPUTE_TYPE})...")

    try:
        from faster_whisper import WhisperModel
        _model_instance = WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE,
            cpu_threads=4
        )
        logger.info("Successfully loaded Faster-Whisper model.")
        return _model_instance
    except Exception as e:
        logger.warning(f"Faster-Whisper load failed ({e}), attempting standard openai-whisper fallback...")
        try:
            import whisper
            _model_instance = whisper.load_model(settings.WHISPER_MODEL, device=settings.WHISPER_DEVICE)
            logger.info("Successfully loaded standard Whisper model.")
            return _model_instance
        except Exception as err:
            logger.error(f"Failed to load standard Whisper model: {err}")
            raise RuntimeError(f"Could not load Whisper STT model: {err}")

async def transcribe(audio_bytes: bytes, suffix: str = ".wav") -> str:
    """Asynchronously transcribe raw audio bytes into text."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _transcribe_sync, audio_bytes, suffix)

def _transcribe_sync(audio_bytes: bytes, suffix: str = ".wav") -> str:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        model = get_whisper_model()
        # Check type of model (Faster-Whisper vs standard whisper)
        model_type = type(model).__name__

        if model_type == "WhisperModel":
            segments, info = model.transcribe(tmp_path, beam_size=5)
            text = " ".join([seg.text for seg in segments]).strip()
            return text
        else:
            # Standard openai-whisper
            result = model.transcribe(tmp_path)
            return result.get("text", "").strip()
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return ""
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
