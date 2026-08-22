import sys
import os
from pathlib import Path

# Add project root directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import io
import wave
import asyncio
import logging
import uvicorn

from app.config import settings
from app.llm import ollama

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("omnivoice")

def create_sample_voice_file_if_missing():
    """Ensure voices/ directory has at least a default my_voice.wav sample file."""
    sample_file = settings.BASE_DIR / "voices" / "my_voice.wav"
    if not sample_file.exists():
        logger.info("Creating default voice sample file at 'voices/my_voice.wav'...")
        # Create a 1-second silent WAV file as placeholder
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b"\x00" * 32000)
        with open(sample_file, "wb") as f:
            f.write(buf.getvalue())

async def preflight_checks():
    """Run initial system diagnostic checks."""
    logger.info("Running OmniVoice Preflight Checks...")

    # Check Ollama connection
    is_running, msg = await ollama.check_ollama_status()
    if is_running:
        logger.info(f"✓ Ollama status: {msg}")
    else:
        logger.warning(f"Ollama check: {msg}")
        print("\n=======================================================")
        print(" NOTE: Could not connect to Ollama. Please start Ollama first.")
        print(" Command to start Ollama: ollama serve")
        print(f" Target Model: {settings.OLLAMA_MODEL}")
        print("=======================================================\n")

    create_sample_voice_file_if_missing()

def main():
    asyncio.run(preflight_checks())

    logger.info(f"Starting OmniVoice Web Server on http://localhost:{settings.PORT} ...")
    uvicorn.run(
        "app.ui.server:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=False
    )

if __name__ == "__main__":
    main()
