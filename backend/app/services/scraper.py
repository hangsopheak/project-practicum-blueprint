import urllib.request
import urllib.parse
import urllib.error
import json
import re
import hashlib
from datetime import datetime, timezone, date
from typing import Optional, Tuple, List, Dict, Any
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from app.models.models import JobListing, Skill, JobSkill, TelegramJob, WebJob
from app.services.dedup_manager import save_job_with_dedup, compute_dedup_hash


def extract_channel_username(input_val: str) -> str:
    """Extract clean username whether user passes a channel name, @handle, or full t.me URL."""
    cleaned = input_val.strip()
    if "t.me/" in cleaned:
        cleaned = re.sub(r'https?://t\.me/(s/)?', '', cleaned)
    cleaned = cleaned.lstrip('@')
    return cleaned.split('/')[0].split('?')[0]


def make_dedup_hash(title: str, company: str, location: str) -> str:
    """
    Standardized cross-source dedup hash:
    Normalizes noise words ('urgent', 'hiring', 'is seeking', company suffixes, location).
    Guarantees that Telegram and Web postings of the exact same job produce the exact same SHA-256 hash.
    """
    # 1. Clean Title
    t = re.sub(r'[\[\]\(\)‼️🔴🟢🟡⚡💼📢📣🔔⭐🌟✨🎯💡🚀]', ' ', title or '')
    t = re.sub(r'^\s*(?:urgent|hiring|announcement|immediate|vacancy|hot\s*job)\s*[:\-–\s]*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*[-|–]\s*(BongThom|JobNet|CamboJob|Khmer24|Telegram).*$', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s+', ' ', t).strip().lower()

    # 2. Clean Company
    c = re.sub(r'[\[\]\(\)]', ' ', company or '')
    c = re.sub(r'\s*(?:is\s+seeking|is\s+looking\s+for|looking\s+for|needs|is\s+hiring|company:|employer:).*$', '', c, flags=re.IGNORECASE)
    c = re.sub(r'\b(?:co\.?,?\s*ltd|inc\.|corp\.?|llc)\b', '', c, flags=re.IGNORECASE)
    c = re.sub(r'\s+', ' ', c).strip().lower()

    # 3. Clean Location
    l = re.sub(r'\s*,?\s*cambodia', '', (location or '').lower()).strip()
    l = re.sub(r'\s+', ' ', l)

    raw_key = f"{t}|{c}|{l}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:64]


def _normalize_location(text_lower: str) -> str:
    """Detect and standardize Cambodian city names from post text."""
    if "siem reap" in text_lower:
        return "Siem Reap, Cambodia"
    if "sihanouk" in text_lower or "sihanoukvile" in text_lower:
        return "Sihanoukville, Cambodia"
    if "battambang" in text_lower:
        return "Battambang, Cambodia"
    if "kandal" in text_lower:
        return "Kandal, Cambodia"
    if "kampot" in text_lower:
        return "Kampot, Cambodia"
    if "takeo" in text_lower:
        return "Takeo, Cambodia"
    # Default to Phnom Penh for Cambodia-focused channels
    return "Phnom Penh, Cambodia"


def _parse_salary_from_text(text: str) -> Tuple[Optional[float], Optional[float], bool]:
    """
    Extract salary range from Telegram post text.
    Returns (salary_min, salary_max, is_negotiable).
    Examples: '$500-$800', 'USD 600', '$300+', 'negotiable'
    """
    salary_min = None
    salary_max = None
    is_negotiable = False

    text_lower = text.lower()
    if "negotiable" in text_lower or "competitive" in text_lower:
        is_negotiable = True

    # Pattern: $500 - $800 | $500-$800 | USD 500-800
    range_match = re.search(
        r'(?:usd|\$)\s*(\d{2,5})\s*[-–to]+\s*(?:usd|\$)?\s*(\d{2,5})',
        text, re.IGNORECASE
    )
    if range_match:
        salary_min = float(range_match.group(1))
        salary_max = float(range_match.group(2))
        return salary_min, salary_max, is_negotiable

    # Pattern: $500+ or $500/month
    single_match = re.search(
        r'(?:usd|\$)\s*(\d{2,5})(?:\+|/month|/mo|k)?',
        text, re.IGNORECASE
    )
    if single_match:
        val = float(single_match.group(1))
        salary_min = val
        salary_max = val * 1.3  # rough upper estimate
        return salary_min, salary_max, is_negotiable

    return None, None, is_negotiable


def _parse_openings_from_text(text: str) -> int:
    """
    Detect number of openings from post text.
    Examples: '2 vacancies', 'hiring 3 people', '(5 positions)'
    """
    patterns = [
        r'(\d+)\s+(?:vacancy|vacancies|opening[s]?|position[s]?|slot[s]?)',
        r'hiring\s+(\d+)',
        r'\((\d+)\s+(?:vacancy|vacancies|position[s]?)\)',
        r'need[s]?\s+(\d+)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                return max(1, int(m.group(1)))
            except ValueError:
                pass
    return 1


def _parse_deadline_from_text(text: str) -> Optional[date]:
    """
    Parse deadline/closing date from post text.
    Examples: 'Deadline: 30 Nov 2024', 'Apply by: 2024-11-30', 'Closing: Nov 30'
    """
    deadline_markers = [
        r'(?:deadline|closing|apply by|due by|close[sd]? on|expires?)[:\s]+([A-Za-z0-9 ,\-/]+)',
    ]
    date_formats = [
        "%d %b %Y", "%d %B %Y", "%B %d, %Y", "%b %d, %Y",
        "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y",
    ]
    for pat in deadline_markers:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()[:30]
            for fmt in date_formats:
                try:
                    return datetime.strptime(raw, fmt).date()
                except ValueError:
                    pass
    return None


def _extract_company_url(text: str, post_url: str) -> Optional[str]:
    """
    Extract company website URL from post text (skip Telegram URLs).
    """
    urls = re.findall(r'https?://[^\s<>"]+', text)
    for url in urls:
        if "t.me" not in url and url != post_url:
            return url
    return None


def _parse_telegram_contacts(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract (apply_telegram, apply_email, apply_phone) from Telegram message text."""
    # Email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    apply_email = email_match.group(0) if email_match else None

    # Phone (Cambodia patterns: 012 345 678, +855 12 345 678, 088-123-4567, etc.)
    phone_match = re.search(r'(?:\+?855|0)\s*[1-9]\d{1,2}[-\s]?\d{3}[-\s]?\d{3,4}', text)
    apply_phone = phone_match.group(0).strip() if phone_match else None

    # Telegram handle (@recruiter or t.me/recruiter)
    tg_handles = re.findall(r'@[A-Za-z0-9_]{4,}', text)
    apply_telegram = None
    for handle in tg_handles:
        h_low = handle.lower()
        if "channel" not in h_low and "internship" not in h_low and "job" not in h_low:
            apply_telegram = handle
            break

    return apply_telegram, apply_email, apply_phone


def scrape_and_ingest_telegram(db: Session, channel_or_url: str = "internshipscambodia") -> dict:
    """
    Scrapes live vacancies from public Telegram channel or URL preview
    and ingests them into the PostgreSQL database.

    Fills all 25 job_listings schema fields where extractable from post text.
    """
    channel_username = extract_channel_username(channel_or_url)
    url = f"https://t.me/s/{channel_username}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')

    soup = BeautifulSoup(html, 'html.parser')
    messages = soup.find_all('div', class_='tgme_widget_message_wrap')

    # Load master skills catalog for keyword extraction
    all_skills = db.query(Skill).all()

    new_jobs_count = 0

    for msg in messages:
        text_elem = msg.find('div', class_='tgme_widget_message_text')
        if not text_elem:
            continue
        text = text_elem.get_text(separator="\n").strip()

        link_elem = msg.find('a', class_='tgme_widget_message_date')
        post_url = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""
        if not post_url:
            continue

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if len(lines) < 2 or len(text) < 40:
            continue

        text_lower = text.lower()

        # --- source_post_id: extract numeric post ID from URL ---
        post_id_match = re.search(r'/(\d+)$', post_url)
        source_post_id = post_id_match.group(1) if post_id_match else None

        # --- raw_title: first non-empty line, uncleaned ---
        raw_title = lines[0][:255]

        # --- title: clean version of raw_title ---
        clean_raw = re.sub(r'[\[\]\(\)‼️🔴🟢🟡⚡💼📢📣🔔⭐🌟✨🎯💡🚀]', '', raw_title)
        clean_raw = re.sub(r'^\s*(?:urgent|hiring|announcement|immediate|vacancy|hot\s*job)\s*[:\-–\s]*', '', clean_raw, flags=re.IGNORECASE)
        title = clean_raw.strip()[:100] or raw_title[:100]
        if len(title) < 5 and len(lines) > 1:
            title = lines[1][:100]

        # --- company: detect from text context ---
        company = "Cambodia Hiring Organization"
        for line in lines[:6]:
            line_low = line.lower()
            if any(kw in line_low for kw in ["looking for", "is seeking", "co., ltd", "co.,ltd",
                                               "company:", "organization:", "employer:"]):
                c_line = re.sub(r'\s*(?:is\s+seeking|is\s+looking\s+for|looking\s+for|needs|is\s+hiring|company:|organization:|employer:).*$', '', line, flags=re.IGNORECASE).strip()
                company = c_line[:150] if len(c_line) > 2 else line[:150]
                break
            if re.search(r'\b(?:co\.?,?\s*ltd|inc\.|corp\.?|group|bank|school|hotel|clinic)\b',
                         line_low):
                c_line = re.sub(r'\s*(?:is\s+seeking|is\s+looking\s+for|looking\s+for|needs|is\s+hiring).*$', '', line, flags=re.IGNORECASE).strip()
                company = c_line[:150] if len(c_line) > 2 else line[:150]
                break

        # --- posted_at: parse from <time> element ---
        date_elem = msg.find('time')
        posted_date = None
        if date_elem and 'datetime' in date_elem.attrs:
            try:
                posted_date = datetime.fromisoformat(
                    date_elem['datetime'].replace("Z", "+00:00")
                ).date()
            except Exception:
                posted_date = datetime.utcnow().date()

        # --- work_arrangement ---
        if "remote" in text_lower:
            work_arrangement = "remote"
        elif "hybrid" in text_lower:
            work_arrangement = "hybrid"
        else:
            work_arrangement = "on-site"

        # --- job_type: snake_case ---
        if "intern" in text_lower:
            job_type = "internship"
        elif "part" in text_lower and "time" in text_lower:
            job_type = "part_time"
        elif "contract" in text_lower or "freelance" in text_lower:
            job_type = "contract"
        else:
            job_type = "full_time"

        # --- experience_level ---
        if any(k in text_lower for k in ["fresh grad", "no experience", "entry", "intern"]):
            experience_level = "entry"
        elif "junior" in text_lower:
            experience_level = "junior"
        elif "senior" in text_lower or "lead" in text_lower:
            experience_level = "senior"
        elif "manager" in text_lower or "director" in text_lower:
            experience_level = "manager"
        else:
            experience_level = "entry"

        # --- location & normalized_location ---
        location = "Phnom Penh"
        normalized_location = _normalize_location(text_lower)

        # --- salary ---
        salary_min, salary_max, is_negotiable = _parse_salary_from_text(text)

        # --- openings ---
        openings = _parse_openings_from_text(text)

        # --- deadline ---
        deadline = _parse_deadline_from_text(text)

        # --- application_url: first non-Telegram URL or post_url ---
        company_url = _extract_company_url(text, post_url)
        urls_in_text = re.findall(r'https?://[^\s<>"]+', text)
        application_url = urls_in_text[0] if urls_in_text else post_url

        # --- dedup_hash: cross-source normalized SHA-256 ---
        dedup_hash = make_dedup_hash(title, company, normalized_location or location)

        # Extract Telegram contact methods
        apply_tg, apply_em, apply_ph = _parse_telegram_contacts(text)
        lang = "km" if any('\u1780' <= c <= '\u17ff' for c in text) else "en"
        channel_handle = f"@{channel_username}"
        now_utc = datetime.now(timezone.utc)
        post_id_str = str(source_post_id or post_url)

        # 1. Save directly into dedicated telegram_jobs table (all 33 fields)
        existing_tg = db.query(TelegramJob).filter(
            TelegramJob.source == channel_handle,
            TelegramJob.source_post_id == post_id_str,
            TelegramJob.job_index == 0
        ).first()

        if existing_tg:
            existing_tg.title = title
            existing_tg.company = company
            existing_tg.location = location
            existing_tg.normalized_location = normalized_location
            existing_tg.work_arrangement = work_arrangement
            existing_tg.job_type = job_type
            existing_tg.experience_level = experience_level
            existing_tg.description = text
            existing_tg.raw_text = text
            existing_tg.language = lang
            existing_tg.salary_min = salary_min
            existing_tg.salary_max = salary_max
            existing_tg.is_negotiable = is_negotiable
            existing_tg.deadline = deadline
            existing_tg.application_url = application_url
            existing_tg.apply_email = apply_em
            existing_tg.apply_phone = apply_ph
            existing_tg.apply_telegram = apply_tg
            existing_tg.dedup_hash = dedup_hash
            existing_tg.is_active = True
            existing_tg.last_seen_at = now_utc
        else:
            tg_record = TelegramJob(
                title=title,
                company=company,
                location=location,
                normalized_location=normalized_location,
                work_arrangement=work_arrangement,
                job_type=job_type,
                experience_level=experience_level,
                description=text,
                raw_text=text,
                language=lang,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency="USD",
                salary_period="month",
                is_negotiable=is_negotiable,
                posted_at=posted_date,
                deadline=deadline,
                application_url=application_url,
                apply_email=apply_em,
                apply_phone=apply_ph,
                apply_telegram=apply_tg,
                source_platform="telegram",
                source=channel_handle,
                source_post_id=post_id_str,
                job_index=0,
                source_url=post_url,
                dedup_hash=dedup_hash,
                is_active=True,
                scraped_at=now_utc,
                last_seen_at=now_utc,
            )
            db.add(tg_record)

        # 2. Sync to JobListing table using dedup_manager
        job_payload = {
            "title": title,
            "raw_title": raw_title,
            "company": company,
            "company_url": company_url,
            "company_logo_url": None,
            "location": location,
            "normalized_location": normalized_location,
            "experience_level": experience_level,
            "job_type": job_type,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_currency": "USD",
            "salary_period": "monthly",
            "is_negotiable": is_negotiable,
            "openings": openings,
            "description": text,
            "source": "Telegram",
            "source_url": post_url,
            "source_post_id": source_post_id,
            "application_url": application_url,
            "apply_email": apply_em,
            "apply_phone": apply_ph,
            "apply_telegram": apply_tg,
            "work_arrangement": work_arrangement,
            "posted_at": posted_date,
            "deadline": deadline,
        }
        target_job, is_new, dup_of = save_job_with_dedup(db, job_payload)
        if is_new and dup_of is None:
            new_jobs_count += 1

    db.commit()
    total_jobs = db.query(JobListing).count()

    return {
        "status": "success",
        "channel": f"@{channel_username}",
        "new_jobs_added": new_jobs_count,
        "total_jobs": total_jobs
    }


def _detect_source_name(url: str) -> str:
    """Derive clean source name from domain."""
    domain = urllib.parse.urlparse(url).netloc.lower()
    if "bongthom" in domain:
        return "BongThom"
    if "jobnet" in domain:
        return "JobNet"
    if "cambojob" in domain:
        return "CamboJob"
    if "khmer24" in domain:
        return "Khmer24"
    if "workingna" in domain:
        return "Workingna"
    # Format general domain as Clean Title (e.g. example.com -> Example)
    clean_domain = domain.replace("www.", "").split(".")[0]
    return clean_domain.capitalize() if clean_domain else "Web Aggregator"


def scrape_and_ingest_web_url(db: Session, web_url: str) -> Dict[str, Any]:
    """
    Directly scrapes a web job posting URL and ingests it into PostgreSQL.
    Extracts structured JSON-LD (Schema.org JobPosting) or parses HTML metadata.
    Automatically standardizes all fields, deduplicates, and links skills.
    """
    clean_url = web_url.strip()
    if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
        clean_url = "https://" + clean_url

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }

    req = urllib.request.Request(clean_url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as response:
        html = response.read().decode('utf-8', errors='replace')

    soup = BeautifulSoup(html, 'html.parser')

    # Defaults
    source_name = _detect_source_name(clean_url)
    title = ""
    raw_title = ""
    company = "Hiring Organization"
    company_logo_url = None
    location = "Phnom Penh"
    description = ""
    salary_min = None
    salary_max = None
    is_negotiable = False
    salary_currency = "USD"
    job_type = "full_time"
    experience_level = "entry"
    posted_date = datetime.now(timezone.utc).date()
    deadline = None
    openings = 1
    work_arrangement = "on-site"

    # 1. Attempt structured Schema.org JobPosting extraction
    json_ld_tags = soup.find_all('script', type='application/ld+json')
    for tag in json_ld_tags:
        try:
            data = json.loads(tag.string or "{}")
            if isinstance(data, list):
                postings = [p for p in data if isinstance(p, dict) and p.get("@type") == "JobPosting"]
                data = postings[0] if postings else {}
            if isinstance(data, dict) and data.get("@type") == "JobPosting":
                title = data.get("title", "")
                raw_title = title
                desc_html = data.get("description", "")
                if desc_html:
                    description = BeautifulSoup(desc_html, 'html.parser').get_text(separator="\n").strip()
                
                hiring_org = data.get("hiringOrganization")
                if isinstance(hiring_org, dict):
                    company = hiring_org.get("name", company)
                    company_logo_url = hiring_org.get("logo")
                elif isinstance(hiring_org, str):
                    company = hiring_org

                job_loc = data.get("jobLocation")
                if isinstance(job_loc, dict):
                    addr = job_loc.get("address", {})
                    if isinstance(addr, dict):
                        location = addr.get("addressLocality") or addr.get("addressRegion") or location
                    elif isinstance(addr, str):
                        location = addr

                emp_type = data.get("employmentType")
                if emp_type:
                    emp_type_str = str(emp_type).lower()
                    if "intern" in emp_type_str:
                        job_type = "internship"
                    elif "part" in emp_type_str:
                        job_type = "part_time"
                    elif "contract" in emp_type_str:
                        job_type = "contract"

                base_sal = data.get("baseSalary")
                if isinstance(base_sal, dict):
                    val = base_sal.get("value")
                    if isinstance(val, dict):
                        salary_min = float(val.get("minValue") or 0) or None
                        salary_max = float(val.get("maxValue") or 0) or None
                    elif val:
                        try:
                            salary_min = float(val)
                        except (ValueError, TypeError):
                            pass
                    salary_currency = str(base_sal.get("currency") or "USD")

                date_posted_str = data.get("datePosted")
                if date_posted_str:
                    try:
                        posted_date = datetime.fromisoformat(date_posted_str.replace("Z", "+00:00")).date()
                    except Exception:
                        pass

                valid_through_str = data.get("validThrough")
                if valid_through_str:
                    try:
                        deadline = datetime.fromisoformat(valid_through_str.replace("Z", "+00:00")).date()
                    except Exception:
                        pass
                break
        except Exception:
            continue

    # 2. Fallback to OpenGraph and semantic HTML tags
    if not title:
        og_title = soup.find('meta', property='og:title') or soup.find('meta', attrs={'name': 'twitter:title'})
        if og_title and og_title.get('content'):
            title = og_title['content'].strip()
        elif soup.find('h1'):
            title = soup.find('h1').get_text().strip()
        elif soup.title:
            title = soup.title.get_text().strip()
        raw_title = title
        # Strip common site titles like " - BongThom" or " | JobNet"
        title = re.sub(r'\s*[-|–]\s*(BongThom|JobNet|CamboJob|Khmer24|Careers|Jobs).*$', '', title, flags=re.IGNORECASE).strip()

    if company == "Hiring Organization":
        og_site = soup.find('meta', property='og:site_name')
        if og_site and og_site.get('content'):
            company = og_site['content'].strip()
        else:
            comp_elem = soup.find(class_=re.compile(r'company|employer|organization', re.I))
            if comp_elem:
                company = comp_elem.get_text().strip()[:100]

    if not company_logo_url:
        og_img = soup.find('meta', property='og:image')
        if og_img and og_img.get('content'):
            company_logo_url = og_img['content'].strip()

    page_text = soup.get_text(separator="\n")
    if not description:
        desc_elem = soup.find('article') or soup.find(class_=re.compile(r'description|job-detail|vacancy-detail', re.I))
        if desc_elem:
            description = desc_elem.get_text(separator="\n").strip()
        else:
            description = page_text[:2000].strip()

    page_text_lower = page_text.lower()

    # Normalize location
    normalized_location = _normalize_location(page_text_lower)

    # Parse salary from text if not extracted from JSON-LD
    if salary_min is None and salary_max is None:
        sal_min, sal_max, sal_neg = _parse_salary_from_text(page_text)
        salary_min = sal_min
        salary_max = sal_max
        is_negotiable = sal_neg

    # Experience level
    if any(k in page_text_lower for k in ["fresh grad", "no experience", "entry", "intern"]):
        experience_level = "entry"
    elif "junior" in page_text_lower:
        experience_level = "junior"
    elif "senior" in page_text_lower or "lead" in page_text_lower:
        experience_level = "senior"
    elif "manager" in page_text_lower:
        experience_level = "manager"

    # Work arrangement
    if "remote" in page_text_lower:
        work_arrangement = "remote"
    elif "hybrid" in page_text_lower:
        work_arrangement = "hybrid"

    # Openings & Deadline
    openings = _parse_openings_from_text(page_text)
    if not deadline:
        deadline = _parse_deadline_from_text(page_text)

    # Deduplication hash (standardized cross-source SHA-256)
    clean_title = title[:100] if title else "Job Vacancy"
    clean_company = company[:150] if company else "Confidential"
    dedup_hash = make_dedup_hash(clean_title, clean_company, normalized_location or location)

    # Source post id from URL
    url_slug = clean_url.rstrip("/").split("/")[-1].split("?")[0]
    source_post_id = url_slug[:100] if url_slug else None

    # Load skills catalog
    all_skills = db.query(Skill).all()

    # Save to JobListing using dedup_manager
    web_payload = {
        "title": clean_title,
        "raw_title": raw_title[:255] if raw_title else clean_title,
        "company": clean_company,
        "company_url": None,
        "company_logo_url": company_logo_url,
        "location": location,
        "normalized_location": normalized_location,
        "experience_level": experience_level,
        "job_type": job_type,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": salary_currency,
        "salary_period": "monthly",
        "is_negotiable": is_negotiable,
        "openings": openings,
        "description": description,
        "source": source_name,
        "source_url": clean_url,
        "source_post_id": source_post_id,
        "application_url": clean_url,
        "work_arrangement": work_arrangement,
        "posted_at": posted_date,
        "deadline": deadline,
    }
    target_job, is_new, dup_of = save_job_with_dedup(db, web_payload)
    # Save into dedicated web_jobs table
    now_utc = datetime.now(timezone.utc)
    existing_web = db.query(WebJob).filter(WebJob.source_url == clean_url).first()
    if existing_web:
        existing_web.title = clean_title
        existing_web.raw_title = raw_title[:255] if raw_title else clean_title
        existing_web.company = clean_company
        existing_web.company_logo_url = company_logo_url or existing_web.company_logo_url
        existing_web.location = location
        existing_web.normalized_location = normalized_location
        existing_web.work_arrangement = work_arrangement
        existing_web.job_type = job_type
        existing_web.experience_level = experience_level
        existing_web.salary_min = salary_min
        existing_web.salary_max = salary_max
        existing_web.is_negotiable = is_negotiable
        existing_web.openings = openings
        existing_web.description = description
        existing_web.deadline = deadline or existing_web.deadline
        existing_web.dedup_hash = dedup_hash
        existing_web.is_active = True
        existing_web.last_seen_at = now_utc
    else:
        web_record = WebJob(
            title=clean_title,
            raw_title=raw_title[:255] if raw_title else clean_title,
            company=clean_company,
            company_url=None,
            company_logo_url=company_logo_url,
            location=location,
            normalized_location=normalized_location,
            work_arrangement=work_arrangement,
            job_type=job_type,
            experience_level=experience_level,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            salary_period="month",
            is_negotiable=is_negotiable,
            openings=openings,
            description=description,
            source_portal=source_name,
            source_url=clean_url,
            source_job_id=source_post_id,
            application_url=clean_url,
            posted_at=posted_date,
            deadline=deadline,
            dedup_hash=dedup_hash,
            is_active=True,
            scraped_at=now_utc,
            last_seen_at=now_utc,
        )
        db.add(web_record)

    # Tag skills
    matched_skill_names = []
    desc_lower = (clean_title + " " + description).lower()
    for skill in all_skills:
        pattern = r'\b' + re.escape(skill.name.lower()) + r'\b'
        if re.search(pattern, desc_lower):
            db.add(JobSkill(job_id=target_job.id, skill_id=skill.id))
            matched_skill_names.append(skill.name)

    db.commit()
    total_jobs = db.query(JobListing).count()

    return {
        "status": "success",
        "action": "inserted" if is_new else "updated",
        "source": source_name,
        "new_jobs_added": 1 if is_new else 0,
        "duplicates_skipped": 0 if is_new else 1,
        "total_jobs": total_jobs,
        "job": {
            "id": target_job.id,
            "title": target_job.title,
            "company": target_job.company,
            "location": target_job.normalized_location or target_job.location,
            "job_type": target_job.job_type,
            "experience_level": target_job.experience_level,
            "salary": f"${int(target_job.salary_min)}-${int(target_job.salary_max)}" if target_job.salary_min and target_job.salary_max else ("Negotiable" if target_job.is_negotiable else "Not disclosed"),
            "skills_tagged": matched_skill_names,
            "source_url": target_job.source_url
        }
    }

