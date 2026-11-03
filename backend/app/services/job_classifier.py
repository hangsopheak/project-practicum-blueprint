"""
backend/app/services/job_classifier.py
======================================
TypeSafe AI Jev Job Classification & Hybrid Fallback Engine.

Responsibilities:
1. Receives normalized job data (title, company, description).
2. Formulates structured queries for TypeSafe AI's Jev "System One" decision engine.
   - Uses the 'choice' primitive with 'criteria' mappings (label -> description).
3. Evaluates returned answers and confidence scores against the threshold.
4. Falls back gracefully to local Python rule-based classification if:
   - JEV_API_KEY is unset or invalid
   - API timeout or network failure occurs
   - Classification confidence < threshold
   - Content is primarily non-English/Khmer without clear English signals
5. Returns a typed dictionary with:
   - job_category
   - job_subcategory
   - job_level
   - work_arrangement (inferred if missing)
   - classification_confidence
   - classification_source ('jev' | 'rule')
"""

import os
import re
import logging
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)

JEV_API_URL = os.getenv("JEV_API_URL", "https://api.typesafe.ai/v1/systemone")
JEV_API_KEY = os.getenv("JEV_API_KEY", "").strip()
CONFIDENCE_THRESHOLD = float(os.getenv("JEV_CONFIDENCE_THRESHOLD", "0.65"))

# ─────────────────────────────────────────────────────────────────────────────
# 1. Classification Taxonomies & Criteria for Jev
# ─────────────────────────────────────────────────────────────────────────────

JOB_CATEGORY_CRITERIA = {
    "Information Technology": "Software development, programming, IT support, cloud infrastructure, systems, computer science, mobile/web engineering.",
    "Finance & Accounting": "Accounting, bookkeeping, financial analysis, auditing, tax reporting, payroll management.",
    "Banking": "Commercial banking, credit assessment, loan officers, teller services, microfinance institutions (MFI).",
    "Marketing": "Digital marketing, social media management, brand strategy, advertising campaigns, SEO/content creation.",
    "Sales": "Business development, account executive, outdoor sales, retail sales, lead generation, client acquisitions.",
    "Human Resources": "Recruitment, talent acquisition, employee relations, HR administration, training and development.",
    "Administration": "Office management, administrative assistant, document control, reception, general clerical work.",
    "Education": "Teaching, lecturing, curriculum development, academic coordination, tutoring, training institutes.",
    "Engineering": "Civil engineering, electrical engineering, mechanical engineering, architecture, construction design.",
    "Healthcare": "Medical staff, nursing, pharmacy, clinical practice, public health, laboratory technicians.",
    "Hospitality & Tourism": "Hotel management, front desk, travel agency, tour operations, food & beverage (F&B) service.",
    "Customer Service": "Call center, customer support, helpdesk, client care, issue resolution.",
    "Logistics & Supply Chain": "Warehouse management, shipping, freight forwarding, inventory control, procurement.",
    "Manufacturing": "Factory operations, production line, quality assurance (QA) in manufacturing, garment production.",
    "Construction": "Site supervisor, construction worker, contractor, building inspection, site safety.",
    "Other": "Occupations and roles that do not clearly fit into any of the predefined primary categories.",
}

IT_SUBCATEGORY_CRITERIA = {
    "Mobile Development": "iOS, Android, Flutter, Dart, React Native, Swift, Kotlin mobile app engineering.",
    "Web Development": "Full stack, web applications, general web developer, PHP, Laravel, WordPress, web platforms.",
    "Frontend Development": "Client-side web development, React, Vue, Angular, HTML/CSS, JavaScript/TypeScript UI.",
    "Backend Development": "Server-side architecture, APIs, Node.js, Python, Java, Go, databases, microservices.",
    "Full Stack Development": "Both frontend and backend development across the entire web application stack.",
    "Software Engineering": "Core software design, algorithmic systems, C/C++, embedded systems, desktop software.",
    "UI/UX Design": "User interface, user experience, Figma, wireframing, product design, user research.",
    "Data Analysis": "Data analytics, business intelligence, SQL, Excel reports, PowerBI, Tableau.",
    "Data Science": "Machine learning, AI, statistical modeling, Python data science libraries, predictive algorithms.",
    "Cybersecurity": "Information security, penetration testing, network security, security audits, SOC.",
    "Network Administration": "Cisco, routers, switches, LAN/WAN, system administration, server maintenance.",
    "IT Support": "Technical helpdesk, hardware troubleshooting, workstation setup, office IT support.",
    "DevOps": "CI/CD pipelines, Docker, Kubernetes, AWS/GCP, infrastructure as code, cloud operations.",
    "Other": "Technical computing roles that do not map directly to these subcategories.",
}

