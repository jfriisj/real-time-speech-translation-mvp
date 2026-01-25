from pathlib import Path

TOPIC_AUDIO_INGRESS = "speech.audio.ingress"
TOPIC_SPEECH_SEGMENT = "speech.audio.speech_segment"
TOPIC_ASR_TEXT = "speech.asr.text"
TOPIC_TRANSLATION_TEXT = "speech.translation.text"
TOPIC_TTS_OUTPUT = "speech.tts.audio"

KAFKA_MESSAGE_MAX_BYTES = 2 * 1024 * 1024
AUDIO_PAYLOAD_MAX_BYTES = int(1.5 * 1024 * 1024)

DEFAULT_SCHEMA_DIR = Path("shared/schemas/avro")
