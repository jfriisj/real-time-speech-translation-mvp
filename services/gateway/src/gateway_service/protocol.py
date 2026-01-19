from __future__ import annotations

import json
from typing import Any, Dict


def build_handshake_message(correlation_id: str) -> str:
    return json.dumps({"status": "connected", "correlation_id": correlation_id})


def parse_sentinel_message(message: str) -> bool:
    try:
        payload: Dict[str, Any] = json.loads(message)
    except json.JSONDecodeError:
        return False
    if not isinstance(payload, dict):
        return False
    return payload.get("event") == "done"
