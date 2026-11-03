import pytest
from datetime import date, timedelta
from app.core.database import SessionLocal
from app.models.models import JobListing, TelegramJob, WebJob
from app.services.dedup_manager import save_job_with_dedup, compute_dedup_hash, normalize_text_for_matching
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_test_jobs():
    """Clean up test records before and after each test."""
    db = SessionLocal()
    try:
        db.query(JobListing).filter(JobListing.company.ilike("%TestCorp%")).delete()
        db.query(TelegramJob).filter(TelegramJob.company.ilike("%TestCorp%")).delete()
        db.query(WebJob).filter(WebJob.company.ilike("%TestCorp%")).delete()
        db.commit()
    finally:
        db.close()
    yield
    db = SessionLocal()
    try:
        db.query(JobListing).filter(JobListing.company.ilike("%TestCorp%")).delete()
        db.query(TelegramJob).filter(TelegramJob.company.ilike("%TestCorp%")).delete()
        db.query(WebJob).filter(WebJob.company.ilike("%TestCorp%")).delete()
        db.commit()
    finally:
        db.close()


def test_telegram_first_then_website_merges_salary():
    """
    Test 1: Telegram first, then website with the same job
    -> 1 visible job via API, 2 total rows in job_listings, website salary merged in.
    """
    db = SessionLocal()
    try:
        # Step 1: Telegram job arrives without salary
        tg_job = {
            "title": "Flutter Developer",
            "company": "TestCorp Bank",
            "location": "Phnom Penh",
            "normalized_location": "Phnom Penh, Cambodia",
            "description": "Telegram posting text",
            "source": "Telegram",
            "source_url": "https://t.me/testcorp/101",
            "source_post_id": "101",
            "apply_telegram": "@testcorp_hr",
            "posted_at": date.today() - timedelta(days=2),
            "salary_min": None,
            "salary_max": None,
        }
        main_row, is_new, dup_of = save_job_with_dedup(db, tg_job)
        db.commit()
        assert dup_of is None
        assert main_row.salary_min is None

        # Step 2: Website job arrives with salary
        web_job = {
            "title": "Flutter Developer",
            "company": "TestCorp Bank Co., Ltd",
            "location": "Phnom Penh",
            "normalized_location": "Phnom Penh, Cambodia",
            "description": "Comprehensive BongThom announcement text for Flutter Developer position",
            "source": "BongThom",
            "source_url": "https://bongthom.com/job/testcorp-flutter-101",
            "source_post_id": "bongthom_101",
            "company_logo_url": "https://testcorp.com/logo.png",
            "salary_min": 1200.0,
            "salary_max": 2000.0,
            "posted_at": date.today() - timedelta(days=1),
        }
        second_row, is_new2, dup_of2 = save_job_with_dedup(db, web_job)
        db.commit()

        # Database checks: 2 rows stored, second is duplicate_of first
        all_rows = db.query(JobListing).filter(JobListing.company.ilike("%TestCorp%")).all()
        assert len(all_rows) == 2, f"Expected 2 rows in DB, got {len(all_rows)}"
        assert second_row.duplicate_of == main_row.id

        # Verify salary merged into main row
        db.refresh(main_row)
        assert float(main_row.salary_min) == 1200.0
        assert float(main_row.salary_max) == 2000.0
        assert main_row.company_logo_url == "https://testcorp.com/logo.png"

        # API check: GET /jobs returns only 1 visible job
        res = client.get("/api/v1/jobs?search=TestCorp")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["id"] == main_row.id
        assert data["jobs"][0]["salary_min"] == 1200.0
    finally:
        db.close()


