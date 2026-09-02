"""Authority domain unit tests."""

from authority.ingest import build_chunks
from authority.live_card import generate_live_card
from authority.manifest import resolve_bot_root
from authority.router import namespaces_for_query


def test_router_live_flags():
    nss = namespaces_for_query("How do I restart the sniper containers after a flag change?")
    assert "compose-live" in nss or "docs-ai" in nss
    assert "state-live" in nss or "compose-live" in nss


def test_router_encode_prefers_code():
    nss = namespaces_for_query("What is CANONICAL_BTC_REGIME unknown code?")
    assert "code-critical" in nss or "tests-parity" in nss


def test_dry_ingest_builds_chunks():
    bot = resolve_bot_root()
    chunks = build_chunks(bot)
    assert len(chunks) > 0
    namespaces = {c.namespace for c in chunks}
    assert "docs-ai" in namespaces
    assert "code-critical" in namespaces
    assert "state-live" in namespaces

    blob = "\n".join(c.text for c in chunks if "CANONICAL_BTC_REGIME" in c.text or "unknown" in c.text)
    assert "3" in blob


def test_live_card_mentions_measurement_rules():
    bot = resolve_bot_root()
    card = generate_live_card(bot)
    assert "direction_correct_close" in card
    assert "prediction_id" in card
    assert "GARBAGE" in card
    assert "SNIPER_FORCE_REGIME_FIX_DEPLOY" in card
