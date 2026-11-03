import pytest
from unittest.mock import patch, MagicMock
from app.services.job_classifier import rule_based_classify, classify_job
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_rule_based_classify_it_flutter():
    """Verify local classifier correctly identifies IT Flutter roles"""
    res = rule_based_classify(
        title="Junior Flutter Developer",
        description="We are seeking a junior mobile developer with Dart, Flutter and Firebase experience in Phnom Penh.",
        company="ABC Tech"
    )
    assert res["job_category"] == "Information Technology"
    assert res["job_subcategory"] == "Mobile Development"
    assert res["job_level"] == "Junior"
    assert res["classification_source"] == "rule"

def test_rule_based_classify_finance_and_remote():
    """Verify local classifier identifies Finance and Remote work arrangement"""
    res = rule_based_classify(
        title="Senior Accountant",
        description="Responsible for monthly tax reports, auditing, and financial statements. Fully remote / work from home.",
        company="Phnom Penh Holdings"
    )
    assert res["job_category"] == "Finance & Accounting"
    assert res["job_level"] == "Senior"
    assert res["work_arrangement"] == "Remote"

def test_rule_based_classify_unknown_fallback():
    """Verify unclassifiable text returns Unknown gracefully without throwing"""
    res = rule_based_classify(
        title="General Vacancy",
        description="Please contact office for details.",
        company="Local Shop"
    )
    assert res["job_category"] == "Unknown"
    assert res["job_level"] == "Unknown"

def test_classify_job_without_api_key_uses_fallback():
    """Verify classify_job runs rule-based fallback when JEV_API_KEY is unset"""
    with patch("app.services.job_classifier.JEV_API_KEY", ""):
        res = classify_job(
            title="Frontend React Developer",
            description="Looking for mid-level engineer skilled in React and TypeScript."
        )
        assert res["classification_source"] == "rule"
        assert res["job_category"] == "Information Technology"
        assert res["job_subcategory"] == "Frontend Development"

def test_classify_job_with_mocked_jev_success():
    """Verify classify_job parses Jev Choice responses with confidence >= threshold"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "model": "jev-latest",
        "answers": {
            "job_category": {
                "type": "choice",
                "choice": "Information Technology",
                "confidence": 0.95
            },
            "job_level": {
                "type": "choice",
                "choice": "Junior",
                "confidence": 0.90
            },
            "job_subcategory": {
                "type": "choice",
                "choice": "Mobile Development",
                "confidence": 0.88
            },
            "work_arrangement": {
                "type": "choice",
                "choice": "On-site",
                "confidence": 0.92
            }
        }
    }

    with patch("app.services.job_classifier.JEV_API_KEY", "mock-jev-key-123"):
        with patch("requests.post", return_value=mock_response):
            res = classify_job(
                title="Junior Flutter Developer",
                description="Flutter app developer needed."
            )
            assert res["classification_source"] == "jev"
            assert res["job_category"] == "Information Technology"
            assert res["job_subcategory"] == "Mobile Development"
            assert res["job_level"] == "Junior"
            assert res["classification_confidence"] >= 0.65

def test_classify_job_with_mocked_jev_low_confidence_fallback():
    """Verify low confidence results trigger rule-based fallback"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "model": "jev-latest",
        "answers": {
            "job_category": {
                "type": "choice",
                "choice": "Information Technology",
                "confidence": 0.30  # Low confidence
            },
            "job_level": {
                "type": "choice",
                "choice": "Unknown",
                "confidence": 0.20
            }
        }
    }

    with patch("app.services.job_classifier.JEV_API_KEY", "mock-jev-key-123"):
        with patch("requests.post", return_value=mock_response):
            res = classify_job(
                title="Junior Flutter Developer",
                description="Flutter mobile work."
            )
            # Should fall back to rule
            assert res["classification_source"] == "rule"
            assert res["job_category"] == "Information Technology"

def test_classify_job_api_error_fallback():
    """Verify network or HTTP failure falls back to rule without crashing"""
    with patch("app.services.job_classifier.JEV_API_KEY", "mock-jev-key-123"):
        with patch("requests.post", side_effect=Exception("API Connection Refused")):
            res = classify_job(
                title="Marketing Specialist",
                description="Social media campaigns and digital marketing."
            )
            assert res["classification_source"] == "rule"
            assert res["job_category"] == "Marketing"

def test_api_jobs_includes_classification_fields():
    """Verify GET /api/v1/jobs returns classification attributes"""
    res = client.get("/api/v1/jobs?limit=5")
    assert res.status_code == 200
    data = res.json()
    jobs = data["jobs"]
    assert len(jobs) > 0
    first = jobs[0]
    for key in ["job_category", "job_subcategory", "job_level", "classification_source"]:
        assert key in first

