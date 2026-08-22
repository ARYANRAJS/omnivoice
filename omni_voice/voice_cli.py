"""
OmniVoice — Terminal Voice CLI (Updated with local agent pipeline)
Push-to-talk & live voice chat with local Ollama LLM, tools, memory, and cloned voice.

Usage:
    python -m omni_voice.voice_cli
"""
import asyncio
import io
import os
import sys
import threading
import sounddevice as sd

from app.config import settings
from app.stt import whisper
from app.agent import router
from app.tts import factory as tts_factory
from app.audio import playback

# Audio Config
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"

# ANSI Colors
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
PURPLE = "\033[95m"
RED    = "\033[91m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def _record_blocking() -> bytes:
    """Record microphone until Enter is pressed."""
    frames = []
    def callback(indata, frame_count, time_info, status):
        frames.append(bytes(indata))

    stream = sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=DTYPE,
        callback=callback,
    )
    with stream:
        input()
    return b"".join(frames)

def _pcm_to_wav(pcm: bytes) -> bytes:
    import wave
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm)
    return buf.getvalue()

async def main():
    banner = f"""
{GREEN}╔══════════════════════════════════════════════════════╗
║   🎙  OmniVoice — Fully Local Voice AI Agent        ║
║                                                      ║
║   LLM: {settings.OLLAMA_MODEL:<15}  TTS: {settings.TTS_PROVIDER:<15}║
║   Enter  → start / stop recording                    ║
║   Ctrl+C → quit                                      ║
╚══════════════════════════════════════════════════════╝{RESET}"""
    print(banner)
    print(f"{BLUE}  Ready. Press Enter to speak...{RESET}\n")

    while True:
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{DIM}  Goodbye.{RESET}")
            break

        print(f"{RED}  🔴 Recording… Press Enter to stop{RESET}", flush=True)
        pcm = _record_blocking()

        print(f"{DIM}  ⏳ Transcribing audio (Faster-Whisper)...{RESET}", flush=True)
        wav = _pcm_to_wav(pcm)
        user_text = await whisper.transcribe(wav)

        if not user_text:
            print(f"{DIM}  (no speech detected){RESET}\n")
            continue

        print(f"\n{YELLOW}  🗣 You:{RESET} {user_text}")

        print(f"{BLUE}  🧠 Agent thinking...{RESET}", flush=True)
        reply_text, action_type = await router.process_user_input(user_text)

        print(f"{PURPLE}  [{action_type}] Agent:{RESET} {reply_text}")

        print(f"{GREEN}  🔊 Synthesizing speech ({settings.TTS_PROVIDER})...{RESET}", flush=True)
        audio_bytes = await tts_factory.synthesize_speech(reply_text)
        
        print(f"{GREEN}  🔊 Playing speech...{RESET}", flush=True)
        await playback.player.play_audio(audio_bytes)

        print(f"\n{DIM}  ⏎ Press Enter to speak...{RESET}\n")

if __name__ == "__main__":
    asyncio.run(main())
