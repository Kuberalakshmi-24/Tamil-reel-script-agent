"""Unit and integration tests for Tamil Reel Script Agent components.

All tests run completely offline and deterministically without consuming
LLM API quota or depending on live internet connections.
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from pydantic import ValidationError

from src.models import (
    ScriptDraft,
    ScriptInput,
    ResearchResult,
    QualityCheckResult,
    CheckItem,
    FullDeliverable,
    SourceItem,
    HookItem,
    CtaOptionItem,
)
from src.llm import clean_json_response
from src.search_tool import search_web


def test_word_count_reactive_property():
    """Confirms bullet numbers and punctuation are ignored, and word_count updates reactively."""
    draft = ScriptDraft(
        hook="90% business websites oru brochure maadhiri irukku!",
        context="Visitors 5 seconds-la leave aaguraanga.",
        body_points=[
            "1. Clear value proposition missing.",
            "2. Complex contact forms on mobile.",
            "3. WhatsApp CTA button illai.",
        ],
        engagement="Unga website check pannirukeengala?",
        cta="Free audit-ku DM pannunga!",
    )
    initial_count = draft.word_count
    assert initial_count > 0
    # Expected words: 7 (hook) + 5 (context) + 4+5+4 (body without numbers) + 4 (engage) + 4 (cta) = 33
    assert initial_count <= 35

    # Test reactive recalculation when hook is updated
    draft.hook = "Website irundhum leads varalaya?"
    updated_count = draft.word_count
    assert updated_count != initial_count
    assert updated_count > 0


def test_script_input_validation_boundaries():
    """Verifies Pydantic boundaries for ScriptInput (Fix 6)."""
    # Valid input succeeds
    valid_inp = ScriptInput.create_with_defaults(
        topic="Valid business marketing topic",
        duration=30,
        tone="Tanglish",
    )
    assert valid_inp.topic == "Valid business marketing topic"
    assert valid_inp.duration == 30

    # Topic too short (< 3 chars) should raise ValidationError
    with pytest.raises(ValidationError):
        ScriptInput(topic="Hi", duration=30, tone="Tanglish")

    # Invalid duration outside [30, 45, 60] should raise ValidationError
    with pytest.raises(ValidationError):
        ScriptInput(topic="Valid topic here", duration=90, tone="Tanglish")

    # Invalid tone outside allowed literals should raise ValidationError
    with pytest.raises(ValidationError):
        ScriptInput(topic="Valid topic here", duration=30, tone="French")


def test_clean_json_response():
    """Tests non-greedy code fence extraction and handling of surrounding conversational text (Fix 2)."""
    # Test 1: Standard markdown code fence
    sample_1 = '```json\n{"status": "PASS", "score": 95}\n```'
    parsed_1 = clean_json_response(sample_1)
    assert parsed_1 == {"status": "PASS", "score": 95}

    # Test 2: Surrounding text before and after JSON
    sample_2 = 'Here is your audited result:\n```json\n{"valid": true}\n```\nHope this helps!'
    parsed_2 = clean_json_response(sample_2)
    assert parsed_2 == {"valid": True}

    # Test 3: Raw JSON without markdown fence
    sample_3 = '{"topic": "Tamil SEO", "duration": 30}'
    parsed_3 = clean_json_response(sample_3)
    assert parsed_3["topic"] == "Tamil SEO"

    # Test 4: Code fence with nested braces
    sample_4 = '```json\n{"meta": {"deep": true}, "items": [1, 2, 3]}\n```'
    parsed_4 = clean_json_response(sample_4)
    assert parsed_4["meta"]["deep"] is True


def test_deliverable_serialization(tmp_path: Path):
    """Verifies .save_deliverables() and .load_from_json() round-trip fidelity, including CTA options."""
    inp = ScriptInput.create_with_defaults(
        topic="Test Topic Leads",
        duration=30,
        tone="Tanglish",
    )
    research = ResearchResult(
        topic="Test Topic Leads",
        chosen_angle="Test Angle",
        sources=[SourceItem(url="https://example.com/test", claim_supported="Valid claim")],
    )
    draft = ScriptDraft(
        hook="Test Hook",
        hooks=[HookItem(type="question", text="Test Hook", is_recommended=True)],
        context="Test Context",
        body_points=["Test point"],
        engagement="Test question?",
        cta="DM us for audit",
        cta_options=[
            CtaOptionItem(text="DM us for audit", is_recommended=True, reason="Direct inquiry"),
            CtaOptionItem(text="Comment AUDIT below", is_recommended=False, reason="Low friction"),
        ],
    )
    qc = QualityCheckResult(
        unsupported_claims=CheckItem(status="PASS", notes="ok"),
        repetition=CheckItem(status="PASS", notes="ok"),
        weak_cta=CheckItem(status="PASS", notes="ok"),
        unnatural_tamil=CheckItem(status="PASS", notes="ok"),
        duration_fit=CheckItem(status="PASS", notes="ok"),
    )
    deliverable = FullDeliverable(
        input_data=inp,
        research=research,
        script=draft,
        quality_check=qc,
    )

    out_base = tmp_path / "test_out"
    deliverable.save_deliverables(out_base)

    # Check files exist
    assert out_base.with_suffix(".md").exists()
    assert out_base.with_suffix(".json").exists()

    # Verify markdown includes CTA options
    md_content = out_base.with_suffix(".md").read_text(encoding="utf-8")
    assert "Comment AUDIT below" in md_content

    # Round-trip load from JSON
    loaded = FullDeliverable.load_from_json(out_base.with_suffix(".json"))
    assert loaded.input_data.topic == "Test Topic Leads"
    assert loaded.script.hook == "Test Hook"
    assert len(loaded.script.cta_options) == 2
    assert loaded.research.sources[0].url == "https://example.com/test"


def test_search_tool_handles_failures():
    """Confirms search tool returns empty list instead of invented URLs on error."""
    results = search_web("   ")
    assert isinstance(results, list)
    for r in results:
        assert r.get("url") != "https://official.info/verify"


def _create_mock_deliverable() -> FullDeliverable:
    """Helper to create a deterministic mock deliverable for tests."""
    inp = ScriptInput.create_with_defaults(
        topic="Mocked Business Leads Topic",
        duration=30,
        tone="Tanglish",
    )
    research = ResearchResult(
        topic="Mocked Business Leads Topic",
        chosen_angle="Conversion Optimization",
        sources=[SourceItem(url="https://example.com/mock", claim_supported="Mocked claim")],
    )
    draft = ScriptDraft(
        hook="Mocked Hook",
        hooks=[HookItem(type="pain-point", text="Mocked Hook", is_recommended=True)],
        context="Mocked Context",
        body_points=["Point 1", "Point 2"],
        engagement="Agree pannreengala?",
        cta="Comment LEADS below",
        cta_options=[
            CtaOptionItem(text="Comment LEADS below", is_recommended=True, reason="Direct"),
        ],
    )
    qc = QualityCheckResult(
        unsupported_claims=CheckItem(status="PASS", notes="all claims verified"),
        repetition=CheckItem(status="PASS", notes="no repetitive phrasing"),
        weak_cta=CheckItem(status="PASS", notes="clear single CTA"),
        unnatural_tamil=CheckItem(status="PASS", notes="natural spoken Tanglish"),
        duration_fit=CheckItem(status="PASS", notes="duration calibrated"),
    )
    return FullDeliverable(
        input_data=inp,
        research=research,
        script=draft,
        quality_check=qc,
    )


def test_fastapi_health_endpoint():
    """Verify FastAPI health endpoint responds correctly without network."""
    from fastapi.testclient import TestClient
    from api import app

    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "active_provider" in data


def test_fastapi_generate_endpoint_offline_mocked():
    """Verify script generation via FastAPI endpoint using offline mock (Fix 8)."""
    from fastapi.testclient import TestClient
    import api

    mock_deliverable = _create_mock_deliverable()

    with patch.object(api.pipeline, "run", return_value=mock_deliverable) as mock_run:
        client = TestClient(api.app)
        payload = {
            "topic": "Why are businesses not getting leads from their websites?",
            "duration": 30,
            "tone": "Tanglish",
            "objective": "Get agency leads",
        }
        response = client.post("/api/v1/scripts/generate", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "deliverable" in data
        assert "markdown" in data
        assert data["deliverable"]["script"]["word_count"] > 0
        assert mock_run.called


def test_pipeline_offline_execution():
    """Verify 3-step pipeline can execute fully offline with mocked search and LLM."""
    from src.pipeline import TamilReelScriptPipeline

    mock_search = [{"title": "Web Leads Guide", "url": "https://sample.org/leads", "snippet": "Tips for conversion"}]
    mock_research_data = {
        "topic": "Why Websites Fail",
        "key_findings": ["Slow speed", "No mobile responsiveness"],
        "pain_points": ["High ad spend, zero calls"],
        "chosen_angle": "Conversion breakdown",
        "angle_reason": "Relatable to business owners",
        "sources": [{"title": "Web Leads Guide", "url": "https://sample.org/leads", "claim_supported": "Mobile issues"}],
        "uncertainties": []
    }
    mock_script_data = {
        "hooks": [
            {"type": "question", "text": "Website irundhum leads varalaya?", "reason": "Curiosity", "is_recommended": True},
            {"type": "pain-point", "text": "Ad spend waste aagudha?", "reason": "Pain", "is_recommended": False},
            {"type": "bold statement", "text": "Website create panradhu waste!", "reason": "Shock", "is_recommended": False}
        ],
        "hook": "Website irundhum leads varalaya?",
        "context": "Nariya business owners lakhs spend panraanga but inquiry varadhu.",
        "body_points": ["First speed check pannunga.", "WhatsApp CTA add pannunga."],
        "engagement": "Unga site speed check panniteengala?",
        "cta": "Free audit-ku DM pannunga!",
        "cta_options": [
            {"text": "Free audit-ku DM pannunga!", "reason": "High intent", "is_recommended": True}
        ],
        "on_screen_texts": ["No Leads?", "Check Speed", "Add CTA"],
        "caption": "Save this reel for your business! #TamilBusiness #DigitalMarketing",
        "hashtags": ["#TamilBusiness", "#DigitalMarketing"]
    }
    mock_qc_data = {
        "unsupported_claims": {"status": "PASS", "notes": "ok"},
        "repetition": {"status": "PASS", "notes": "ok"},
        "weak_cta": {"status": "PASS", "notes": "ok"},
        "unnatural_tamil": {"status": "PASS", "notes": "ok"},
        "duration_fit": {"status": "PASS", "notes": "ok"},
        "fixes_applied": []
    }

    def mock_generate_json(*args, **kwargs):
        system_prompt = kwargs.get("system_prompt", args[0] if len(args) > 0 else "")
        user_prompt = kwargs.get("user_prompt", args[1] if len(args) > 1 else "")
        if "Research" in system_prompt or "RESEARCH" in system_prompt:
            return mock_research_data
        elif "Quality" in system_prompt or "5-point" in system_prompt or "audit" in user_prompt.lower():
            return mock_qc_data
        else:
            return mock_script_data

    with patch("src.agents.research_agent.run_research_queries", return_value=mock_search), \
         patch("src.llm.LLMClient.generate_json", side_effect=mock_generate_json):

        pipeline = TamilReelScriptPipeline()
        inp = ScriptInput.create_with_defaults(
            topic="Why Websites Fail",
            duration=30,
            tone="Tanglish"
        )
        deliverable = pipeline.run(inp)

        assert deliverable.input_data.topic == "Why Websites Fail"
        assert deliverable.script.hook == "Website irundhum leads varalaya?"
        assert deliverable.script.word_count > 0
        assert len(deliverable.script.hooks) == 3
        assert deliverable.quality_check.overall_passed is True


