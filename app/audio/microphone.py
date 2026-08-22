import io
import wave
import logging
import threading
import sounddevice as sd
import numpy as np

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"

class MicrophoneRecorder:
    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.is_recording = False
        self._frames = []
        self._stream = None

    def start(self):
        """Start non-blocking recording."""
        self._frames = []
        self.is_recording = True

        def callback(indata, frame_count, time_info, status):
            if self.is_recording:
                self._frames.append(bytes(indata))

        self._stream = sd.RawInputStream(
            samplerate=self.sample_rate,
            channels=CHANNELS,
            dtype=DTYPE,
            callback=callback,
        )
        self._stream.start()

    def stop(self) -> bytes:
        """Stop recording and return WAV bytes."""
        self.is_recording = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                logger.warning(f"Error closing mic stream: {e}")
            self._stream = None

        pcm_data = b"".join(self._frames)
        self._frames = []
        return pcm_to_wav(pcm_data, self.sample_rate)

def pcm_to_wav(pcm_bytes: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Wrap raw PCM int16 bytes in a WAV header."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # int16 = 2 bytes
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()
