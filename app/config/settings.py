import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
VOICES_DIR = BASE_DIR / "voices"
DATA_DIR = BASE_DIR / "data"

VOICES_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# LLM
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

# STT
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu").lower()
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8").lower()

# TTS
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "omnivoice").lower()
VOICE_REFERENCE_AUDIO = os.getenv("VOICE_REFERENCE_AUDIO", "voices/my_voice.wav")
VOICE_REFERENCE_TEXT = os.getenv("VOICE_REFERENCE_TEXT", "")
PIPER_VOICE = os.getenv("PIPER_VOICE", "en_US-lessac-medium")
EDGE_TTS_VOICE = os.getenv("EDGE_TTS_VOICE", "en-US-AriaNeural")

# Interaction
WAKE_WORD_ENABLED = os.getenv("WAKE_WORD_ENABLED", "false").lower() in ("true", "1", "yes")
WAKE_WORD = os.getenv("WAKE_WORD", "hey assistant").lower()

# Server
PORT = int(os.getenv("PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
