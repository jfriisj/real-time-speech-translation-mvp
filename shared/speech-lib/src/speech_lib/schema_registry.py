from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict

import requests


@dataclass
class SchemaRegistryClient:
    base_url: str

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    def register_schema(self, subject: str, schema: Dict[str, Any]) -> int:
        payload = {"schema": json.dumps(schema)}
        response = requests.post(self._url(f"subjects/{subject}/versions"), json=payload)
        response.raise_for_status()
        return int(response.json()["id"])

    def get_latest_schema(self, subject: str) -> Dict[str, Any]:
        response = requests.get(self._url(f"subjects/{subject}/versions/latest"))
        response.raise_for_status()
        return response.json()

    def get_schema_by_id(self, schema_id: int) -> Dict[str, Any]:
        response = requests.get(self._url(f"schemas/ids/{schema_id}"))
        response.raise_for_status()
        data = response.json()
        return json.loads(data["schema"])
