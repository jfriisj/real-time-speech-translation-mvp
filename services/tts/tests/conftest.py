from __future__ import annotations

from pathlib import Path
import sys
from types import ModuleType


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

if "prometheus_client" not in sys.modules:
    fake_module = ModuleType("prometheus_client")

    class _NoOpMetric:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def observe(self, *_args, **_kwargs) -> None:
            return None

        def labels(self, *_args, **_kwargs):
            return self

        def inc(self, *_args, **_kwargs) -> None:
            return None

    fake_module.Counter = _NoOpMetric  # type: ignore[attr-defined]
    fake_module.Histogram = _NoOpMetric  # type: ignore[attr-defined]

    def _noop_start_http_server(*_args, **_kwargs) -> None:
        return None

    fake_module.start_http_server = _noop_start_http_server  # type: ignore[attr-defined]
    sys.modules["prometheus_client"] = fake_module

if "boto3" not in sys.modules:
    fake_boto3 = ModuleType("boto3")

    class _FakeClient:
        def put_object(self, *args, **kwargs) -> None:  # noqa: ANN001
            return None

    def _fake_client(*_args, **_kwargs):
        return _FakeClient()

    fake_boto3.client = _fake_client  # type: ignore[attr-defined]
    sys.modules["boto3"] = fake_boto3
