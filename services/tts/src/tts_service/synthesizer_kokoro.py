import os
import io
import json
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Iterable

import numpy as np
import soundfile as sf
from huggingface_hub import hf_hub_download

try:  # pragma: no cover - environment dependent
    import onnxruntime as ort
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    class _MissingOnnxRuntime:
        def __getattr__(self, _name: str):
            raise ModuleNotFoundError(
                "onnxruntime is required for KokoroSynthesizer; install it in the runtime environment"
            )

    ort = _MissingOnnxRuntime()

try:  # pragma: no cover - environment dependent
    from misaki import en
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    en = None
from .synthesizer_interface import Synthesizer

logger = logging.getLogger(__name__)

REPO_ID = "onnx-community/Kokoro-82M-v1.0-ONNX"
MODEL_FILENAME = "onnx/model.onnx"
VOICES_FILENAME = "voices/af_bella.bin"
TOKENIZER_FILENAME = "tokenizer.json"

class KokoroSynthesizer(Synthesizer):
    def __init__(self):
        self.model_cache = os.getenv("TTS_MODEL_CACHE_DIR") or os.getenv(
            "MODEL_CACHE_DIR", "/app/model_cache"
        )
        os.makedirs(self.model_cache, exist_ok=True)
        
        # 1. Ensure Model and Assets
        self.model_path = self._download_asset(MODEL_FILENAME)
        self.voices_path = self._download_asset(VOICES_FILENAME)
        self.tokenizer_path = self._download_asset(TOKENIZER_FILENAME)
        
        # 2. Init Inference Session
        providers_env = (
            os.getenv("ONNX_PROVIDER")
            or os.getenv("ONNX_PROVIDERS")
            or "CPUExecutionProvider"
        )
        providers = [p.strip() for p in providers_env.split(",") if p.strip()]
        logger.info(f"Loading Kokoro ONNX from {self.model_path} with providers={providers}")
        self.session = ort.InferenceSession(self.model_path, providers=providers)
        
        # 3. Init Text Processor (Misaki G2P)
        # Fallback to simple English G2P with signature-compatible initialization.
        self.g2p = self._init_g2p()
        
        # 4. Load Voice Styles
        self.voices = self._load_voices(self.voices_path)
        self.default_voice_key = self._default_voice_key(self.voices_path)
        logger.info(
            "Loaded %s voice profiles (default=%s)",
            len(self.voices),
            self.default_voice_key,
        )

        # 5. Load Vocab
        self.vocab = self._load_vocab(self.tokenizer_path)

    def _download_asset(self, filename: str) -> str:
        try:
            return hf_hub_download(
                repo_id=REPO_ID,
                filename=filename,
                cache_dir=self.model_cache
            )
        except Exception as e:
            logger.error(f"Failed to download {filename} from {REPO_ID}: {e}")
            raise

    def _default_voice_key(self, path: str) -> str:
        return Path(path).stem or "af_bella"

    def _load_voices(self, path: str) -> Dict[str, np.ndarray]:
        voice_name = self._default_voice_key(path)
        fallback = {voice_name: np.zeros((1, 256), dtype=np.float32)}
        if not os.path.exists(path):
            logger.warning("Kokoro voice asset not found at %s; using fallback voice", path)
            return fallback

        try:
            voice_vectors = np.fromfile(path, dtype=np.float32)
            if voice_vectors.size == 0:
                raise ValueError("voice asset was empty")
            if voice_vectors.size % 256 != 0:
                raise ValueError("voice asset size is not divisible by 256")

            voice_vectors = voice_vectors.reshape(-1, 256)
            voices: Dict[str, np.ndarray] = {}
            for idx, vector in enumerate(voice_vectors):
                key = f"{voice_name}-{idx}"
                voices[key] = vector.reshape(1, 256)

            voices[voice_name] = voice_vectors[0:1]
            return voices
        except Exception as exc:
            logger.warning("Failed to load voice asset %s: %s", path, exc)
            return fallback

    def _init_g2p(self) -> en.G2P:
        if en is None:
            raise ModuleNotFoundError(
                "misaki is required for KokoroSynthesizer; install it in the runtime environment"
            )
        try:
            return en.G2P(trf=False, british=False, fallback=None)
        except TypeError:
            try:
                return en.G2P(trf=False)
            except TypeError:
                return en.G2P()

    def _load_vocab(self, path: str) -> Dict[str, int]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # The structure is usually data["model"]["vocab"] for HF tokenizers
            return data["model"]["vocab"]
        except Exception as e:
            logger.error(f"Failed to load vocab from {path}: {e}")
            return {}

    def _split_phonemes(self, phonemes: str | Iterable[str]) -> list[str]:
        if isinstance(phonemes, str):
            normalized = phonemes.strip()
            if not normalized:
                return []
            parts = normalized.split()
            if len(parts) == 1:
                return list(normalized)
            return parts
        return [str(token).strip() for token in phonemes if str(token).strip()]

    def _phonemes_to_ids(self, phonemes: str | Iterable[str]) -> list[int]:
        tokens = self._split_phonemes(phonemes)
        return [self.vocab.get(token, 0) for token in tokens]

    def _resolve_speed(self) -> float:
        raw = (os.getenv("TTS_SPEED") or "1.0").strip()
        try:
            speed = float(raw)
        except ValueError:
            logger.warning("Invalid TTS_SPEED=%s; falling back to 1.0", raw)
            return 1.0
        if speed <= 0:
            logger.warning("TTS_SPEED must be > 0; falling back to 1.0")
            return 1.0
        return speed

    def _resolve_voice_key(self, speaker_id: Optional[str]) -> str:
        if speaker_id:
            candidate = speaker_id.strip()
            if candidate in self.voices:
                return candidate
            if candidate.isdigit():
                indexed = f"{self.default_voice_key}-{candidate}"
                if indexed in self.voices:
                    return indexed
            logger.warning(
                "Unknown speaker_id=%s; falling back to default voice=%s",
                candidate,
                self.default_voice_key,
            )
        return self.default_voice_key

    def synthesize(
        self, 
        text: str, 
        speaker_reference_bytes: Optional[bytes] = None, 
        speaker_id: Optional[str] = None
    ) -> Tuple[bytes, int, int]:
        _ = speaker_reference_bytes
        
        # 1. Text Processing
        try:
            result = self.g2p(text)
            if isinstance(result, tuple):
                # misaki returns (phonemes, list_of_MToken) where MTokens are objects.
                # We need the direct phoneme string to map to IDs.
                phonemes = result[0]
            else:
                phonemes = result
                
            tokens = self._phonemes_to_ids(phonemes)
        except Exception as e:
            logger.error(f"G2P Failed for text '{text}': {e}")
            raise e

        # Pad with 0 ($)
        tokens = [0] + tokens + [0]
        
        input_ids = np.array([tokens], dtype=np.int64)
        
        # 2. Style Selection
        selected_voice = self._resolve_voice_key(speaker_id)
        style = self.voices.get(selected_voice)
        if style is None:
            style = next(iter(self.voices.values()))

        # 3. Inference
        speed = np.array([self._resolve_speed()], dtype=np.float32)
        
        try:
            audio = self.session.run(None, {
                "input_ids": input_ids, 
                "style": style, 
                "speed": speed
            })[0]
        except Exception as e:
            logger.error(f"ONNX Inference Failed: {e}")
            raise

        # 4. Audio Formatting
        # Ensure audio is 1D for mono WAV writing
        if audio.ndim > 1:
            audio = np.squeeze(audio)

        sample_rate = 24000
        sample_count = int(audio.shape[0]) if audio.ndim > 0 else 0
        duration_ms = int(sample_count / sample_rate * 1000)
        
        # Convert to WAV bytes (PCM_16)
        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format='WAV', subtype='PCM_16')
        buffer.seek(0)
        audio_bytes = buffer.read()
        
        # Return audio bytes, sample rate, and duration (ms)
        return audio_bytes, sample_rate, duration_ms
