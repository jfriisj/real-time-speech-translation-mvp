from __future__ import annotations

from pathlib import Path
import sys
from types import ModuleType


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
SPEECH_LIB_PATH = Path(__file__).resolve().parents[3] / "shared" / "speech-lib" / "src"
for path in (SRC_PATH, SPEECH_LIB_PATH):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

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

if "onnxruntime" not in sys.modules:
    fake_ort = ModuleType("onnxruntime")
    
    class _FakeSession:
        def __init__(self, path, providers=None, **kwargs):
            pass
            
        def run(self, output_names, input_feed, **kwargs):
            # return dummy audio float array (1, N)
            import numpy as np
            return [np.zeros((1, 24000), dtype=np.float32)] 
            
        def get_inputs(self):
            return []

    fake_ort.InferenceSession = _FakeSession # type: ignore[attr-defined]
    sys.modules["onnxruntime"] = fake_ort

if "misaki" not in sys.modules:
    fake_misaki = ModuleType("misaki")
    fake_misaki_en = ModuleType("misaki.en")

    class _FakeG2P:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def __call__(self, _text: str):
            return "a"

    fake_misaki_en.G2P = _FakeG2P  # type: ignore[attr-defined]
    fake_misaki.en = fake_misaki_en  # type: ignore[attr-defined]
    sys.modules["misaki"] = fake_misaki
    sys.modules["misaki.en"] = fake_misaki_en

if "confluent_kafka" not in sys.modules:
    fake_kafka = ModuleType("confluent_kafka")
    
    class _FakeProducer:
        def __init__(self, config): pass
        def produce(self, topic, value, key=None, headers=None, on_delivery=None): pass
        def poll(self, timeout): pass
        def flush(self): pass
        
    class _FakeConsumer:
        def __init__(self, config): pass
        def subscribe(self, topics): pass
        def poll(self, timeout): return None
        def close(self): pass

    fake_kafka.Producer = _FakeProducer # type: ignore[attr-defined]
    fake_kafka.Consumer = _FakeConsumer # type: ignore[attr-defined]
    sys.modules["confluent_kafka"] = fake_kafka

