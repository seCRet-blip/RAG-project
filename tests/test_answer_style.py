"""Retrieval priority helpers (not answer schemas)."""

from authority.answer_style import query_priority_keys
from authority.router import namespaces_for_query


def test_encode_query_keys():
    keys = query_priority_keys("Should ranging encode as 1?")
    assert "CANONICAL_BTC_REGIME" in keys
    assert "direction_correct_close" not in keys


def test_encode_namespaces():
    nss = namespaces_for_query("Should ranging encode as 1?")
    assert nss[0] == "code-critical"


def test_measurement_keys_not_forced_on_encode_namespace_path():
    nss = namespaces_for_query("What is unknown in CANONICAL_BTC_REGIME?")
    assert "code-critical" in nss
