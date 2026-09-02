"""Answer formatting tests."""

from frontend.components.formatting import answer_lines, plain_text_answer


def test_strips_bold_and_code():
    raw = "**unknown** maps to `3` in the codebook."
    assert plain_text_answer(raw) == "unknown maps to 3 in the codebook."


def test_converts_bullets():
    raw = "- First item\n- Second item"
    lines = answer_lines(raw)
    assert any(l.startswith("• ") for l in lines)