def test_website_first_then_telegram_same_result():
    """
    Test 2: Website first, then Telegram -> same result (order independent).
    """
    db = SessionLocal()
    try:
        # Step 1: Website job arrives with salary
        web_job = {
            "title": "Flutter Developer",
            "company": "TestCorp Bank Co., Ltd",
            "location": "Phnom Penh",
            "normalized_location": "Phnom Penh, Cambodia",
            "description": "Comprehensive BongThom announcement text for Flutter Developer position",
            "source": "BongThom",
            "source_url": "https://bongthom.com/job/testcorp-flutter-202",
            "source_post_id": "bongthom_202",
            "company_logo_url": "https://testcorp.com/logo.png",
            "salary_min": 1200.0,
            "salary_max": 2000.0,
            "posted_at": date.today() - timedelta(days=3),
        }
        main_row, is_new, dup_of = save_job_with_dedup(db, web_job)
        db.commit()
        assert dup_of is None

        # Step 2: Telegram job arrives with telegram contact
        tg_job = {
            "title": "Flutter Developer",
            "company": "TestCorp Bank",
            "location": "Phnom Penh",
            "normalized_location": "Phnom Penh, Cambodia",
            "description": "Telegram posting text",
            "source": "Telegram",
            "source_url": "https://t.me/testcorp/202",
            "source_post_id": "202",
            "apply_telegram": "@testcorp_hr",
            "posted_at": date.today() - timedelta(days=1),
            "salary_min": None,
            "salary_max": None,
        }
        second_row, is_new2, dup_of2 = save_job_with_dedup(db, tg_job)
        db.commit()

        # Database checks: 2 rows stored, second is duplicate_of first
        all_rows = db.query(JobListing).filter(JobListing.company.ilike("%TestCorp%")).all()
        assert len(all_rows) == 2
        assert second_row.duplicate_of == main_row.id

        # Verify main row's contacts stay unchanged (empty) to prevent scam/phishing pollution
        db.refresh(main_row)
        assert float(main_row.salary_min) == 1200.0
        assert main_row.apply_telegram is None  # Remains unchanged!
        # Duplicate row still preserves its own contacts
        db.refresh(second_row)
        assert second_row.apply_telegram == "@testcorp_hr"

        # API check: GET /jobs returns only 1 visible job
        res = client.get("/api/v1/jobs?search=TestCorp")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["id"] == main_row.id
    finally:
        db.close()


def test_same_telegram_message_scraped_twice_results_in_one_row():
    """
    Test 3: Same Telegram message scraped twice -> 1 row (updated, not duplicated).
    """
    db = SessionLocal()
    try:
        tg_job = {
            "title": "Backend Python Engineer",
            "company": "TestCorp Tech",
            "location": "Phnom Penh",
            "source": "Telegram",
            "source_url": "https://t.me/testcorp/303",
            "source_post_id": "303",
            "posted_at": date.today(),
        }
        row1, is_new1, _ = save_job_with_dedup(db, tg_job)
        db.commit()
        assert is_new1 is True

        # Second scrape of the exact same message
        row2, is_new2, _ = save_job_with_dedup(db, tg_job)
        db.commit()
        assert is_new2 is False
        assert row1.id == row2.id

        # Total rows must be 1
        count = db.query(JobListing).filter(
            JobListing.source == "Telegram",
            JobListing.source_post_id == "303"
        ).count()
        assert count == 1
    finally:
        db.close()


def test_two_different_jobs_at_same_company_not_merged():
    """
    Test 4: Two different jobs at the same company -> NOT merged.
    """
    db = SessionLocal()
    try:
        job_dev = {
            "title": "Senior Flutter Developer",
            "company": "TestCorp Global",
            "location": "Phnom Penh",
            "source": "Website",
            "source_url": "https://testcorp.com/job/flutter-1",
            "source_post_id": "dev_1",
            "posted_at": date.today(),
        }
        job_hr = {
            "title": "Senior Accountant",
            "company": "TestCorp Global",
            "location": "Phnom Penh",
            "source": "Website",
            "source_url": "https://testcorp.com/job/accountant-1",
            "source_post_id": "acc_1",
            "posted_at": date.today(),
        }
        row1, is_new1, dup1 = save_job_with_dedup(db, job_dev)
        row2, is_new2, dup2 = save_job_with_dedup(db, job_hr)
        db.commit()

        assert dup1 is None
        assert dup2 is None
        assert row1.id != row2.id
        assert row2.duplicate_of is None

        # Both must be visible in API
        res = client.get("/api/v1/jobs?search=TestCorp")
        assert res.status_code == 200
        assert res.json()["total"] == 2
    finally:
        db.close()


def test_urgent_noise_title_matches_clean_title():
    """
    Test 5: Title "[URGENT] Mobile App Dev!!" matches "Mobile App Developer".
    """
    db = SessionLocal()
    try:
        job_clean = {
            "title": "Mobile App Developer",
            "company": "TestCorp Fintech",
            "location": "Phnom Penh",
            "source": "Website",
            "source_url": "https://testcorp.com/job/mobile-app-developer",
            "source_post_id": "fintech_1",
            "salary_min": 1500.0,
            "posted_at": date.today() - timedelta(days=2),
        }
        main_row, _, _ = save_job_with_dedup(db, job_clean)
        db.commit()

        job_urgent = {
            "title": "[URGENT] Mobile App Dev!!",
            "company": "TestCorp Fintech",
            "location": "Phnom Penh",
            "source": "Telegram",
            "source_url": "https://t.me/testcorp/urgent-app-dev",
            "source_post_id": "tg_urgent_1",
            "posted_at": date.today(),
        }
        second_row, is_new, dup_of = save_job_with_dedup(db, job_urgent)
        db.commit()

        # Must be detected as duplicate of main_row
        assert dup_of == main_row.id
        assert second_row.duplicate_of == main_row.id

        # Only 1 job visible in the API
        res = client.get("/api/v1/jobs?search=TestCorp")
        assert res.status_code == 200
        assert res.json()["total"] == 1
    finally:
        db.close()


