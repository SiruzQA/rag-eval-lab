"""RAG qiymətləndirməsi: Faithfulness və Context Precision (DeepEval).

Hər ssenari ayrıca ölçülür, sonra ORTA bal threshold ilə müqayisə olunur.
Threshold-dan aşağı olarsa pytest fail edir -> CI PR-ı bloklayır.
"""
import json
import os
import statistics
import sys
import time
from pathlib import Path

import pytest
from deepeval.metrics import ContextualPrecisionMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from app.rag import SimpleRAG  # noqa: E402
from gemini_judge import GeminiJudge  # noqa: E402

DATASET = ROOT / "datasets" / "golden_v1.jsonl"
REPORT = ROOT / "reports" / "results.json"
FAITHFULNESS_MIN = float(os.getenv("FAITHFULNESS_MIN", "0.8"))
CONTEXT_PRECISION_MIN = float(os.getenv("CONTEXT_PRECISION_MIN", "0.7"))
SLEEP = float(os.getenv("EVAL_SLEEP", "2"))  # pulsuz API limiti üçün fasilə


def load_cases():
    with open(DATASET, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    # injection və kontekstdən kənar suallar promptfoo / ayrı testlərdə yoxlanılır
    return [r for r in rows if r["category"] not in ("injection", "out_of_scope")]


@pytest.fixture(scope="module")
def results():
    rag = SimpleRAG()
    judge = GeminiJudge()
    faith = FaithfulnessMetric(model=judge, include_reason=False, async_mode=False)
    prec = ContextualPrecisionMetric(model=judge, include_reason=False, async_mode=False)

    rows = []
    for case in load_cases():
        out = rag.ask(case["question"])
        tc = LLMTestCase(
            input=case["question"],
            actual_output=out["answer"],
            expected_output=case["expected_answer"],
            retrieval_context=out["contexts"],
        )
        faith.measure(tc)
        prec.measure(tc)
        rows.append({
            "id": case["id"],
            "question": case["question"],
            "answer": out["answer"],
            "faithfulness": faith.score,
            "context_precision": prec.score,
        })
        time.sleep(SLEEP)

    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return rows


def test_faithfulness_mean(results):
    mean = statistics.mean(r["faithfulness"] for r in results)
    low = [r["id"] for r in results if r["faithfulness"] < FAITHFULNESS_MIN]
    assert mean >= FAITHFULNESS_MIN, f"Faithfulness {mean:.2f} < {FAITHFULNESS_MIN}. Zəif ssenarilər: {low}"


def test_context_precision_mean(results):
    mean = statistics.mean(r["context_precision"] for r in results)
    low = [r["id"] for r in results if r["context_precision"] < CONTEXT_PRECISION_MIN]
    assert mean >= CONTEXT_PRECISION_MIN, f"Context Precision {mean:.2f} < {CONTEXT_PRECISION_MIN}. Zəif ssenarilər: {low}"
