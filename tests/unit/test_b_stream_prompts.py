"""Escalation B-stream Jinja system prompts."""

from __future__ import annotations

import pytest

from application.prompts.b_stream import render_b_stream_system_prompt
from application.vulnerabilities.direct_prompt_escalation import STAGE_TO_SECRET, level_for_escalation_stage


@pytest.mark.parametrize(
    "stage,expected_secret", [(0, "margherita"), (1, "sausage"), (2, "slice"), (5, "chili")]
)
def test_b_stream_renders_secret(stage: int, expected_secret: str):
    level = level_for_escalation_stage(stage)
    secret = STAGE_TO_SECRET[stage]
    assert secret == expected_secret
    text = render_b_stream_system_prompt(stage, secret=secret, baseline_level=level)
    assert expected_secret in text.lower()
    assert "{{" not in text


def test_all_ten_stages_render():
    for s in range(10):
        level = level_for_escalation_stage(s)
        secret = LEVEL_TO_SECRET[level]
        out = render_b_stream_system_prompt(s, secret=secret, baseline_level=level)
        assert len(out) > 40
