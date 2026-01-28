from __future__ import annotations

import logging
import random
import socket
import time
from typing import Protocol, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


LOGGER = logging.getLogger(__name__)


class StartupSettings(Protocol):
    kafka_bootstrap_servers: str
    schema_registry_url: str
    startup_max_wait_seconds: float
    startup_initial_backoff_seconds: float
    startup_max_backoff_seconds: float
    startup_attempt_timeout_seconds: float


def _sanitize_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or url
    port = parsed.port
    if port is None:
        if parsed.scheme == "https":
            port = 443
        elif parsed.scheme == "http":
            port = 80
    return f"{host}:{port}" if port else host


def _parse_kafka_bootstrap(bootstrap_servers: str) -> Tuple[str, int]:
    candidate = bootstrap_servers.split(",", maxsplit=1)[0].strip()
    if "://" in candidate:
        parsed = urlparse(candidate)
        host = parsed.hostname or "localhost"
        port = parsed.port or 9092
        return host, port
    if ":" in candidate:
        host, port_raw = candidate.split(":", maxsplit=1)
        try:
            port = int(port_raw)
        except ValueError:
            port = 9092
        return host, port
    return candidate or "localhost", 9092


def _sleep_with_jitter(delay_seconds: float) -> None:
    jitter = random.uniform(0.0, min(0.5, delay_seconds * 0.1))
    time.sleep(delay_seconds + jitter)


def _next_backoff(
    *,
    attempt: int,
    initial_backoff_seconds: float,
    max_backoff_seconds: float,
) -> float:
    return min(initial_backoff_seconds * (2 ** (attempt - 1)), max_backoff_seconds)


def wait_for_kafka(
    *,
    host: str,
    port: int,
    max_wait_seconds: float,
    initial_backoff_seconds: float,
    max_backoff_seconds: float,
    attempt_timeout_seconds: float,
) -> None:
    deadline = time.monotonic() + max_wait_seconds
    attempt = 0
    while True:
        attempt += 1
        try:
            with socket.create_connection((host, port), timeout=attempt_timeout_seconds):
                LOGGER.info("Kafka ready at %s:%s", host, port)
                return
        except OSError as exc:
            if time.monotonic() >= deadline:
                LOGGER.error(
                    "Kafka not ready after %.0fs at %s:%s",
                    max_wait_seconds,
                    host,
                    port,
                )
                raise SystemExit(1) from exc
            delay = _next_backoff(
                attempt=attempt,
                initial_backoff_seconds=initial_backoff_seconds,
                max_backoff_seconds=max_backoff_seconds,
            )
            LOGGER.info(
                "Waiting for Kafka at %s:%s (retry in %.1fs)", host, port, delay
            )
            _sleep_with_jitter(delay)


def wait_for_schema_registry(
    *,
    registry_url: str,
    max_wait_seconds: float,
    initial_backoff_seconds: float,
    max_backoff_seconds: float,
    attempt_timeout_seconds: float,
) -> None:
    deadline = time.monotonic() + max_wait_seconds
    attempt = 0
    safe_target = _sanitize_url(registry_url)
    while True:
        attempt += 1
        try:
            request = Request(f"{registry_url.rstrip('/')}/subjects", method="GET")
            with urlopen(request, timeout=attempt_timeout_seconds) as response:
                if response.status >= 400:
                    raise HTTPError(
                        request.full_url,
                        response.status,
                        "Schema Registry error",
                        response.headers,
                        None,
                    )
            LOGGER.info("Schema Registry ready at %s", safe_target)
            return
        except (URLError, HTTPError, OSError) as exc:
            if time.monotonic() >= deadline:
                LOGGER.error(
                    "Schema Registry not ready after %.0fs at %s",
                    max_wait_seconds,
                    safe_target,
                )
                raise SystemExit(1) from exc
            delay = _next_backoff(
                attempt=attempt,
                initial_backoff_seconds=initial_backoff_seconds,
                max_backoff_seconds=max_backoff_seconds,
            )
            LOGGER.info(
                "Waiting for Schema Registry at %s (retry in %.1fs)",
                safe_target,
                delay,
            )
            _sleep_with_jitter(delay)


def wait_for_dependencies(settings: StartupSettings) -> None:
    LOGGER.info("Starting readiness checks...")
    host, port = _parse_kafka_bootstrap(settings.kafka_bootstrap_servers)
    wait_for_kafka(
        host=host,
        port=port,
        max_wait_seconds=settings.startup_max_wait_seconds,
        initial_backoff_seconds=settings.startup_initial_backoff_seconds,
        max_backoff_seconds=settings.startup_max_backoff_seconds,
        attempt_timeout_seconds=settings.startup_attempt_timeout_seconds,
    )
    wait_for_schema_registry(
        registry_url=settings.schema_registry_url,
        max_wait_seconds=settings.startup_max_wait_seconds,
        initial_backoff_seconds=settings.startup_initial_backoff_seconds,
        max_backoff_seconds=settings.startup_max_backoff_seconds,
        attempt_timeout_seconds=settings.startup_attempt_timeout_seconds,
    )
