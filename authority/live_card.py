"""Generate rag_live_card.md from bot-repo state (Tier C)."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path


def _read_json(path: Path) -> dict | list | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _yaml_scalar_lookups(compose_text: str, keys: list[str]) -> dict[str, str]:
    found: dict[str, str] = {}
    for key in keys:
        # Match KEY: value or KEY=value in env blocks
        patterns = [
            rf"(?m)^\s*-\s*{re.escape(key)}=([^\s#]+)",
            rf"(?m)^\s*{re.escape(key)}:\s*[\"']?([^\"'\n#]+)",
            rf"{re.escape(key)}=([^\s,\"']+)",
        ]
        for pat in patterns:
            m = re.search(pat, compose_text)
            if m:
                found[key] = m.group(1).strip().strip("\"'")
                break
    return found


def _compose_force_regime(compose_text: str) -> str:
    """Return live force-regime value or explicitly disarmed/empty."""
    m = re.search(
        r"SNIPER_FORCE_REGIME_FIX_DEPLOY[=:][\"'\s]*([A-Za-z0-9_,-]*)",
        compose_text,
    )
    if not m:
        return "(disarmed / not set in compose — treat as empty)"
    val = m.group(1).strip()
    if not val or val.lower() in {"false", "0", "none", "off", '""', "''"}:
        return "(disarmed / empty)"
    return val


def _sample_predictions(bot_root: Path, n: int = 8) -> tuple[str, list[str]]:
    csv_path = bot_root / "logs" / "predictions_multi_asset.csv"
    if not csv_path.is_file():
        return "", []
    try:
        lines = csv_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return "", []
    if not lines:
        return "", []
    header = lines[0]
    # Prefer annotated mix: skip pure GARBAGE if possible after first few
    samples = lines[1 : min(len(lines), n + 1)]
    return header, samples


def generate_live_card(bot_root: Path) -> str:
    compose_path = bot_root / "docker-compose.multi_asset.yml"
    compose = compose_path.read_text(encoding="utf-8") if compose_path.is_file() else ""

    flags = _yaml_scalar_lookups(
        compose,
        [
            "SNIPER_BTC_REAL_CATEGORIES",
            "SNIPER_SOL_STATIONARIZE_LIVE",
            "SNIPER_SOL_STATIONARIZE_TRAIN",
            "SNIPER_FORCE_REGIME_FIX_DEPLOY",
            "SNIPER_MIN_UPLIFT_SOL",
            "SNIPER_MIN_UPLIFT_LTC",
        ],
    )
    force = _compose_force_regime(compose)

    sol_meta = _read_json(bot_root / "models" / "sol" / "deployment_metadata.json") or {}
    ltc_meta = _read_json(bot_root / "models" / "ltc" / "deployment_metadata.json") or {}
    footing = _read_json(bot_root / "reports" / "sol_live_footing.json")
    promo = _read_json(bot_root / "reports" / "retrain_promotion_summary.json")

    # Config uplift floors
    config_path = bot_root / "workflows" / "config" / "retrain_config.yaml"
    config_text = config_path.read_text(encoding="utf-8") if config_path.is_file() else ""
    uplift = {}
    for asset in ("sol", "ltc"):
        m = re.search(
            rf"(?is){asset}.*?min_uplift[_a-z]*\s*:\s*([0-9.]+)",
            config_text,
        )
        if m:
            uplift[asset.upper()] = m.group(1)
    # also try flat keys
    for key in ("min_uplift_ltc", "min_uplift_sol", "ltc_min_uplift", "sol_min_uplift"):
        m = re.search(rf"(?m)^\s*{key}\s*:\s*([0-9.]+)", config_text)
        if m:
            asset = "LTC" if "ltc" in key else "SOL"
            uplift[asset] = m.group(1)

    header, samples = _sample_predictions(bot_root)

    generated_at = datetime.now(UTC).isoformat()

    def meta_line(label: str, meta: dict) -> str:
        if not isinstance(meta, dict):
            return f"- **{label}**: (missing)"
        return (
            f"- **{label}**: last_deployed_at=`{meta.get('last_deployed_at', 'n/a')}`, "
            f"reason=`{meta.get('reason', 'n/a')}`, "
            f"forced_replacement=`{meta.get('forced_replacement', 'n/a')}`, "
            f"last_write_reason=`{meta.get('last_write_reason', 'n/a')}`"
        )

    promo_summary = ""
    if isinstance(promo, dict):
        promo_summary = json.dumps(promo, indent=2)[:4000]
    elif promo is not None:
        promo_summary = str(promo)[:4000]
    else:
        promo_summary = "(missing reports/retrain_promotion_summary.json)"

    footing_blob = (
        json.dumps(footing, indent=2)[:2000]
        if footing is not None
        else "(missing reports/sol_live_footing.json)"
    )

    sample_block = ""
    if header:
        sample_block = "```\n" + header + "\n" + "\n".join(samples) + "\n```"
    else:
        sample_block = "(predictions CSV not found — skip full CSV; do not invent rows)"

    card = f"""# Sniper Bot Live Card

