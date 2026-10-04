"""DeepEval üçün Gemini 'hakim' (judge) modeli."""
import json
import os
import re

from deepeval.models import DeepEvalBaseLLM
from langchain_google_genai import ChatGoogleGenerativeAI

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gemini-3.8-flash")


def _text(response) -> str:
    """Yeni langchain versiyalarında content siyahı ola bilər."""
    content = response.content
    if isinstance(content, list):
        return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return content


def _load_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(match.group(0) if match else text)


class GeminiJudge(DeepEvalBaseLLM):
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(model=JUDGE_MODEL, temperature=0)

    def load_model(self):
        return self.model

    def generate(self, prompt: str, schema=None):
        if schema is None:
            return _text(self.model.invoke(prompt))
        try:
            return self.model.with_structured_output(schema).invoke(prompt)
        except Exception:
            raw = _text(self.model.invoke(prompt))
            return schema(**_load_json(raw))

    async def a_generate(self, prompt: str, schema=None):
        return self.generate(prompt, schema)

    def get_model_name(self):
        return JUDGE_MODEL
