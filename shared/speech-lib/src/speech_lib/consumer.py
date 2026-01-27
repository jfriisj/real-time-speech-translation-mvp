from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping

from .serialization import deserialize_event
from .schema_registry import SchemaRegistryClient


@dataclass
class KafkaConsumerWrapper:
    consumer: Any
    schema_registry: SchemaRegistryClient | None = None

    @classmethod
    def from_confluent(
        cls,
        bootstrap_servers: str,
        group_id: str,
        topics: Iterable[str],
        config: Mapping[str, Any] | None = None,
        schema_registry: SchemaRegistryClient | None = None,
    ) -> "KafkaConsumerWrapper":
        try:
            from confluent_kafka import Consumer  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "confluent-kafka is required to create a consumer. "
                "Install it or pass an existing consumer instance."
            ) from exc

        consumer_config: Dict[str, Any] = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
        }
        if config:
            consumer_config.update(dict(config))

        consumer = Consumer(consumer_config)
        consumer.subscribe(list(topics))
        return cls(consumer=consumer, schema_registry=schema_registry)

    def poll(self, schema: Dict[str, Any], timeout: float = 1.0) -> Dict[str, Any] | None:
        message = self.consumer.poll(timeout=timeout)
        if message is None or message.error():
            return None
        return deserialize_event(schema, message.value(), schema_registry=self.schema_registry)

    def poll_with_message(
        self, schema: Dict[str, Any], timeout: float = 1.0
    ) -> tuple[Dict[str, Any], Any] | None:
        message = self.consumer.poll(timeout=timeout)
        if message is None or message.error():
            return None
        return (
            deserialize_event(schema, message.value(), schema_registry=self.schema_registry),
            message,
        )

    def commit_message(self, message: Any) -> None:
        self.consumer.commit(message=message, asynchronous=False)
