import os
import logging
from .synthesizer_interface import Synthesizer

logger = logging.getLogger(__name__)

class SynthesizerFactory:
    """
    Factory for creating the appropriate Synthesizer implementation 
    based on configuration.
    """
    
    @staticmethod
    def create() -> Synthesizer:
        model_name = os.getenv("TTS_MODEL_NAME", "kokoro-82m-onnx")
        logger.info(f"Initializing TTS Synthesizer backend: {model_name}")
        
        if model_name.lower() in ["kokoro-82m-onnx", "kokoro"]:
            from .synthesizer_kokoro import KokoroSynthesizer
            return KokoroSynthesizer()
            
        # Extension point for future models:
        # if model_name == "indextts": ...
        
        raise ValueError(f"Unknown TTS_MODEL_NAME: {model_name}. Supported: kokoro-82m-onnx")
