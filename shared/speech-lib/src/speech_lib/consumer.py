from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable

from .serialization import deserialize_event


@dataclass
class KafkaConsumerWrapper:
    consumer: Any

    @classmethod
    def from_confluent(
        cls, bootstrap_servers: str, group_id: str, topics: Iterable[str]
    ) -> "KafkaConsumerWrapper":
        try:
            from confluent_kafka import Consumer  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "confluent-kafka is required to create a consumer. "
                "Install it or pass an existing consumer instance."
            ) from exc

        consumer = Consumer(
            {
                "bootstrap.servers": bootstrap_servers,
                "group.id": group_id,
                "auto.offset.reset": "earliest",
            }
        )
        consumer.subscribe(list(topics))
        return cls(consumer=consumer)

    def poll(self, schema: Dict[str, Any], timeout: float = 1.0) -> Dict[str, Any] | None:
        message = self.consumer.poll(timeout=timeout)
        if message is None or message.error():
            return None
        return deserialize_event(schema, message.value())