Generated: `{generated_at}`
Source root: `{bot_root}`
Namespace: `state-live`
Freshness: generated on refresh — prefer this for "what's live?" questions.

## Live flags (compose-live / multi_asset compose file)

| Flag | Value |
|------|-------|
| SNIPER_BTC_REAL_CATEGORIES | {flags.get('SNIPER_BTC_REAL_CATEGORIES', '(not found — verify compose)')} |
| SNIPER_SOL_STATIONARIZE_LIVE | {flags.get('SNIPER_SOL_STATIONARIZE_LIVE', '(not found)')} |
| SNIPER_SOL_STATIONARIZE_TRAIN | {flags.get('SNIPER_SOL_STATIONARIZE_TRAIN', '(not found)')} |
| SNIPER_FORCE_REGIME_FIX_DEPLOY | {force} |
| SNIPER_MIN_UPLIFT_SOL (compose) | {flags.get('SNIPER_MIN_UPLIFT_SOL', '(not in compose)')} |
| SNIPER_MIN_UPLIFT_LTC (compose) | {flags.get('SNIPER_MIN_UPLIFT_LTC', '(not in compose)')} |

Config uplift floors (retrain_config.yaml, if present): SOL={uplift.get('SOL', 'see config')}, LTC={uplift.get('LTC', 'see config')}

**Invariant:** Treat `SNIPER_FORCE_REGIME_FIX_DEPLOY` as **disarmed/empty** unless compose shows a non-empty target asset list.

**Ops:** Env/flag changes in compose require **container recreate**. Model files on disk are picked up by the next scorer subprocess without recreate.

## Per-asset deploy metadata

{meta_line('SOL', sol_meta if isinstance(sol_meta, dict) else {})}
{meta_line('LTC', ltc_meta if isinstance(ltc_meta, dict) else {})}

## SOL live footing report

```json
{footing_blob}
```

## Last promotion summary

```json
{promo_summary}
```

## Predictions CSV — header + annotated sample rows ONLY

Do NOT load the full CSV into the RAG. Measurement reminders:
- Metric: `direction_correct_close`
- Exclude rows with `GARBAGE` in note
- Use `prediction_id` scored-at for post-deploy filters — NOT candle `timestamp`
- Train/serve SOL footing must match (`SNIPER_SOL_STATIONARIZE_TRAIN` ↔ `SNIPER_SOL_STATIONARIZE_LIVE`)

{sample_block}

## Hard codebook reminder (local truth)

`CANONICAL_BTC_REGIME`: ranging=0, trending_bear=1, trending_bull=2, unknown=3, volatile=4.
Post–Half A models require `SNIPER_BTC_REAL_CATEGORIES=true`.
SOL uses z-footing on 8 columns; LTC is raw — assets are NOT symmetric.
Do not recommend `scripts/audit_gate_comparison.py` for routine gate verification after footing changes (false positives).
"""
    return card


def write_live_card(bot_root: Path, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    card = generate_live_card(bot_root)
    output.write_text(card, encoding="utf-8")
    return output
