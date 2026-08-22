import io
import time
import asyncio
import logging
import threading
import numpy as np
import sounddevice as sd
from pydub import AudioSegment

logger = logging.getLogger(__name__)

CURRENT_STATUS = "IDLE"

class AudioPlayer:
    def __init__(self):
        self._is_playing = False
        self._stop_requested = False
        self._current_stream = None

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def stop(self):
        """Immediately stop current playback."""
        self._stop_requested = True
        if self._current_stream:
            try:
                self._current_stream.stop()
                self._current_stream.close()
            except Exception:
                pass
            self._current_stream = None
        self._is_playing = False
        set_status("IDLE")

    async def play_audio_file(self, file_path: str):
        """Asynchronously play WAV file through speakers."""
        try:
            with open(file_path, "rb") as f:
                b = f.read()
            await self.play_audio(b, format="wav")
        except Exception as e:
            logger.error(f"Error reading audio file '{file_path}': {e}")

    async def play_audio(self, audio_bytes: bytes, format: str = "wav"):
        """Asynchronously play audio bytes through speakers with interrupt check."""
        if not audio_bytes:
            return

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._play_sync, audio_bytes, format)

    def _play_sync(self, audio_bytes: bytes, format: str):
        self._stop_requested = False
        self._is_playing = True
        set_status("SPEAKING")

        try:
            try:
                seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format=format)
            except Exception:
                seg = AudioSegment.from_file(io.BytesIO(audio_bytes))

            seg = seg.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            arr = np.frombuffer(seg.raw_data, dtype=np.int16)

            chunk_size = 1600
            for i in range(0, len(arr), chunk_size):
                if self._stop_requested:
                    logger.info("Playback interrupted by user barge-in.")
                    break
                chunk = arr[i:i + chunk_size]
                sd.play(chunk, samplerate=16000)
                sd.wait()

        except Exception as e:
            logger.error(f"Playback error: {e}")
        finally:
            self._is_playing = False
            set_status("IDLE")

player = AudioPlayer()

def get_current_status() -> str:
    return CURRENT_STATUS

def set_status(status: str):
    global CURRENT_STATUS
    CURRENT_STATUS = status

def is_playing() -> bool:
    return player.is_playing

def stop_audio():
    player.stop()

async def play_audio(file_path: str):
    await player.play_audio_file(file_path)
