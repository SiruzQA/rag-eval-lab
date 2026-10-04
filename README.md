# rag-eval-lab

A small RAG assistant with an **automated evaluation and security-testing pipeline** that gates pull requests in CI.

The app itself is intentionally simple. The point of the project is the QA layer around it: a versioned golden dataset, LLM-output metrics with thresholds, adversarial tests, and a CI gate.

## What it does

| Layer | Tooling | Purpose |
|---|---|---|
| App | LangChain, Chroma, Gemini | Answers customer-support questions from 6 markdown docs |
| Golden dataset | `datasets/golden_v1.jsonl` | 20 versioned scenarios (18 in-scope, 1 out-of-scope, 1 injection) |
| Quality eval | DeepEval | Faithfulness and Context Precision, gated by thresholds |
| Security eval | Promptfoo | Prompt injection, data leakage, unsafe tool-use claims |
| CI gate | GitHub Actions | Fails the PR if any threshold or security test fails |

## Architecture

```
PR opened
   |
   +--> rag-eval job:      pytest -> DeepEval -> mean score vs threshold
   |                         Faithfulness >= 0.8, Context Precision >= 0.7
   |
   +--> security-eval job: Promptfoo -> 8 adversarial tests (exit code 100 on failure)
   |
   v
Branch protection blocks merge unless both jobs pass
```

## Project structure

```
app/rag.py                      RAG application
app/docs/                       Knowledge base (markdown)
datasets/golden_v1.jsonl        Golden dataset v1
tests/test_rag.py               DeepEval quality gate
tests/gemini_judge.py           Gemini as the DeepEval judge model
security/promptfooconfig.yaml   Adversarial test suite
security/provider.py            Promptfoo provider that calls the app
.github/workflows/eval.yml      CI pipeline
```

## Run locally

```bash
pip install -r requirements.txt
export GOOGLE_API_KEY="your-key"        # never commit this

pytest tests/ -v                         # quality gate
npx promptfoo@latest eval -c security/promptfooconfig.yaml
npx promptfoo@latest view                # browse results
```

Thresholds are configurable: `FAITHFULNESS_MIN`, `CONTEXT_PRECISION_MIN`, `EVAL_SLEEP` (delay between calls for free-tier rate limits).

## Golden dataset

Each line in `golden_v1.jsonl` has: `id`, `category`, `question`, `expected_answer`, `source`.
The file is versioned (`v1`, `v2`, ...). When the knowledge base changes, create a new version instead of editing in place, so scores stay comparable across runs.

Categories: refund, shipping, warranty, payment, account, support, out_of_scope, injection.

## Results

> TODO: fill in after the first real run (`reports/results.json`, Promptfoo view).

| Run | Model | Faithfulness (mean) | Context Precision (mean) | Promptfoo pass rate |
|---|---|---|---|---|
| v1 baseline | TODO | TODO | TODO | TODO / 8 |

## Re-validation on model change

The chat and judge models are set via environment variables (`CHAT_MODEL`, `JUDGE_MODEL`). To re-validate after a model version change, update the variable and re-run the pipeline; compare the new scores against the baseline row above.

## Defect reports

> TODO: document 1-2 real findings from the first run in this format.

### DEF-001: <short title>

- **Severity:** High / Medium / Low
- **Component:** RAG app / retrieval / prompt
- **Found by:** Promptfoo test "<name>" or golden scenario `gXX`
- **Steps to reproduce:**
  1. Run `<command>`
  2. Send the question: `<input>`
- **Expected:** <expected behavior>
- **Actual:** <actual behavior>
- **Evidence:** <screenshot, report link, score>
- **Status:** Open / Fixed in <commit>

## Known limitations

- The judge model is the same model family as the app, which can bias scores. A cross-check with a different judge is a planned improvement.
- 18 scored scenarios is a small sample, so scores are noisy. Repeated sampling and bootstrapped confidence intervals are planned.
- Indirect prompt injection (malicious content inside retrieved documents) is not covered yet.
- The app has no real tools, so "unsafe tool use" tests check that it does not falsely claim to perform actions.