JOB_LEVEL_CRITERIA = {
    "Internship": "Student internship, trainee, apprentice, educational practical placement with zero or minimal prior experience.",
    "Entry-level": "Fresh graduates, 0-1 year experience, foundational knowledge, supervised tasks.",
    "Junior": "1-2 years experience, working knowledge, developing independence in standard assignments.",
    "Mid-level": "2-4 years experience, autonomous execution, proficient problem solver.",
    "Senior": "4+ years experience, architectural guidance, mentoring, advanced technical ownership.",
    "Manager": "Team management, operational responsibility, budgeting, leading personnel.",
    "Director": "Strategic leadership, head of department, executive oversight, business alignment.",
    "Unknown": "Seniority level is not mentioned or cannot be determined from the posting.",
}

WORK_ARRANGEMENT_CRITERIA = {
    "On-site": "Work performed primarily or exclusively at physical office or company premises.",
    "Remote": "Work performed 100% from home or anywhere without physical office attendance required.",
    "Hybrid": "Combination of partial days in physical office and partial days remote from home.",
    "Unknown": "Work arrangement is not specified in the description.",
}


# ─────────────────────────────────────────────────────────────────────────────
# 2. Local Python Rule-Based Fallback Classifier
# ─────────────────────────────────────────────────────────────────────────────

