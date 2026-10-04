"""Promptfoo üçün Python provider: sorğunu birbaşa RAG tətbiqinə göndərir."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.rag import SimpleRAG  # noqa: E402

_rag = None


def call_api(prompt, options, context):
    global _rag
    if _rag is None:
        _rag = SimpleRAG()
    return {"output": _rag.ask(prompt)["answer"]}
