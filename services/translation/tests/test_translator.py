from __future__ import annotations

import os

import pytest

from translation_service.translator import HuggingFaceTranslator


def test_huggingface_translator_translates_en_to_es() -> None:
    if os.getenv("RUN_TRANSLATION_MODEL_TEST") != "1":
        pytest.skip("Set RUN_TRANSLATION_MODEL_TEST=1 to run model download/inference test")

    translator = HuggingFaceTranslator(model_name="Helsinki-NLP/opus-mt-en-es")
    out = translator.translate("hello", source_language="en", target_language="es")
    assert isinstance(out, str)
    assert out.strip()
