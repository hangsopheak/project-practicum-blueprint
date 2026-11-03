from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_skills_catalog_ep06():
    """Verify EP-06 returns normalized skills list"""
    res = client.get("/api/v1/skills")
    assert res.status_code == 200
    skills = res.json()
    assert isinstance(skills, list)
    assert len(skills) > 0
    skill_names = [s["name"] for s in skills]
    assert "Flutter" in skill_names
    assert "Dart" in skill_names

def test_job_discovery_ep07_and_ep08():
    """Verify EP-07 list & filter and EP-08 job details"""
    # 1. List jobs
    list_res = client.get("/api/v1/jobs")
    assert list_res.status_code == 200
    data = list_res.json()
    assert "total" in data
    assert "jobs" in data
    assert len(data["jobs"]) > 0

    first_job = data["jobs"][0]
    job_id = first_job["id"]
    assert "title" in first_job
    assert "company" in first_job
    assert "skills" in first_job

    # 2. Filter jobs by keyword
    search_res = client.get("/api/v1/jobs?search=Flutter")
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total"] >= 1

    # 3. Get Job Detail (EP-08)
    detail_res = client.get(f"/api/v1/jobs/{job_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["id"] == job_id
    assert "description" in detail_data
    assert "source_url" in detail_data

    # 4. Job not found (EP-08 404)
    missing_res = client.get("/api/v1/jobs/999999")
    assert missing_res.status_code == 404

def test_saved_jobs_flow_ep10_ep11_ep12():
    """Verify bookmarking lifecycle for logged-in user"""
    # 1. Login to get token
    login_res = client.post("/api/v1/auth/login", json={
        "email": "dara@example.com",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get sample job
    job_id = client.get("/api/v1/jobs").json()["jobs"][0]["id"]

    # 2. Bookmark job (EP-11)
    save_res = client.post(f"/api/v1/saved-jobs/{job_id}", headers=headers)
    assert save_res.status_code == 201

    # 3. View saved jobs (EP-10)
    list_saved = client.get("/api/v1/saved-jobs", headers=headers)
    assert list_saved.status_code == 200
    saved_list = list_saved.json()
    saved_job_ids = [item["job"]["id"] for item in saved_list]
    assert job_id in saved_job_ids

    # 4. Remove bookmark (EP-12)
    delete_res = client.delete(f"/api/v1/saved-jobs/{job_id}", headers=headers)
    assert delete_res.status_code == 200

    # 5. Verify removed
    list_after = client.get("/api/v1/saved-jobs", headers=headers)
    assert list_after.status_code == 200
    assert job_id not in [item["job"]["id"] for item in list_after.json()]
