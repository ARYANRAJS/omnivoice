import logging
from app.tts.base import TTSProvider
from app.tts.omnivoice import OmniVoiceProvider
from app.tts.piper import PiperTTSProvider
from app.tts.edge import EdgeTTSProvider
from app.config import settings

logger = logging.getLogger(__name__)

def get_tts_provider(provider_name: str = None) -> TTSProvider:
    name = (provider_name or settings.TTS_PROVIDER).lower()
    if name == "omnivoice":
        return OmniVoiceProvider()
    elif name == "piper":
        return PiperTTSProvider()
    elif name == "edge":
        return EdgeTTSProvider()
    else:
        logger.warning(f"Unknown TTS provider '{name}'. Defaulting to Edge TTS.")
        return EdgeTTSProvider()

async def synthesize_speech(text: str, provider_name: str = None) -> bytes:
    """
    Synthesize text with requested provider and graceful fallback.
    Fallback hierarchy: OmniVoice -> Piper -> Edge
    """
    selected_name = (provider_name or settings.TTS_PROVIDER).lower()

    # Step 1: Try requested provider
    if selected_name == "omnivoice":
        try:
            logger.info("Synthesizing audio with OmniVoice (personal voice cloning)...")
            provider = OmniVoiceProvider()
            return await provider.synthesize(text)
        except Exception as e:
            logger.warning(f"OmniVoice synthesis failed ({e}). Falling back to Piper TTS.")
            selected_name = "piper"

    if selected_name == "piper":
        try:
            logger.info("Synthesizing audio with Piper TTS...")
            provider = PiperTTSProvider()
            return await provider.synthesize(text)
        except Exception as e:
            logger.warning(f"Piper TTS synthesis failed ({e}). Falling back to Edge TTS.")
            selected_name = "edge"

    # Step 3: Edge TTS fallback
    logger.info("Synthesizing audio with Edge TTS fallback...")
    provider = EdgeTTSProvider()
    return await provider.synthesize(text)