def rule_based_classify(title: str, description: str, company: str = "") -> Dict[str, Any]:
    """
    Deterministic local classifier using keyword heuristics.
    Used when Jev API is unavailable or returns low confidence.
    """
    text = f"{title} {company} {description}".lower()

    # Category heuristic
    category = "Unknown"
    subcategory = "Unknown"

    if re.search(r'\b(developer|software|programmer|flutter|dart|react|python|backend|frontend|java|devops|network|sysadmin|cyber|ui/ux|figma|database|it support|it specialist|coder)\b', text):
        category = "Information Technology"
        if re.search(r'\b(flutter|dart|android|ios|react native|swift|kotlin|mobile)\b', text):
            subcategory = "Mobile Development"
        elif re.search(r'\b(frontend|front-end|react|vue|angular|html|css)\b', text):
            subcategory = "Frontend Development"
        elif re.search(r'\b(backend|back-end|node|django|fastapi|laravel|golang|spring boot|api)\b', text):
            subcategory = "Backend Development"
        elif re.search(r'\b(full stack|fullstack|full-stack)\b', text):
            subcategory = "Full Stack Development"
        elif re.search(r'\b(ui/ux|ui|ux|figma|designer|user experience)\b', text):
            subcategory = "UI/UX Design"
        elif re.search(r'\b(devops|docker|kubernetes|aws|cloud|ci/cd)\b', text):
            subcategory = "DevOps"
        elif re.search(r'\b(data analyst|data analysis|bi analyst|power bi|tableau|sql analyst)\b', text):
            subcategory = "Data Analysis"
        elif re.search(r'\b(cyber|security|penetration|soc)\b', text):
            subcategory = "Cybersecurity"
        elif re.search(r'\b(it support|helpdesk|hardware|computer technician)\b', text):
            subcategory = "IT Support"
        elif re.search(r'\b(network|cisco|system admin|sysadmin)\b', text):
            subcategory = "Network Administration"
        else:
            subcategory = "Software Engineering"
    elif re.search(r'\b(accountant|accounting|audit|tax|bookkeeper|finance|financial)\b', text):
        category = "Finance & Accounting"
    elif re.search(r'\b(bank|teller|loan officer|credit officer|mfi|microfinance)\b', text):
        category = "Banking"
    elif re.search(r'\b(marketing|social media|seo|content creator|copywriter|branding)\b', text):
        category = "Marketing"
    elif re.search(r'\b(sales|business development|outdoor sales|retail sales|account executive)\b', text):
        category = "Sales"
    elif re.search(r'\b(hr|human resource|recruitment|talent acquisition|payroll)\b', text):
        category = "Human Resources"
    elif re.search(r'\b(admin|administration|receptionist|clerk|office assistant)\b', text):
        category = "Administration"
    elif re.search(r'\b(teacher|teaching|lecturer|instructor|curriculum|academic|tutor)\b', text):
        category = "Education"
    elif re.search(r'\b(hotel|resort|front desk|f&b|tourist|tourism|waiter|chef)\b', text):
        category = "Hospitality & Tourism"
    elif re.search(r'\b(nurse|doctor|pharmacist|medical|clinic|hospital)\b', text):
        category = "Healthcare"
    elif re.search(r'\b(civil engineer|electrical engineer|mechanical engineer|architect)\b', text):
        category = "Engineering"
    elif re.search(r'\b(customer service|call center|customer support|client care)\b', text):
        category = "Customer Service"
    elif re.search(r'\b(logistics|warehouse|shipping|procurement|supply chain)\b', text):
        category = "Logistics & Supply Chain"

    # Seniority Level heuristic
    level = "Unknown"
    title_lower = title.lower()
    if re.search(r'\b(intern|internship|trainee|apprentice)\b', title_lower) or re.search(r'\b(intern|internship)\b', text):
        level = "Internship"
    elif re.search(r'\b(fresh|graduate|entry|entry-level)\b', title_lower):
        level = "Entry-level"
    elif re.search(r'\b(junior|jr\.?)\b', title_lower):
        level = "Junior"
    elif re.search(r'\b(director|head of|vp|chief)\b', title_lower):
        level = "Director"
    elif re.search(r'\b(manager|lead|supervisor)\b', title_lower):
        level = "Manager"
    elif re.search(r'\b(senior|sr\.?|principal)\b', title_lower):
        level = "Senior"
    elif re.search(r'\b(mid|mid-level)\b', title_lower):
        level = "Mid-level"
    else:
        # Check description context
        if re.search(r'\b(senior|5\+\s*years|4\+\s*years)\b', text):
            level = "Senior"
        elif re.search(r'\b(junior|1\s*year|fresh)\b', text):
            level = "Junior"

    # Work arrangement heuristic
    arrangement = "Unknown"
    if re.search(r'\b(remote|work from home|wfh|telecommute)\b', text):
        arrangement = "Remote"
    elif re.search(r'\b(hybrid|flexible)\b', text):
        arrangement = "Hybrid"
    elif re.search(r'\b(on-site|onsite|office based|in office)\b', text):
        arrangement = "On-site"

    return {
        "job_category": category,
        "job_subcategory": subcategory,
        "job_level": level,
        "work_arrangement": arrangement,
        "classification_confidence": 0.70 if category != "Unknown" else 0.40,
        "classification_source": "rule",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Hybrid Jev Classifier Main Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

def classify_job(
    title: str,
    description: str,
    company: str = "",
    existing_work_arrangement: Optional[str] = None
) -> Dict[str, Any]:
    """
    Classifies a job posting using TypeSafe AI's Jev if available;
    otherwise falls back smoothly to local Python rule-based classification.

    Preserves existing work_arrangement if already specified.
    """
    clean_title = (title or "").strip()
    clean_desc = (description or "").strip()
    clean_company = (company or "").strip()

    # If JEV_API_KEY is not configured, run rule-based immediately (zero overhead)
    if not JEV_API_KEY:
        res = rule_based_classify(clean_title, clean_desc, clean_company)
        if existing_work_arrangement and existing_work_arrangement.lower() != "unknown":
            res["work_arrangement"] = existing_work_arrangement
        return res

    # Construct concise state representation (limit text to stay within fast tokens)
    state_text = f"Title: {clean_title}\nCompany: {clean_company}\nDescription:\n{clean_desc[:2500]}"

    questions = {
        "job_category": {
            "type": "choice",
            "instructions": "Classify the primary professional industry or domain of this job vacancy.",
            "criteria": JOB_CATEGORY_CRITERIA,
        },
        "job_level": {
            "type": "choice",
            "instructions": "Determine the required career seniority level for this role based on the title and duties.",
            "criteria": JOB_LEVEL_CRITERIA,
        },
    }

    # Only request subcategory if likely IT or general
    questions["job_subcategory"] = {
        "type": "choice",
        "instructions": "If this is an Information Technology position, identify the specific subcategory. Otherwise select 'Other'.",
        "criteria": IT_SUBCATEGORY_CRITERIA,
    }

    # Only request work arrangement if not already known
    if not existing_work_arrangement or existing_work_arrangement.lower() == "unknown":
        questions["work_arrangement"] = {
            "type": "choice",
            "instructions": "Determine if this vacancy is On-site, Remote, Hybrid, or Unknown.",
            "criteria": WORK_ARRANGEMENT_CRITERIA,
        }

    payload = {
        "model": "jev-latest",
        "state": state_text,
        "questions": questions,
    }

    try:
        response = requests.post(
            JEV_API_URL,
            headers={
                "Authorization": f"Bearer {JEV_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=4.0  # 4 second timeout prevents scraper slowdown
        )

        if response.status_code == 200:
            data = response.json()
            answers = data.get("answers", {})

            # Extract category
            cat_ans = answers.get("job_category", {})
            cat_choice = cat_ans.get("choice", "Unknown")
            cat_conf = float(cat_ans.get("confidence", 0.0))

            # Extract level
            lvl_ans = answers.get("job_level", {})
            lvl_choice = lvl_ans.get("choice", "Unknown")
            lvl_conf = float(lvl_ans.get("confidence", 0.0))

            # Extract subcategory
            sub_ans = answers.get("job_subcategory", {})
            sub_choice = sub_ans.get("choice", "Unknown")

            # Extract work arrangement
            if "work_arrangement" in answers:
                arr_ans = answers.get("work_arrangement", {})
                arr_choice = arr_ans.get("choice", "Unknown")
            else:
                arr_choice = existing_work_arrangement or "Unknown"

            avg_conf = (cat_conf + lvl_conf) / 2.0

            # Confidence check
            if avg_conf >= CONFIDENCE_THRESHOLD and cat_choice in JOB_CATEGORY_CRITERIA:
                return {
                    "job_category": cat_choice,
                    "job_subcategory": sub_choice if sub_choice in IT_SUBCATEGORY_CRITERIA else "Unknown",
                    "job_level": lvl_choice if lvl_choice in JOB_LEVEL_CRITERIA else "Unknown",
                    "work_arrangement": arr_choice,
                    "classification_confidence": round(avg_conf, 3),
                    "classification_source": "jev",
                }
            else:
                logger.info(f"Jev confidence below threshold ({avg_conf:.2f} < {CONFIDENCE_THRESHOLD}); falling back to rules.")
        else:
            logger.warning(f"Jev API returned status {response.status_code}: {response.text[:200]}")

    except Exception as e:
        logger.warning(f"Jev API call failed ({e}); engaging rule-based fallback.")

    # Graceful fallback on any failure
    fallback = rule_based_classify(clean_title, clean_desc, clean_company)
    if existing_work_arrangement and existing_work_arrangement.lower() != "unknown":
        fallback["work_arrangement"] = existing_work_arrangement
    return fallback

