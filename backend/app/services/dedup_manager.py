"""
backend/app/services/dedup_manager.py
=====================================
Enterprise Cross-Source Duplicate Handling & Job Merge Pipeline.

Implements order-independent deduplication across Telegram and Web job sources:
- 3-tier matching:
    1. Exact SHA-256 dedup_hash
    2. Same apply contact (email/phone/telegram) + title similarity >= 80
    3. Same company + title similarity >= 90 (rapidfuzz) posted within last 30 days
- Order-independent field merging:
    - Fill only empty fields in the main job (salary, logo, contacts, deadline)
    - posted_at = earliest date
    - description = longer text
    - duplicate row saved with duplicate_of = main.id
- Always updates last_seen_at
"""

import hashlib
import re
from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from rapidfuzz import fuzz

from app.models.models import JobListing, Skill, JobSkill

SOURCE_PRIORITY = {
    "website": 2,
    "web": 2,
    "bongthom": 2,
    "jobnet": 2,
    "cambojob": 2,
    "khmer24": 2,
    "telegram": 1,
}


def normalize_text_for_matching(text: Optional[str]) -> str:
    """Lowercase, trim, collapse whitespace, and strip common noise words and emojis."""
    if not text:
        return ""
    # Strip emojis and punctuation noise
    s = re.sub(r'[\[\]\(\)‼️🔴🟢🟡⚡💼📢📣🔔⭐🌟✨🎯💡🚀!]', ' ', str(text))
    # Strip common recruitment prefix noise
    s = re.sub(r'^\s*(?:urgent|hiring|immediate|announcement|we\s+are\s+looking\s+for|vacancy|hot\s*job)\s*[:\-–\s]*', '', s, flags=re.IGNORECASE)
    # Strip site name suffixes (e.g. " - BongThom", " | JobNet")
    s = re.sub(r'\s*[-|–]\s*(?:BongThom|JobNet|CamboJob|Khmer24|Telegram|Careers|Jobs).*$', '', s, flags=re.IGNORECASE)
    # Standardize common tech job abbreviations
    s = re.sub(r'\bdevs?\b', 'developer', s, flags=re.IGNORECASE)
    s = re.sub(r'\bsr\.?\b', 'senior', s, flags=re.IGNORECASE)
    s = re.sub(r'\bjr\.?\b', 'junior', s, flags=re.IGNORECASE)
    s = re.sub(r'\beng\.?\b', 'engineer', s, flags=re.IGNORECASE)
    s = re.sub(r'\bmgr\.?\b', 'manager', s, flags=re.IGNORECASE)
    # Collapse multiple spaces
    s = re.sub(r'\s+', ' ', s).strip().lower()
    return s


def normalize_company_name(comp: Optional[str]) -> str:
    """Strip business suffixes and recruitment phrases from company name."""
    if not comp:
        return ""
    c = normalize_text_for_matching(comp)
    c = re.sub(r'\s*(?:is\s+seeking|is\s+looking\s+for|looking\s+for|needs|is\s+hiring|company:|employer:).*$', '', c, flags=re.IGNORECASE)
    c = re.sub(r'\b(?:co\.?,?\s*ltd|plc|bank\s+plc|inc\.|corp\.?|llc|group)\b', '', c, flags=re.IGNORECASE)
    c = re.sub(r'\s+', ' ', c).strip()
    return c


def compute_dedup_hash(title: str, company: str, location: str) -> str:
    """
    SHA-256 of normalized title|company|location.
    Never hash an empty string.
    """
    t = normalize_text_for_matching(title)
    c = normalize_company_name(company)
    l = normalize_text_for_matching(re.sub(r',?\s*cambodia', '', (location or '').lower()))
    
    key = f"{t}|{c}|{l}"
    if not key.replace("|", "").strip():
        # Fallback to avoid hashing empty
        key = f"{title.strip().lower()}|{company.strip().lower()}|{location.strip().lower()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:64]


