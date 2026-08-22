import numpy as np
import logging

logger = logging.getLogger(__name__)

class EnergyVAD:
    """RMS Energy-based Voice Activity Detection."""
    def __init__(self, threshold: float = 400.0, silence_duration_sec: float = 1.2, sample_rate: int = 16000):
        self.threshold = threshold
        self.silence_duration_sec = silence_duration_sec
        self.sample_rate = sample_rate

    def calculate_rms(self, pcm_chunk: bytes) -> float:
        """Calculate Root Mean Square energy of 16-bit PCM chunk."""
        if not pcm_chunk:
            return 0.0
        audio_data = np.frombuffer(pcm_chunk, dtype=np.int16)
        if len(audio_data) == 0:
            return 0.0
        return float(np.sqrt(np.mean(audio_data.astype(np.float32) ** 2)))

    def is_speech(self, pcm_chunk: bytes) -> bool:
        rms = self.calculate_rms(pcm_chunk)
        return rms > self.threshold
