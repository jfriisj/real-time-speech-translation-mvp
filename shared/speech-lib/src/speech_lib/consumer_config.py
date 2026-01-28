from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


ALLOWED_ASSIGNMENT_STRATEGIES = {
    "range",
    "roundrobin",
    "cooperative-sticky",
    "sticky",
}


@dataclass(frozen=True)
class ConsumerTuning:
    session_timeout_ms: int
    heartbeat_interval_ms: int
    max_poll_interval_ms: int
    partition_assignment_strategy: str | None
    enable_static_membership: bool
    group_instance_id: str | None


def build_consumer_config(tuning: ConsumerTuning) -> Dict[str, Any]:
    config: Dict[str, Any] = {
        "session.timeout.ms": tuning.session_timeout_ms,
        "heartbeat.interval.ms": tuning.heartbeat_interval_ms,
        "max.poll.interval.ms": tuning.max_poll_interval_ms,
    }
    if tuning.partition_assignment_strategy:
        config["partition.assignment.strategy"] = tuning.partition_assignment_strategy
    if tuning.enable_static_membership and tuning.group_instance_id:
        config["group.instance.id"] = tuning.group_instance_id
    return config


def validate_consumer_tuning(tuning: ConsumerTuning) -> List[str]:
    errors: List[str] = []
    if tuning.session_timeout_ms <= 0:
        errors.append("session.timeout.ms must be positive")
    if tuning.heartbeat_interval_ms <= 0:
        errors.append("heartbeat.interval.ms must be positive")
    if tuning.max_poll_interval_ms <= 0:
        errors.append("max.poll.interval.ms must be positive")

    if tuning.session_timeout_ms <= tuning.heartbeat_interval_ms:
        errors.append(
            "session.timeout.ms must be greater than heartbeat.interval.ms"
        )
    if tuning.session_timeout_ms < tuning.heartbeat_interval_ms * 2:
        errors.append(
            "session.timeout.ms must allow multiple heartbeats within the session window"
        )
    if tuning.max_poll_interval_ms <= tuning.session_timeout_ms:
        errors.append("max.poll.interval.ms must exceed session.timeout.ms")

    if tuning.partition_assignment_strategy:
        if tuning.partition_assignment_strategy not in ALLOWED_ASSIGNMENT_STRATEGIES:
            errors.append(
                "partition.assignment.strategy must be one of: "
                + ", ".join(sorted(ALLOWED_ASSIGNMENT_STRATEGIES))
            )

    if tuning.enable_static_membership and not tuning.group_instance_id:
        errors.append("group.instance.id is required when static membership is enabled")
    if not tuning.enable_static_membership and tuning.group_instance_id:
        errors.append("group.instance.id provided but static membership is disabled")

    return errors