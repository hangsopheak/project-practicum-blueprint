from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_list_sources():
    """Verify GET /api/v1/sources returns list of recruitment sources"""
    res = client.get("/api/v1/sources")
    assert res.status_code == 200
    sources = res.json()
    assert isinstance(sources, list)
    assert len(sources) >= 10

    first = sources[0]
    for key in ["id", "name", "code", "platform_type", "url", "is_active", "scrape_interval_minutes"]:
        assert key in first

def test_filter_sources_by_platform():
    """Verify filtering sources by platform_type"""
    res_tg = client.get("/api/v1/sources?platform_type=telegram")
    assert res_tg.status_code == 200
    telegram_sources = res_tg.json()
    assert len(telegram_sources) > 0
    for s in telegram_sources:
        assert s["platform_type"] == "telegram"

    res_web = client.get("/api/v1/sources?platform_type=web_portal")
    assert res_web.status_code == 200
    web_sources = res_web.json()
    assert len(web_sources) > 0
    for s in web_sources:
        assert s["platform_type"] == "web_portal"

def test_get_source_detail_and_404():
    """Verify GET /api/v1/sources/{id} and 404 response"""
    # 1. Valid source
    res = client.get("/api/v1/sources/1")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 1
    assert data["code"] == "internships_cambodia"

    # 2. Not found
    res_404 = client.get("/api/v1/sources/99999")
    assert res_404.status_code == 404
    err = res_404.json()
    assert "error" in err or "detail" in err

def test_jobs_contain_source_id():
    """Verify that jobs returned by /api/v1/jobs include source_id"""
    res = client.get("/api/v1/jobs")
    assert res.status_code == 200
    jobs = res.json()["jobs"]
    assert len(jobs) > 0
    # Every job should have source_id key
    assert "source_id" in jobs[0]

