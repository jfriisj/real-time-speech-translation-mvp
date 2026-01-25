from abc import ABC, abstractmethod
from typing import Optional, Tuple

class Synthesizer(ABC):
    @abstractmethod
    def synthesize(
        self, 
        text: str, 
        speaker_reference_bytes: Optional[bytes] = None, 
        speaker_id: Optional[str] = None
    ) -> Tuple[bytes, int, int]:
        """
        Synthesize text to audio.
        
        Args:
            text: The text to synthesize.
            speaker_reference_bytes: Optional raw audio bytes for voice cloning context.
            speaker_id: Optional speaker identifier for style selection.
            
        Returns:
            Tuple containing:
            - audio_bytes: The generated WAV audio bytes.
            - sample_rate_hz: The sample rate of the audio (e.g. 24000).
            - duration_ms: The duration of the audio in milliseconds.
        """
        pass
