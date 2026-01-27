from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any, Dict

from .schema_registry import SchemaRegistryClient

from fastavro import parse_schema, schemaless_reader, schemaless_writer

from .constants import DEFAULT_SCHEMA_DIR


def load_schema(schema_name: str, schema_dir: Path | None = None) -> Dict[str, Any]:
    schema_path = (schema_dir or DEFAULT_SCHEMA_DIR) / schema_name
    with schema_path.open("r", encoding="utf-8") as handle:
        return parse_schema(__import__("json").load(handle))


def serialize_event(schema: Dict[str, Any], payload: Dict[str, Any]) -> bytes:
    buffer = BytesIO()
    schemaless_writer(buffer, schema, payload)
    return buffer.getvalue()


def serialize_event_with_schema_id(
    schema: Dict[str, Any], payload: Dict[str, Any], schema_id: int
) -> bytes:
    buffer = BytesIO()
    schemaless_writer(buffer, schema, payload)
    payload_bytes = buffer.getvalue()
    return b"\x00" + int(schema_id).to_bytes(4, "big") + payload_bytes


def deserialize_event(
    schema: Dict[str, Any],
    raw_bytes: bytes,
    schema_registry: SchemaRegistryClient | None = None,
) -> Dict[str, Any]:
    if raw_bytes and raw_bytes[0] == 0 and schema_registry is not None:
        if len(raw_bytes) < 5:
            raise ValueError("Invalid Avro payload: missing schema id")
        schema_id = int.from_bytes(raw_bytes[1:5], "big")
        writer_schema = schema_registry.get_schema_by_id(schema_id)
        buffer = BytesIO(raw_bytes[5:])
        return schemaless_reader(buffer, writer_schema, reader_schema=schema)

    buffer = BytesIO(raw_bytes)
    return schemaless_reader(buffer, schema)
