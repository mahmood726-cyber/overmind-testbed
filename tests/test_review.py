"""Test multi-persona review for CardioOracle."""
from __future__ import annotations

from overmind.review.multi_persona import MultiPersonaReviewer
from overmind.review.finding import parse_review_output, compute_consensus


def test_five_personas_for_high_risk_math(fresh_db, cardiooracle_project):
    """CardioOracle (high-risk, advanced_math) should get all 5 personas."""
    reviewer = MultiPersonaReviewer(fresh_db)
    personas = reviewer.select_personas(cardiooracle_project)
    assert len(personas) == 5
    names = {p.name for p in personas}
    assert "correctness" in names
    assert "statistical_rigor" in names
    assert "security" in names
    assert "robustness" in names
    assert "efficiency" in names


def test_cross_model_dispatch(fresh_db, cardiooracle_project):
    """Reviewer runner must differ from writer runner (cross-model)."""
    reviewer = MultiPersonaReviewer(fresh_db)
    personas = reviewer.select_personas(cardiooracle_project)
    for persona in personas:
        reviewer_runner = reviewer.preferred_runner_for(persona, "claude")
        assert reviewer_runner != "claude"


def test_consensus_from_mock_outputs(fresh_db):
    """Two persona outputs with shared finding -> consensus BLOCK."""
    r1 = parse_review_output(
        "correctness",
        "- [P1] Missing validation on input\nVERDICT: CONCERNS",
    )
    r2 = parse_review_output(
        "robustness",
        "- [P1] Missing validation on user input\nVERDICT: CONCERNS",
    )
    consensus = compute_consensus([r1, r2])
    assert consensus.overall_verdict == "BLOCK"
    assert consensus.p0_count >= 1


def test_parse_review_output_extracts_findings():
    """parse_review_output correctly extracts severity and description."""
    result = parse_review_output(
        "security",
        "- [P0] SQL injection in query builder\n- [P2] Minor log leak\nVERDICT: BLOCK",
    )
    assert result.verdict == "BLOCK"
    assert len(result.findings) == 2
    assert result.findings[0].severity == "P0"
    assert "SQL injection" in result.findings[0].description
