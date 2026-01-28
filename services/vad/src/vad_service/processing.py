from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import logging
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
import soundfile as sf
import librosa

from speech_lib.constants import AUDIO_PAYLOAD_MAX_BYTES
from speech_lib.storage import ObjectStorage


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SpeechSegment:
    start_ms: int
    end_ms: int
    audio_bytes: bytes


def validate_audio_payload(
    payload: Dict[str, Any],
    storage: ObjectStorage | None,
) -> tuple[bytes, int, str]:
    audio_bytes = payload.get("audio_bytes")
    audio_uri = payload.get("audio_uri")
    audio_format = payload.get("audio_format")
    sample_rate_hz = payload.get("sample_rate_hz")

    has_bytes = isinstance(audio_bytes, (bytes, bytearray)) and bool(audio_bytes)
    has_uri = isinstance(audio_uri, str) and bool(str(audio_uri).strip())
    if has_bytes == has_uri:
        raise ValueError("exactly one of audio_bytes or audio_uri must be set")
    if has_uri:
        if storage is None:
            raise ValueError("audio_uri provided but storage unavailable")
        audio_bytes = storage.download_bytes(uri=str(audio_uri))
    if not isinstance(audio_bytes, (bytes, bytearray)) or not audio_bytes:
        raise ValueError("audio_bytes missing or empty")

    if not has_uri and len(audio_bytes) > AUDIO_PAYLOAD_MAX_BYTES:
        raise ValueError(f"audio_bytes exceeds {AUDIO_PAYLOAD_MAX_BYTES} bytes (MVP limit)")

    if audio_format != "wav":
        raise ValueError(f"audio_format must be 'wav' for MVP (got {audio_format!r})")

    if not isinstance(sample_rate_hz, int) or sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz missing or invalid")

    return bytes(audio_bytes), sample_rate_hz, audio_format


def decode_wav(audio_bytes: bytes, sample_rate_hz: int) -> tuple[np.ndarray, int]:
    data, actual_rate = sf.read(BytesIO(audio_bytes), dtype="float32")
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    if actual_rate != sample_rate_hz:
        LOGGER.warning(
            "Sample rate metadata mismatch (payload=%s, wav=%s). Using wav rate.",
            sample_rate_hz,
            actual_rate,
        )

    return data, actual_rate


def resample_audio(audio: np.ndarray, sample_rate: int, target_rate: int) -> tuple[np.ndarray, int]:
    if sample_rate == target_rate:
        return audio, sample_rate

    resampled = librosa.resample(audio, orig_sr=sample_rate, target_sr=target_rate)
    return resampled, target_rate


def encode_wav(audio: np.ndarray, sample_rate: int) -> bytes:
    buffer = BytesIO()
    sf.write(buffer, audio, sample_rate, format="WAV")
    return buffer.getvalue()


def _frame_audio(audio: np.ndarray, frame_length: int, hop_length: int) -> Iterable[np.ndarray]:
    for start in range(0, len(audio), hop_length):
        frame = audio[start : start + frame_length]
        if len(frame) < frame_length:
            frame = np.pad(frame, (0, frame_length - len(frame)))
        yield frame


def _energy_probabilities(audio: np.ndarray, frame_length: int, hop_length: int) -> np.ndarray:
    probs: List[float] = []
    for frame in _frame_audio(audio, frame_length, hop_length):
        rms = float(np.sqrt(np.mean(frame ** 2)))
        probs.append(rms)
    return np.asarray(probs, dtype=np.float32)


def _segments_from_probs(
    probabilities: np.ndarray,
    *,
    hop_ms: int,
    window_ms: int,
    threshold: float,
    min_speech_ms: int,
    min_silence_ms: int,
    padding_ms: int,
    total_ms: int,
) -> List[tuple[int, int]]:
    segments: List[tuple[int, int]] = []
    in_speech = False
    speech_start_index = 0
    silence_start_index: Optional[int] = None

    for idx, prob in enumerate(probabilities):
        if prob >= threshold:
            if not in_speech:
                in_speech = True
                speech_start_index = idx
            silence_start_index = None
            continue

        if in_speech:
            if silence_start_index is None:
                silence_start_index = idx
            silence_duration = (idx - silence_start_index + 1) * hop_ms
            if silence_duration >= min_silence_ms:
                end_index = silence_start_index
                start_ms = speech_start_index * hop_ms
                end_ms = end_index * hop_ms + window_ms
                segments.append((start_ms, end_ms))
                in_speech = False
                silence_start_index = None

    if in_speech:
        end_index = len(probabilities) - 1
        start_ms = speech_start_index * hop_ms
        end_ms = end_index * hop_ms + window_ms
        segments.append((start_ms, end_ms))

    padded_segments: List[tuple[int, int]] = []
    for start_ms, end_ms in segments:
        padded_start = max(0, start_ms - padding_ms)
        padded_end = min(total_ms, end_ms + padding_ms)
        if padded_end - padded_start >= min_speech_ms:
            padded_segments.append((padded_start, padded_end))

    return padded_segments


def segment_audio(
    *,
    audio: np.ndarray,
    sample_rate_hz: int,
    window_ms: int,
    hop_ms: int,
    speech_threshold: float,
    energy_threshold: float,
    min_speech_ms: int,
    min_silence_ms: int,
    padding_ms: int,
    speech_probabilities: Optional[np.ndarray] = None,
) -> List[tuple[int, int]]:
    frame_length = max(1, int(sample_rate_hz * window_ms / 1000))
    hop_length = max(1, int(sample_rate_hz * hop_ms / 1000))

    probabilities = speech_probabilities
    threshold = speech_threshold
    if probabilities is None:
        probabilities = _energy_probabilities(audio, frame_length, hop_length)
        threshold = energy_threshold

    total_ms = int(len(audio) / sample_rate_hz * 1000)
    return _segments_from_probs(
        probabilities,
        hop_ms=hop_ms,
        window_ms=window_ms,
        threshold=threshold,
        min_speech_ms=min_speech_ms,
        min_silence_ms=min_silence_ms,
        padding_ms=padding_ms,
        total_ms=total_ms,
    )


def build_segments(
    *,
    audio: np.ndarray,
    sample_rate_hz: int,
    window_ms: int,
    hop_ms: int,
    speech_threshold: float,
    energy_threshold: float,
    min_speech_ms: int,
    min_silence_ms: int,
    padding_ms: int,
    speech_probabilities: Optional[np.ndarray] = None,
) -> List[SpeechSegment]:
    ranges = segment_audio(
        audio=audio,
        sample_rate_hz=sample_rate_hz,
        window_ms=window_ms,
        hop_ms=hop_ms,
        speech_threshold=speech_threshold,
        energy_threshold=energy_threshold,
        min_speech_ms=min_speech_ms,
        min_silence_ms=min_silence_ms,
        padding_ms=padding_ms,
        speech_probabilities=speech_probabilities,
    )

    segments: List[SpeechSegment] = []
    for start_ms, end_ms in ranges:
        start_sample = int(start_ms * sample_rate_hz / 1000)
        end_sample = int(end_ms * sample_rate_hz / 1000)
        segment_samples = audio[start_sample:end_sample]
        if segment_samples.size == 0:
            continue
        segments.append(
            SpeechSegment(
                start_ms=start_ms,
                end_ms=end_ms,
                audio_bytes=encode_wav(segment_samples, sample_rate_hz),
            )
        )

    return segments
