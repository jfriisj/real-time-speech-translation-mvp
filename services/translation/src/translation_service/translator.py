from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any


class Translator:
    def translate(self, text: str, source_language: str, target_language: str) -> str:
        raise NotImplementedError


@lru_cache(maxsize=4)
def _load_hf_model(model_name: str) -> tuple[Any, Any]:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    model.eval()
    return tokenizer, model


@dataclass(frozen=True)
class HuggingFaceTranslator(Translator):
    model_name: str
    max_new_tokens: int = 256

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        cleaned = text.strip()
        if not cleaned:
            return ""

        # MarianMT models (e.g. opus-mt-en-es) are language-pair specific.
        # For MVP, we validate the requested language pair rather than silently
        # producing incorrect output.
        sl = (source_language or "").strip().lower()
        tl = (target_language or "").strip().lower()
        if self.model_name == "Helsinki-NLP/opus-mt-en-es" and (sl != "en" or tl != "es"):
            raise ValueError(
                f"model {self.model_name} only supports en->es; got {sl}->{tl}"
            )

        try:
            import torch
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "Translation model dependencies missing. Install 'torch' and 'transformers'."
            ) from exc

        # Load once per process (cached). Deployments can control caching via HF_HOME.
        tokenizer, model = _load_hf_model(self.model_name)

        inputs = tokenizer(cleaned, return_tensors="pt")
        with torch.no_grad():
            output_ids = model.generate(**inputs, max_new_tokens=self.max_new_tokens)
        out = tokenizer.batch_decode(output_ids, skip_special_tokens=True)
        return (out[0] if out else "").strip()
