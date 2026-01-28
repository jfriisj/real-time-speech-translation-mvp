from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClaimCheckDecision:
    mode: str
    payload_size_bytes: int
    threshold_bytes: int


def select_transport_mode(
    *,
    payload_size_bytes: int,
    threshold_bytes: int,
    force_uri: bool = False,
) -> ClaimCheckDecision:
    if payload_size_bytes < 0:
        raise ValueError("payload_size_bytes must be non-negative")
    if threshold_bytes <= 0:
        raise ValueError("threshold_bytes must be positive")
    if force_uri or payload_size_bytes > threshold_bytes:
        return ClaimCheckDecision(
            mode="uri",
            payload_size_bytes=payload_size_bytes,
            threshold_bytes=threshold_bytes,
        )
    return ClaimCheckDecision(
        mode="inline",
        payload_size_bytes=payload_size_bytes,
        threshold_bytes=threshold_bytes,
    )
