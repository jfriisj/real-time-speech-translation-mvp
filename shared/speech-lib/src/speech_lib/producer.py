from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .constants import AUDIO_PAYLOAD_MAX_BYTES, KAFKA_MESSAGE_MAX_BYTES
from .events import BaseEvent
from .serialization import serialize_event, serialize_event_with_schema_id


@dataclass
class KafkaProducerWrapper:
    producer: Any

    @classmethod
    def from_confluent(cls, bootstrap_servers: str) -> "KafkaProducerWrapper":
        try:
            from confluent_kafka import Producer  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "confluent-kafka is required to create a producer. "
                "Install it or pass an existing producer instance."
            ) from exc

        producer = Producer({"bootstrap.servers": bootstrap_servers})
        return cls(producer=producer)

    def publish_event(
        self,
        topic: str,
        event: BaseEvent,
        schema: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        schema_id: Optional[int] = None,
    ) -> None:
        payload = event.to_dict()
        audio_bytes = payload.get("payload", {}).get("audio_bytes")
        if isinstance(audio_bytes, (bytes, bytearray)) and len(audio_bytes) > AUDIO_PAYLOAD_MAX_BYTES:
            raise ValueError(
                f"audio_bytes exceeds {AUDIO_PAYLOAD_MAX_BYTES} bytes (MVP limit)"
            )
        if schema_id is None:
            raw = serialize_event(schema, payload)
        else:
            raw = serialize_event_with_schema_id(schema, payload, schema_id)
        if len(raw) > KAFKA_MESSAGE_MAX_BYTES:
            raise ValueError(
                f"Serialized event exceeds {KAFKA_MESSAGE_MAX_BYTES} bytes (MVP limit)"
            )
        formatted_headers = None
        if headers:
            formatted_headers = [(k, v) for k, v in headers.items()]
        self.producer.produce(topic, value=raw, key=key, headers=formatted_headers)
        self.producer.flush()
