from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any, Dict

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


def deserialize_event(schema: Dict[str, Any], raw_bytes: bytes) -> Dict[str, Any]:
    buffer = BytesIO(raw_bytes)
    return schemaless_reader(buffer, schema)
