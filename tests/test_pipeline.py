"""Unit and integration tests for Tamil Reel Script Agent components."""

import json
from pathlib import Path
import pytest
from src.models import (
    ScriptDraft,
    ScriptInput,
    ResearchResult,
    QualityCheckResult,
    CheckItem,
    FullDeliverable,
    SourceItem,
)
from src.llm import clean_json_response
from src.search_tool import search_web


def test_word_count_calculation():
    """Confirms bullet numbers ('1. ', '2. ') and punctuation do not inflate spoken word counts."""
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
    count = draft.calculate_word_count()
    # Ensure count is positive and does not count "1.", "2.", "3."
    assert count > 0
    # Expected words: 7 (hook) + 5 (context) + 4+5+4 (body without numbers) + 4 (engage) + 4 (cta) = 33
    assert count <= 35


def test_clean_json_response():
    """Tests non-greedy code fence extraction and handling of surrounding conversational text."""
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


def test_deliverable_serialization(tmp_path: Path):
    """Verifies .save_deliverables() and .load_from_json() round-trip fidelity."""
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
        context="Test Context",
        body_points=["Test point"],
        engagement="Test question?",
        cta="DM us",
        word_count=65,
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

    # Round-trip load from JSON
    loaded = FullDeliverable.load_from_json(out_base.with_suffix(".json"))
    assert loaded.input_data.topic == "Test Topic Leads"
    assert loaded.script.hook == "Test Hook"
    assert loaded.research.sources[0].url == "https://example.com/test"


def test_search_tool_handles_failures():
    """Confirms search tool returns empty list instead of invented URLs on error."""
    # Searching with empty or invalid query handled safely
    results = search_web("   ")
    assert isinstance(results, list)
    # Ensure never contains the fake url
    for r in results:
        assert r.get("url") != "https://official.info/verify"


def test_fastapi_health_endpoint():
    """Verify FastAPI health endpoint responds correctly."""
    from fastapi.testclient import TestClient
    from api import app

    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "active_provider" in data


def test_fastapi_generate_endpoint():
    """Verify script generation via FastAPI endpoint."""
    from fastapi.testclient import TestClient
    from api import app

    client = TestClient(app)
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