def find_matching_main_job(
    db: Session,
    title: str,
    company: str,
    location: str,
    dedup_hash: str,
    apply_email: Optional[str] = None,
    apply_phone: Optional[str] = None,
    apply_telegram: Optional[str] = None,
    posted_at: Optional[date] = None
) -> Optional[JobListing]:
    """
    Look for an existing main job (duplicate_of IS NULL and is_active = True),
    in strict order:
      1. Same dedup_hash
      2. Same contact (apply_email, apply_phone, apply_telegram) AND title similarity >= 80
      3. Same company AND title similarity >= 90 (rapidfuzz), posted within last 30 days
    """
    # 1. Exact dedup_hash match (main job only)
    main_by_hash = db.query(JobListing).filter(
        JobListing.duplicate_of.is_(None),
        JobListing.is_active == True,
        JobListing.dedup_hash == dedup_hash
    ).first()
    if main_by_hash:
        return main_by_hash

    norm_title = normalize_text_for_matching(title)

    # 2. Same contact + title similarity >= 80%
    contact_candidates = []
    if apply_email and len(apply_email) > 4:
        contact_candidates.extend(
            db.query(JobListing).filter(
                JobListing.duplicate_of.is_(None),
                JobListing.is_active == True,
                JobListing.apply_email == apply_email
            ).all()
        )
    if apply_phone and len(apply_phone) > 5:
        contact_candidates.extend(
            db.query(JobListing).filter(
                JobListing.duplicate_of.is_(None),
                JobListing.is_active == True,
                JobListing.apply_phone == apply_phone
            ).all()
        )
    if apply_telegram and len(apply_telegram) > 3:
        contact_candidates.extend(
            db.query(JobListing).filter(
                JobListing.duplicate_of.is_(None),
                JobListing.is_active == True,
                JobListing.apply_telegram == apply_telegram
            ).all()
        )

    for cand in contact_candidates:
        cand_title_norm = normalize_text_for_matching(cand.title)
        ratio = fuzz.token_sort_ratio(cand_title_norm, norm_title)
        if ratio >= 80:
            return cand

    # 3. Same company + title similarity >= 90% (posted within 30 days)
    norm_comp = normalize_company_name(company)
    if norm_comp and len(norm_comp) >= 3:
        cutoff = date.today() - timedelta(days=30)
        company_candidates = db.query(JobListing).filter(
            JobListing.duplicate_of.is_(None),
            JobListing.is_active == True,
            or_(
                JobListing.company.ilike(f"%{norm_comp}%"),
                JobListing.company == company
            )
        ).all()

        for cand in company_candidates:
            # Check date within 30 days if posted_at available
            if cand.posted_at and cand.posted_at < cutoff:
                continue

            cand_title_norm = normalize_text_for_matching(cand.title)
            ratio = fuzz.token_sort_ratio(cand_title_norm, norm_title)
            if ratio >= 90:
                return cand

    return None


def merge_into_main_job(
    db: Session,
    main_job: JobListing,
    incoming: Dict[str, Any]
) -> None:
    """
    Merge incoming job fields into main_job:
    - Fill only EMPTY fields (salary, deadline, apply_*, description, company_logo_url, skills)
    - posted_at = earliest date
    - description = longer one
    - Always update last_seen_at
    """
    now_utc = datetime.now(timezone.utc)
    main_job.last_seen_at = now_utc
    main_job.is_active = True

    # Salary: fill if empty in main
    if main_job.salary_min is None and incoming.get("salary_min") is not None:
        main_job.salary_min = incoming["salary_min"]
        main_job.salary_max = incoming.get("salary_max")
        main_job.salary_currency = incoming.get("salary_currency", "USD")
        main_job.salary_period = incoming.get("salary_period", "monthly")
        main_job.is_negotiable = bool(incoming.get("is_negotiable", False))
    elif main_job.salary_max is None and incoming.get("salary_max") is not None:
        main_job.salary_max = incoming["salary_max"]

    # Company logo & URL
    if not main_job.company_logo_url and incoming.get("company_logo_url"):
        main_job.company_logo_url = incoming["company_logo_url"]
    if not main_job.company_url and incoming.get("company_url"):
        main_job.company_url = incoming["company_url"]

    # Note: Contact info (apply_email, apply_phone, apply_telegram, application_url)
    # is intentionally NOT copied from duplicates to protect the main job from phishing/scams.

    # Work arrangement & openings
    if not main_job.work_arrangement and incoming.get("work_arrangement"):
        main_job.work_arrangement = incoming["work_arrangement"]
    if (not main_job.openings or main_job.openings <= 1) and incoming.get("openings"):
        main_job.openings = incoming["openings"]

    # Deadline: fill if empty
    if not main_job.deadline and incoming.get("deadline"):
        main_job.deadline = incoming["deadline"]

    # posted_at: keep earliest date
    inc_posted = incoming.get("posted_at")
    if inc_posted:
        if main_job.posted_at:
            if inc_posted < main_job.posted_at:
                main_job.posted_at = inc_posted
        else:
            main_job.posted_at = inc_posted

    # Description: keep the longer, more informative description
    inc_desc = incoming.get("description") or ""
    if len(inc_desc) > len(main_job.description or ""):
        main_job.description = inc_desc

    # Skills: sync any new skills from incoming job
    inc_skills = incoming.get("skills") or []
    existing_skill_ids = {js.skill_id for js in main_job.skills}
    for sk in inc_skills:
        skill_obj = db.query(Skill).filter(Skill.name.ilike(sk.strip())).first()
        if skill_obj and skill_obj.id not in existing_skill_ids:
            db.add(JobSkill(job_id=main_job.id, skill_id=skill_obj.id))
            existing_skill_ids.add(skill_obj.id)


