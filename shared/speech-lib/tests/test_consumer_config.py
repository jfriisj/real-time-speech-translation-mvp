from __future__ import annotations

from speech_lib.consumer_config import (
    ConsumerTuning,
    build_consumer_config,
    validate_consumer_tuning,
)


def test_build_consumer_config_applies_defaults() -> None:
    tuning = ConsumerTuning(
        session_timeout_ms=15000,
        heartbeat_interval_ms=5000,
        max_poll_interval_ms=300000,
        partition_assignment_strategy=None,
        enable_static_membership=False,
        group_instance_id=None,
    )

    config = build_consumer_config(tuning)

    assert config["session.timeout.ms"] == 15000
    assert config["heartbeat.interval.ms"] == 5000
    assert config["max.poll.interval.ms"] == 300000
    assert "partition.assignment.strategy" not in config
    assert "group.instance.id" not in config


def test_build_consumer_config_supports_static_membership() -> None:
    tuning = ConsumerTuning(
        session_timeout_ms=20000,
        heartbeat_interval_ms=5000,
        max_poll_interval_ms=300000,
        partition_assignment_strategy="cooperative-sticky",
        enable_static_membership=True,
        group_instance_id="tts-service-1",
    )

    config = build_consumer_config(tuning)

    assert config["partition.assignment.strategy"] == "cooperative-sticky"
    assert config["group.instance.id"] == "tts-service-1"


def test_validate_consumer_tuning_rejects_invalid_bounds() -> None:
    tuning = ConsumerTuning(
        session_timeout_ms=5000,
        heartbeat_interval_ms=5000,
        max_poll_interval_ms=1000,
        partition_assignment_strategy="range",
        enable_static_membership=False,
        group_instance_id=None,
    )

    errors = validate_consumer_tuning(tuning)

    assert any("session" in error for error in errors)
    assert any("max.poll" in error for error in errors)


def test_validate_consumer_tuning_requires_group_instance_when_enabled() -> None:
    tuning = ConsumerTuning(
        session_timeout_ms=15000,
        heartbeat_interval_ms=5000,
        max_poll_interval_ms=300000,
        partition_assignment_strategy=None,
        enable_static_membership=True,
        group_instance_id=None,
    )

    errors = validate_consumer_tuning(tuning)

    assert any("group.instance.id" in error for error in errors)