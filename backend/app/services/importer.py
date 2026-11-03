"""
backend/app/services/importer.py
================================
Production-quality JSON Ingestion and Normalization Pipeline for JobMatch.

Integrates POC JSON datasets (e.g. jobs_all.json, BongThom, JobNet, Khmer24,
CamboJob, Workingna, AseanWorks, PPHR, etc.) into the PostgreSQL database.

Features:
- Handles nested schema structures: position, salary, insights, requirements.
- Standardizes location, salary, job type, and experience level.
- Automatically maps and tags skills from the master skills catalog.
- Idempotent upsert based on canonical source_url.
- Full statistics reporting: read, inserted, updated, skipped, failed.
- Safe dry-run mode.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from datetime import datetime, date, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from app.models.models import JobListing, Skill, JobSkill
from app.services.job_classifier import classify_job

logger = logging.getLogger(__name__)

DATE_FORMATS = [
    "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y",
    "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y",
]

CHINESE_LOCATION_MAP = {
    "柬埔寨": "Cambodia",
    "金边": "Phnom Penh",
    "西港": "Sihanoukville",
    "暹粒": "Siem Reap",
    "马德望": "Battambang",
    "干拉": "Kandal",
}

def parse_safe_date(val: Any) -> Optional[date]:
    """Parse string to date safely without raising exceptions."""
    if not val:
        return None
    if isinstance(val, (datetime, date)):
        return val if isinstance(val, date) else val.date()
    val_str = re.sub(r"\s+", " ", str(val)).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            pass
    # Try ISO substring
    if len(val_str) >= 10:
        try:
            return datetime.fromisoformat(val_str[:10]).date()
        except Exception:
            pass
    return None

def normalize_location(loc_raw: Optional[str]) -> str:
    """Standardize location string and handle translations."""
    if not loc_raw:
        return "Phnom Penh"
    loc = str(loc_raw).strip()
    for ch, en in CHINESE_LOCATION_MAP.items():
        loc = loc.replace(ch, en)
    # Common standardizations
    if "phnom penh" in loc.lower():
        return "Phnom Penh"
    if "siem reap" in loc.lower():
        return "Siem Reap"
    if "sihanouk" in loc.lower():
        return "Sihanoukville"
    return loc[:250].strip() or "Phnom Penh"

def normalize_company(comp_raw: Optional[str]) -> str:
    """Clean and constrain company name."""
    if not comp_raw:
        return "Confidential / Hiring Organization"
    comp = str(comp_raw).strip().replace("\n", " ")
    comp = re.sub(r"\s+", " ", comp)
    return comp[:250] or "Confidential / Hiring Organization"

def normalize_title(title_raw: Optional[str]) -> str:
    """Clean title string."""
    if not title_raw:
        return "Untitled Position"
    t = str(title_raw).strip().replace("\n", " ")
    t = re.sub(r"\s+", " ", t)
    return t[:200]

def normalize_job_type(job_type_raw: Optional[str], text_context: str = "") -> str:
    """Determine standardized job type (snake_case values)."""
    combined = f"{job_type_raw or ''} {text_context}".lower()
    if "intern" in combined:
        return "internship"
    if "part" in combined and "time" in combined:
        return "part_time"
    if "contract" in combined or "temporary" in combined:
        return "contract"
    if "freelance" in combined:
        return "freelance"
    return "full_time"

def normalize_experience_level(level_raw: Optional[str], seniority_raw: Optional[str], title: str = "") -> str:
    """Determine standardized experience level."""
    combined = f"{level_raw or ''} {seniority_raw or ''} {title}".lower()
    if "intern" in combined or "student" in combined or "fresh" in combined or "entry" in combined:
        return "entry"
    if "junior" in combined:
        return "junior"
    if "senior" in combined or "lead" in combined or "principal" in combined:
        return "senior"
    if "manager" in combined or "director" in combined or "head" in combined:
        return "manager"
    if "mid" in combined:
        return "mid"
    return "entry"

def normalize_source_name(source_raw: Optional[str], url: str = "") -> str:
    """Return a clean standardized source name."""
    if source_raw:
        s = str(source_raw).strip()
        s_lower = s.lower()
        if "telegram" in s_lower:
            return "Telegram"
        if "bongthom" in s_lower:
            return "BongThom"
        if "jobnet" in s_lower:
            return "JobNet"
        if "khmer24" in s_lower:
            return "Khmer24"
        if "cambojob" in s_lower:
            return "CamboJob"
        if "workingna" in s_lower:
            return "Workingna"
        if "asean" in s_lower:
            return "AseanWorks"
        if "forval" in s_lower:
            return "Forval"
        if "pp-hr" in s_lower or "pphr" in s_lower:
            return "PPHR"
        if "khmeronline" in s_lower:
            return "KhmerOnlineJobs"
        return s[:50]
    # Infer from URL
    u_lower = url.lower()
    if "t.me" in u_lower:
        return "Telegram"
    if "bongthom" in u_lower:
        return "BongThom"
    if "jobnet" in u_lower:
        return "JobNet"
    if "khmer24" in u_lower:
        return "Khmer24"
    if "cambojob" in u_lower:
        return "CamboJob"
    return "Web Aggregator"

def extract_and_link_skills(db: Session, job_id: int, text_content: str, catalog_skills: List[Skill]) -> int:
    """Match skills against master catalog and create JobSkill associations."""
    text_lower = text_content.lower()
    matched_count = 0
    for skill in catalog_skills:
        pattern = r'\b' + re.escape(skill.name.lower()) + r'\b'
        if re.search(pattern, text_lower):
            db.add(JobSkill(job_id=job_id, skill_id=skill.id))
            matched_count += 1
    return matched_count


def import_jobs_from_records(
    db: Session,
    records: List[Dict[str, Any]],
    source_label: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Ingests a list of raw job dicts into PostgreSQL with deduplication and normalization.
    """
    catalog_skills = db.query(Skill).all()
    stats = {
        "source": source_label or "multiple",
        "total_read": len(records),
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
    }

    for item in records:
        try:
            raw_url = item.get("application_url") or item.get("source_url") or item.get("url")
            raw_title = item.get("title")

            if not raw_url or not raw_title:
                stats["skipped"] += 1
                continue

            clean_url = str(raw_url).strip()
            clean_title = normalize_title(raw_title)

            # Location
            loc_val = item.get("location")
            location = normalize_location(loc_val)

            # Company
            comp_val = item.get("company")
            company = normalize_company(comp_val)

            # Description and Requirements
            desc_val = item.get("description") or ""
            reqs = item.get("requirements") or []
            if isinstance(reqs, list):
                reqs_text = "\n".join(str(r) for r in reqs)
            else:
                reqs_text = str(reqs)
            
            full_description = desc_val
            if reqs_text and reqs_text not in full_description:
                full_description = f"{full_description}\n\nRequirements:\n{reqs_text}"
            full_description = full_description.strip() or f"{clean_title} at {company}"

            # Dates
            posted_date = parse_safe_date(item.get("posted_date") or item.get("posted_at") or item.get("scraped_at"))
            deadline_date = parse_safe_date(item.get("deadline"))

            # Salary extraction
            salary_data = item.get("salary")
            salary_min = None
            salary_max = None
            is_negotiable = False
            salary_currency = "USD"

            if isinstance(salary_data, dict):
                try:
                    s_min = salary_data.get("min")
                    if s_min is not None and str(s_min).replace(".", "", 1).isdigit():
                        salary_min = float(s_min)
                except Exception:
                    pass
                try:
                    s_max = salary_data.get("max")
                    if s_max is not None and str(s_max).replace(".", "", 1).isdigit():
                        salary_max = float(s_max)
                except Exception:
                    pass
                is_negotiable = bool(salary_data.get("negotiable", False))
                salary_currency = str(salary_data.get("currency") or "USD")[:10]
            elif isinstance(salary_data, str):
                if "negotiable" in salary_data.lower():
                    is_negotiable = True

            # Job type & level
            insights = item.get("insights") or {}
            pos_info = item.get("position") or {}
            job_type = normalize_job_type(
                insights.get("job_type") or item.get("job_type"),
                text_context=f"{clean_title} {full_description}"
            )
            experience_level = normalize_experience_level(
                pos_info.get("level"),
                insights.get("seniority"),
                title=clean_title
            )

            # Work arrangement (on-site | hybrid | remote)
            work_arr_raw = (
                item.get("work_arrangement")
                or item.get("work_type")
                or item.get("remote")
            )
            work_arrangement = None
            if work_arr_raw:
                wa = str(work_arr_raw).lower().strip()
                if "remote" in wa:
                    work_arrangement = "remote"
                elif "hybrid" in wa:
                    work_arrangement = "hybrid"
                elif "on-site" in wa or "onsite" in wa or "office" in wa:
                    work_arrangement = "on-site"
                else:
                    work_arrangement = str(work_arr_raw)[:50]

            # Application URL (direct apply link, may differ from source_url)
            application_url = str(item.get("application_url") or "").strip() or None

            # Company URL (company website)
            company_url = str(item.get("company_url") or item.get("company_website") or "").strip() or None

            # Company Logo URL
            company_logo_url = str(item.get("company_logo_url") or item.get("company_logo") or item.get("logo") or "").strip() or None

            # Raw uncleaned title
            raw_title_val = str(raw_title).strip()[:255] if raw_title else clean_title

            # Normalized location
            normalized_location = location if "Cambodia" in location else f"{location}, Cambodia"

            # Openings / Vacancy count
            openings_val = 1
            raw_openings = item.get("openings") or item.get("vacancy_count") or item.get("vacancies")
            if raw_openings is not None:
                try:
                    openings_val = max(1, int(raw_openings))
                except Exception:
                    openings_val = 1

            # Source post external ID
            source_post_id = str(item.get("source_post_id") or item.get("post_id") or item.get("job_id") or "").strip() or None
            if not source_post_id and clean_url:
                # Infer from URL ending
                url_slug = clean_url.rstrip("/").split("/")[-1].split("?")[0]
                if len(url_slug) < 100:
                    source_post_id = url_slug

            # Salary period (monthly | yearly | hourly | daily)
            salary_period_raw = (
                item.get("salary_period")
                or item.get("pay_period")
                or (salary_data.get("period") if isinstance(salary_data, dict) else None)
            )
            salary_period = "monthly"  # safe default
            if salary_period_raw:
                sp = str(salary_period_raw).lower()
                if "year" in sp or "annual" in sp:
                    salary_period = "yearly"
                elif "hour" in sp:
                    salary_period = "hourly"
                elif "day" in sp or "daily" in sp:
                    salary_period = "daily"
                else:
                    salary_period = "monthly"

            # Dedup hash — SHA-256 of normalized title|company|location (more collision-resistant)
            dedup_raw = f"{clean_title.lower()}|{company.lower()}|{location.lower()}"
            dedup_hash = hashlib.sha256(dedup_raw.encode("utf-8")).hexdigest()[:64]

            # Scraped timestamp
            now_utc = datetime.now(timezone.utc)

            # Source name
            source_name = normalize_source_name(item.get("source") or source_label, clean_url)

            # Check existing for idempotency / deduplication
            existing = db.query(JobListing).filter(JobListing.source_url == clean_url).first()

            if dry_run:
                if existing:
                    stats["updated"] += 1
                else:
                    stats["inserted"] += 1
                continue

            # Run structured classification (Jev with rule-based fallback)
            classification = classify_job(
                title=clean_title,
                description=full_description,
                company=company,
                existing_work_arrangement=work_arrangement
            )
            job_category_val = classification.get("job_category", "Unknown")
            job_subcategory_val = classification.get("job_subcategory", "Unknown")
            job_level_val = classification.get("job_level", "Unknown")
            class_conf_val = classification.get("classification_confidence")
            class_source_val = classification.get("classification_source", "rule")
            if not work_arrangement and classification.get("work_arrangement") != "Unknown":
                work_arrangement = classification.get("work_arrangement")

            if existing:
                # Update existing record
                existing.title = clean_title
                existing.company = company
                existing.location = location
                existing.description = full_description
                existing.job_type = job_type
                existing.experience_level = experience_level
                existing.job_category = job_category_val
                existing.job_subcategory = job_subcategory_val
                existing.job_level = job_level_val
                existing.classification_confidence = class_conf_val
                existing.classification_source = class_source_val
                if salary_min is not None:
                    existing.salary_min = salary_min
                if salary_max is not None:
                    existing.salary_max = salary_max
                existing.is_negotiable = is_negotiable
                if posted_date:
                    existing.posted_at = posted_date
                if deadline_date:
                    existing.deadline = deadline_date
                existing.is_active = True
                existing.status = "active"
                existing.scraped_at = now_utc
                existing.dedup_hash = dedup_hash
                existing.salary_period = salary_period
                if work_arrangement:
                    existing.work_arrangement = work_arrangement
                if application_url:
                    existing.application_url = application_url
                if company_url:
                    existing.company_url = company_url
                if company_logo_url:
                    existing.company_logo_url = company_logo_url
                existing.raw_title = raw_title_val
                existing.normalized_location = normalized_location
                existing.openings = openings_val
                if source_post_id:
                    existing.source_post_id = source_post_id

                # Refresh linked skills
                db.query(JobSkill).filter(JobSkill.job_id == existing.id).delete()
                extract_and_link_skills(db, existing.id, f"{clean_title} {full_description}", catalog_skills)
                stats["updated"] += 1
            else:
                # Insert new record
                new_job = JobListing(
                    title=clean_title,
                    raw_title=raw_title_val,
                    company=company,
                    company_logo_url=company_logo_url,
                    location=location,
                    normalized_location=normalized_location,
                    experience_level=experience_level,
                    job_type=job_type,
                    job_category=job_category_val,
                    job_subcategory=job_subcategory_val,
                    job_level=job_level_val,
                    classification_confidence=class_conf_val,
                    classification_source=class_source_val,
                    openings=openings_val,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency=salary_currency,
                    salary_period=salary_period,
                    is_negotiable=is_negotiable,
                    description=full_description,
                    source=source_name,
                    source_url=clean_url,
                    source_post_id=source_post_id,
                    company_url=company_url,
                    posted_at=posted_date,
                    deadline=deadline_date,
                    work_arrangement=work_arrangement,
                    application_url=application_url,
                    scraped_at=now_utc,
                    status="active",
                    dedup_hash=dedup_hash,
                    is_active=True
                )
                db.add(new_job)
                db.flush()

                # Link matching skills
                extract_and_link_skills(db, new_job.id, f"{clean_title} {full_description}", catalog_skills)
                stats["inserted"] += 1

        except Exception as exc:
            logger.error("Error processing job record %s: %s", item.get("application_url"), exc)
            stats["failed"] += 1

    if not dry_run:
        db.commit()

    return stats


def import_from_json_file(db: Session, filepath: str, dry_run: bool = False) -> Dict[str, Any]:
    """Load JSON file and run batch import."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"JSON file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        records = data.get("jobs", [])
    elif isinstance(data, list):
        records = data
    else:
        records = []

    filename = os.path.basename(filepath)
    source_name = filename.replace(".json", "").replace("_com", "").replace("_kh", "")
    return import_jobs_from_records(db, records, source_label=source_name, dry_run=dry_run)
