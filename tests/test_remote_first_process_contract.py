import re
from pathlib import Path


PROCEDURAL_SKILLS = [
    "slice-implementation",
    "regression-and-test-strategy",
    "radar-run-self-test",
    "radar-run-autofix",
    "radar-run-diagnostics",
    "demo-maintenance",
    "frontend-design-system",
    "radar-pipeline-to-be-design",
    "radar-pipeline-as-is-sync",
    "radar-pipeline-to-as-is-finalize",
]


def test_procedural_skills_do_not_contain_active_local_execution_commands() -> None:
    active_local_command = re.compile(
        r"(?m)^\s*(?:docker\s+compose|python\s+-m\s+pytest|npm\s+(?:--prefix|run)|"
        r"Invoke-RestMethod\s+https?://(?:127\.0\.0\.1|localhost))"
    )
    for skill_name in PROCEDURAL_SKILLS:
        text = Path(f".agents/skills/{skill_name}/SKILL.md").read_text(encoding="utf-8")
        assert not active_local_command.search(text), skill_name
        assert "remote" in text.lower(), skill_name


def test_agents_makes_remote_failure_a_blocker() -> None:
    agents = Path("AGENTS.md").read_text(encoding="utf-8")
    assert "## Mandatory remote execution contour" in agents
    assert "Never silently fall back" in agents
    assert "-AllowProviderCalls" in agents


def test_frontend_product_api_uses_the_remote_aware_api_origin() -> None:
    sales_api = Path("frontend/src/api/salesPlaybookApi.ts").read_text(encoding="utf-8")

    assert "radarApiBaseUrl()" in sales_api
    assert "127.0.0.1:8001/api/products" not in sales_api