def test_last_seen_at_updated_on_rescrape():
    """
    Test 6: Always update last_seen_at on re-scrape, even when nothing else changes.
    """
    from datetime import datetime, timezone
    import time

    db = SessionLocal()
    try:
        job = {
            "title": "DevOps Engineer",
            "company": "TestCorp Cloud",
            "location": "Phnom Penh",
            "source": "Telegram",
            "source_url": "https://t.me/testcorp/devops-1",
            "source_post_id": "devops_1",
            "posted_at": date.today(),
        }
        row, _, _ = save_job_with_dedup(db, job)
        db.commit()

        initial_seen = row.last_seen_at
        time.sleep(0.05)

        # Re-scrape exact same job
        row2, is_new, _ = save_job_with_dedup(db, job)
        db.commit()
        db.refresh(row)

        assert is_new is False
        assert row.last_seen_at > initial_seen
    finally:
        db.close()


def test_since_filter_in_list_jobs():
    """
    Test 7: since= filter in GET /api/v1/jobs returns only jobs created/updated since timestamp.
    """
    from datetime import datetime, timezone
    db = SessionLocal()
    try:
        # Create a job with past created_at
        job_old = JobListing(
            title="Old Job",
            company="TestCorp Old",
            location="Phnom Penh",
            description="Old listing",
            source="Test",
            source_url="https://testcorp.com/old-job-1",
            created_at=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            is_active=True
        )
        job_new = JobListing(
            title="New Job",
            company="TestCorp New",
            location="Phnom Penh",
            description="New listing",
            source="Test",
            source_url="https://testcorp.com/new-job-1",
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        db.add(job_old)
        db.add(job_new)
        db.commit()

        # Query since yesterday
        yesterday_iso = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        res = client.get(f"/api/v1/jobs?search=TestCorp&since={yesterday_iso}")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        assert data["jobs"][0]["title"] == "New Job"
    finally:
        db.close()


def test_fake_post_different_contact_does_not_pollute_real_job():
    """
    Test 8: A fake/phishing post with the same title/company but a different contact
    does NOT overwrite or pollute the real job's contacts.
    """
    db = SessionLocal()
    try:
        real_job = {
            "title": "Senior Mobile Developer",
            "company": "TestCorp Official",
            "location": "Phnom Penh",
            "source": "Website",
            "source_url": "https://testcorp.com/careers/mobile-dev",
            "source_post_id": "official_1",
            "apply_email": "careers@testcorp.com",
            "apply_phone": "+85512345678",
            "posted_at": date.today() - timedelta(days=2),
        }
        main_row, _, _ = save_job_with_dedup(db, real_job)
        db.commit()

        fake_phishing_job = {
            "title": "Senior Mobile Developer",
            "company": "TestCorp Official",
            "location": "Phnom Penh",
            "source": "Telegram",
            "source_url": "https://t.me/scamchannel/999",
            "source_post_id": "scam_999",
            "apply_email": "scammer@fake-mail.com",
            "apply_phone": "+85599999999",
            "apply_telegram": "@phishing_scammer",
            "posted_at": date.today(),
        }
        dup_row, is_new, dup_of = save_job_with_dedup(db, fake_phishing_job)
        db.commit()

        # The fake post is linked as duplicate_of main_row
        assert dup_of == main_row.id

        # The real job's contacts MUST remain 100% authentic and unpolluted!
        db.refresh(main_row)
        assert main_row.apply_email == "careers@testcorp.com"
        assert main_row.apply_phone == "+85512345678"
        assert main_row.apply_telegram is None  # Not polluted by the duplicate!

        # The duplicate row still stores the scammer info for audit/investigation
        db.refresh(dup_row)
        assert dup_row.apply_email == "scammer@fake-mail.com"
        assert dup_row.apply_telegram == "@phishing_scammer"
    finally:
        db.close()

