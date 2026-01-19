from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from speech_lib import (
    AudioInputPayload,
    BaseEvent,
    KafkaProducerWrapper,
    SchemaRegistryClient,
    TOPIC_AUDIO_INGRESS,
    load_schema,
)

from .audio import pcm_to_wav
from .config import Settings
from .limits import BufferAccumulator, ConnectionLimiter, RateLimiter
from .protocol import build_handshake_message, parse_sentinel_message


LOGGER = logging.getLogger(__name__)


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(title="Ingress Gateway", version="0.3.0-dev")
    app.state.settings = settings
    app.state.connection_limiter = ConnectionLimiter(settings.max_connections)

    @app.on_event("startup")
    def _startup() -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        schema = load_schema("AudioInputEvent.avsc", schema_dir=settings.schema_dir)
        registry = SchemaRegistryClient(settings.schema_registry_url)
        registry.register_schema(f"{TOPIC_AUDIO_INGRESS}-value", schema)
        app.state.audio_schema = schema
        app.state.producer = KafkaProducerWrapper.from_confluent(
            settings.kafka_bootstrap_servers
        )
        LOGGER.info("Gateway service started; ws endpoint ready")

    @app.websocket("/ws/audio")
    async def websocket_audio(websocket: WebSocket) -> None:
        await handle_websocket(websocket, app.state)

    return app


async def handle_websocket(websocket: WebSocket, state: Any) -> None:
    settings: Settings = state.settings
    origin = websocket.headers.get("origin")
    if settings.origin_allowlist and origin not in settings.origin_allowlist:
        await websocket.close(code=1008)
        LOGGER.warning("Rejected connection due to origin policy")
        return

    limiter: ConnectionLimiter = state.connection_limiter
    acquired = await limiter.acquire()
    if not acquired:
        await websocket.close(code=1013)
        LOGGER.warning("Rejected connection due to max connection limit")
        return

    correlation_id = str(uuid4())
    await websocket.accept()
    await websocket.send_text(build_handshake_message(correlation_id))

    buffer = BufferAccumulator(settings.max_buffer_bytes)
    rate_limiter = RateLimiter(settings.max_messages_per_second)
    start_time = time.monotonic()
    should_publish = True

    try:
        while True:
            elapsed = time.monotonic() - start_time
            if elapsed > settings.max_session_seconds:
                should_publish = False
                await websocket.close(code=1008)
                LOGGER.warning("Closed connection: session duration exceeded")
                return

            try:
                message = await asyncio.wait_for(
                    websocket.receive(), timeout=settings.idle_timeout_seconds
                )
            except asyncio.TimeoutError:
                should_publish = False
                await websocket.close(code=1001)
                LOGGER.warning("Closed connection: idle timeout")
                return

            if not rate_limiter.allow():
                should_publish = False
                await websocket.close(code=1008)
                LOGGER.warning("Closed connection: message rate exceeded")
                return

            if message.get("type") == "websocket.disconnect":
                break

            if message.get("bytes") is not None:
                payload: bytes = message["bytes"] or b""
                if len(payload) > settings.max_chunk_bytes:
                    should_publish = False
                    await websocket.close(code=1009)
                    LOGGER.warning("Closed connection: chunk size exceeded")
                    return
                try:
                    buffer.add_chunk(payload)
                except ValueError:
                    should_publish = False
                    await websocket.close(code=1009)
                    LOGGER.warning("Closed connection: buffer size exceeded")
                    return
            elif message.get("text") is not None:
                text = message["text"] or ""
                if parse_sentinel_message(text):
                    if buffer.size == 0:
                        should_publish = False
                        await websocket.close(code=1003)
                        LOGGER.warning("Closed connection: empty stream")
                        return
                    try:
                        await finalize_publish(state, buffer, settings, correlation_id)
                    except ValueError as exc:
                        should_publish = False
                        await websocket.close(code=1003)
                        LOGGER.warning("Closed connection: %s", exc)
                        return
                    await websocket.close(code=1000)
                    LOGGER.info("Completed stream correlation_id=%s", correlation_id)
                    return
                should_publish = False
                await websocket.close(code=1003)
                LOGGER.warning("Closed connection: unsupported text frame")
                return
    except WebSocketDisconnect:
        LOGGER.info("Client disconnected correlation_id=%s", correlation_id)
    finally:
        await limiter.release()

    if should_publish and buffer.size > 0:
        try:
            await finalize_publish(state, buffer, settings, correlation_id)
        except ValueError as exc:
            LOGGER.warning("Dropping stream on disconnect: %s", exc)
            return
        LOGGER.info("Completed stream on disconnect correlation_id=%s", correlation_id)


async def finalize_publish(
    state: Any,
    buffer: BufferAccumulator,
    settings: Settings,
    correlation_id: str,
) -> None:
    if buffer.size == 0:
        raise ValueError("no audio data received")
    audio_bytes = buffer.to_bytes()
    wav_bytes = pcm_to_wav(audio_bytes, settings.sample_rate_hz)
    payload = AudioInputPayload(
        audio_bytes=wav_bytes,
        audio_format=settings.audio_format,
        sample_rate_hz=settings.sample_rate_hz,
    )
    payload.validate()

    event = BaseEvent(
        event_type="AudioInputEvent",
        correlation_id=correlation_id,
        source_service="gateway-service",
        payload={
            "audio_bytes": payload.audio_bytes,
            "audio_format": payload.audio_format,
            "sample_rate_hz": payload.sample_rate_hz,
            "language_hint": payload.language_hint,
        },
    )

    schema: Dict[str, Any] = state.audio_schema
    producer: KafkaProducerWrapper = state.producer
    producer.publish_event(TOPIC_AUDIO_INGRESS, event, schema, key=correlation_id)


def main() -> None:
    settings = Settings.from_env()
    app = create_app(settings)

    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")


if __name__ == "__main__":
    main()
