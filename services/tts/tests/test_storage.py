from __future__ import annotations

from dataclasses import dataclass
import sys
from types import ModuleType

import pytest


@dataclass
class _PutObjectCall:
    bucket: str
    key: str
    body: bytes
    content_type: str


class _FakeClient:
    def __init__(self) -> None:
        self.calls: list[_PutObjectCall] = []
        self.presign_calls: list[tuple[str, dict, int]] = []

    def put_object(self, *, Bucket: str, Key: str, Body: bytes, ContentType: str) -> None:  # noqa: N803
        self.calls.append(
            _PutObjectCall(
                bucket=Bucket,
                key=Key,
                body=Body,
                content_type=ContentType,
            )
        )

    def generate_presigned_url(self, operation_name: str, *, Params: dict, ExpiresIn: int) -> str:  # noqa: N803
        self.presign_calls.append((operation_name, Params, ExpiresIn))
        bucket = Params["Bucket"]
        key = Params["Key"]
        return f"http://minio:9000/{bucket}/{key}?X-Amz-Signature=fake"


class _FakeBoto3:
    def __init__(self, client: _FakeClient) -> None:
        self._client = client

    def client(self, *_args, **_kwargs):
        return self._client


def test_upload_bytes_returns_public_uri(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = _FakeClient()
    fake_boto3 = _FakeBoto3(fake_client)

    fake_module = ModuleType("boto3")
    fake_module.client = fake_boto3.client  # type: ignore[attr-defined]
    sys.modules["boto3"] = fake_module

    from tts_service import storage as storage_module
    from importlib import reload

    storage_module = reload(storage_module)
    ObjectStorage = storage_module.ObjectStorage

    storage = ObjectStorage(
        endpoint="http://minio:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        bucket="tts-audio",
        secure=False,
        public_endpoint="http://localhost:9000",
    )

    uri = storage.upload_bytes(key="corr/file.wav", data=b"data", content_type="audio/wav")

    assert uri == "http://localhost:9000/tts-audio/corr/file.wav?X-Amz-Signature=fake"
    assert fake_client.calls
    assert fake_client.presign_calls
    call = fake_client.calls[0]
    assert call.bucket == "tts-audio"
    assert call.key == "corr/file.wav"
    assert call.body == b"data"
    assert call.content_type == "audio/wav"
