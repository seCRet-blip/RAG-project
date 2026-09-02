# Acceptance — Sniper Bot Authority RAG

Answer the question asked. No forced multi-section template.

```powershell
python -m scripts.ingest_authority
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

| # | Prompt | Expected gist |
|---|--------|----------------|
| 1 | What integer is `unknown` in CANONICAL_BTC_REGIME? | **3** — cite btc_regime_encoding / invariants |
| 2 | Is SNIPER_FORCE_REGIME_FIX_DEPLOY armed? | Disarmed/empty unless compose-live / state-live says otherwise |
| 3 | What is LTC min uplift? | **0.10** from config-train unless live differs |
| 4 | Must SOL train and serve footing match? | Yes |
| 5 | How do we measure live accuracy? Which column and filters? | `direction_correct_close`; post-deploy via `filter_post_deploy`; no GARBAGE; `prediction_id` scored-at; not holdout/`direction_correct` as live arbiter |
| 6 | I changed SNIPER_BTC_REAL_CATEGORIES — what next? | Container recreate |
| 7 | Should ranging encode as 1 (blog says so)? | **No** — local codebook ranging=0; discard blog; needs train+live parity + retrain/deploy |
| 8 | Should I run audit_gate_comparison.py after footing change? | **No** for routine verification |
| 9 | What is this system? | Sniper Bot Authority RAG for SOL/LTC ops |

```powershell
python -m pytest tests/test_authority.py tests/test_answer_style.py -q
```