def save_job_with_dedup(
    db: Session,
    job_data: Dict[str, Any]
) -> Tuple[JobListing, bool, Optional[int]]:
    """
    Save or update a job record following the professional duplicate handling specification.
    Returns: (target_job, is_new_record, duplicate_of_id)
    """
    source = job_data.get("source") or "Web"
    source_post_id = job_data.get("source_post_id")
    source_url = job_data.get("source_url") or ""
    now_utc = datetime.now(timezone.utc)

    # 1. Check if EXACT same post already exists under (source, source_post_id) or source_url
    exact_existing = None
    if source and source_post_id:
        exact_existing = db.query(JobListing).filter(
            JobListing.source == source,
            JobListing.source_post_id == str(source_post_id)
        ).first()

    if not exact_existing and source_url:
        exact_existing = db.query(JobListing).filter(
            JobListing.source_url == source_url
        ).first()

    if exact_existing:
        # Just update last_seen_at and refreshed fields
        exact_existing.last_seen_at = now_utc
        exact_existing.is_active = True
        return exact_existing, False, exact_existing.duplicate_of

    # 2. Compute dedup_hash
    title = job_data.get("title") or "Untitled Job"
    company = job_data.get("company") or "Hiring Organization"
    location = job_data.get("normalized_location") or job_data.get("location") or "Phnom Penh"
    dedup_hash = compute_dedup_hash(title, company, location)

    # 3. Look for a matching main job (duplicate_of IS NULL)
    main_match = find_matching_main_job(
        db=db,
        title=title,
        company=company,
        location=location,
        dedup_hash=dedup_hash,
        apply_email=job_data.get("apply_email"),
        apply_phone=job_data.get("apply_phone"),
        apply_telegram=job_data.get("apply_telegram"),
        posted_at=job_data.get("posted_at")
    )

    duplicate_of_id = None
    if main_match:
        # Match found: link this new record as a duplicate of main_match
        duplicate_of_id = main_match.id
        merge_into_main_job(db=db, main_job=main_match, incoming=job_data)

    # 4. Insert new record
    new_job = JobListing(
        title=title,
        raw_title=job_data.get("raw_title") or title,
        company=company,
        company_url=job_data.get("company_url"),
        company_logo_url=job_data.get("company_logo_url"),
        location=job_data.get("location") or "Phnom Penh",
        normalized_location=job_data.get("normalized_location") or "Phnom Penh, Cambodia",
        experience_level=job_data.get("experience_level") or "entry",
        job_type=job_data.get("job_type") or "full_time",
        salary_min=job_data.get("salary_min"),
        salary_max=job_data.get("salary_max"),
        salary_currency=job_data.get("salary_currency") or "USD",
        salary_period=job_data.get("salary_period") or "monthly",
        is_negotiable=bool(job_data.get("is_negotiable", False)),
        openings=job_data.get("openings") or 1,
        description=job_data.get("description") or title,
        source=source,
        source_url=source_url,
        source_post_id=str(source_post_id) if source_post_id else None,
        application_url=job_data.get("application_url"),
        apply_email=job_data.get("apply_email"),
        apply_phone=job_data.get("apply_phone"),
        apply_telegram=job_data.get("apply_telegram"),
        work_arrangement=job_data.get("work_arrangement") or "on-site",
        posted_at=job_data.get("posted_at") or date.today(),
        deadline=job_data.get("deadline"),
        dedup_hash=dedup_hash,
        duplicate_of=duplicate_of_id,
        scraped_at=now_utc,
        last_seen_at=now_utc,
        status="active",
        is_active=True
    )
    db.add(new_job)
    db.flush()

    # Link skills
    skills = job_data.get("skills") or []
    all_skills = db.query(Skill).all()
    desc_lower = (title + " " + (job_data.get("description") or "")).lower()
    for sk in all_skills:
        pattern = r'\b' + re.escape(sk.name.lower()) + r'\b'
        if re.search(pattern, desc_lower) or any(sk.name.lower() == s.lower() for s in skills):
            db.add(JobSkill(job_id=new_job.id, skill_id=sk.id))

    return new_job, True, duplicate_of_id
