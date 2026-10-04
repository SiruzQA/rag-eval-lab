"""DeepEval üçün Gemini 'hakim' (judge) modeli."""
import os

from deepeval.metrics.utils import trim_and_load_json
from deepeval.models import DeepEvalBaseLLM
from langchain_google_genai import ChatGoogleGenerativeAI

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gemini-2.5-flash")


class GeminiJudge(DeepEvalBaseLLM):
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(model=JUDGE_MODEL, temperature=0)

    def load_model(self):
        return self.model

    def generate(self, prompt: str, schema=None):
        if schema is None:
            return self.model.invoke(prompt).content
        try:
            return self.model.with_structured_output(schema).invoke(prompt)
        except Exception:
            raw = self.model.invoke(prompt).content
            return schema(**trim_and_load_json(raw))

    async def a_generate(self, prompt: str, schema=None):
        return self.generate(prompt, schema)

    def get_model_name(self):
        return JUDGE_MODEL
