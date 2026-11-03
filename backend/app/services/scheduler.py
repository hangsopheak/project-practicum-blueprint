"""
backend/app/services/scheduler.py
=================================
Automated Background Scraping Worker for JobMatch.

Periodically syncs Telegram channels and external job sources on a configurable interval.
Provides live status tracking (idle, running, last_scraped_at) for the Admin UI.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.scraper import scrape_and_ingest_telegram

logger = logging.getLogger(__name__)

# State tracker for UI display
scheduler_state: Dict[str, Any] = {
    "is_running": False,
    "current_status": "active",  # 'active', 'scraping_in_progress', 'idle'
    "last_scraped_at": None,
    "last_run_jobs_added": 0,
    "last_sources": [],           # list of sources scraped in last cycle
    "last_error": None,
}

async def auto_scrape_loop():
    """Background task that runs continuously while the FastAPI server is alive."""
    logger.info(
        "Auto-scraper background task initiated. Interval: %s minutes",
        settings.SCRAPER_INTERVAL_MINUTES
    )
    
    # Short delay on boot to allow DB connection pool to settle
    await asyncio.sleep(5)

    while True:
        try:
            scheduler_state["current_status"] = "scraping_in_progress"
            logger.info("Executing scheduled job scraping cycle...")

            # Run in worker thread so it doesn't block FastAPI async event loop
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, _execute_scrape_sync)

            scheduler_state["last_scraped_at"] = datetime.utcnow().isoformat() + "Z"
            scheduler_state["last_run_jobs_added"] = result.get("total_new_added", 0)
            scheduler_state["last_sources"] = result.get("sources_scraped", [])
            scheduler_state["current_status"] = "active"
            scheduler_state["last_error"] = None

            logger.info("Auto-scrape cycle completed: %s new jobs", result.get("total_new_added", 0))

        except Exception as exc:
            logger.error("Auto-scrape cycle failed: %s", exc)
            scheduler_state["current_status"] = "idle"
            scheduler_state["last_error"] = str(exc)

        # Sleep for configured interval
        interval_seconds = max(60, settings.SCRAPER_INTERVAL_MINUTES * 60)
        await asyncio.sleep(interval_seconds)


def _execute_scrape_sync() -> Dict[str, Any]:
    """
    Synchronous scrape execution — runs on every scheduler cycle.
    Scrapes:
      1. All known Telegram channels from DB + default seed channels
      2. Any JSON data files found in the /data directory (web sources)
    """
    import re
    from app.models.models import JobListing
    from app.services.importer import import_from_json_file

    db = SessionLocal()
    total_new_added = 0
    sources_scraped: List[str] = []

    try:
        # --- 1. Telegram Channels ---
        seed_channels = {"internshipscambodia"}
        tg_jobs = db.query(JobListing.source_url).filter(JobListing.source == "Telegram").all()
        for row in tg_jobs:
            url = row[0] or ""
            match = re.search(r't\.me/(?:s/)?([^/]+)', url)
            if match:
                seed_channels.add(match.group(1).lstrip("@"))

        for ch in sorted(seed_channels):
            try:
                res = scrape_and_ingest_telegram(db=db, channel_or_url=ch)
                added = res.get("new_jobs_added", 0)
                total_new_added += added
                sources_scraped.append(f"@{ch} (+{added})")
            except Exception as e:
                logger.warning("Telegram scrape @%s failed: %s", ch, e)
                sources_scraped.append(f"@{ch} (error)")

        # --- 2. Web JSON files (data/ directory) ---
        data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")
        data_dir = os.path.normpath(data_dir)
        if os.path.isdir(data_dir):
            for fname in sorted(os.listdir(data_dir)):
                if fname.endswith(".json"):
                    fpath = os.path.join(data_dir, fname)
                    try:
                        stats = import_from_json_file(db=db, filepath=fpath)
                        added = stats.get("inserted", 0)
                        total_new_added += added
                        sources_scraped.append(f"{fname} (+{added})")
                    except Exception as e:
                        logger.warning("Web import %s failed: %s", fname, e)
                        sources_scraped.append(f"{fname} (error)")

        return {
            "status": "success",
            "sources_scraped": sources_scraped,
            "total_new_added": total_new_added,
        }
    finally:
        db.close()


def get_scheduler_status() -> Dict[str, Any]:
    """Returns current scheduler state for the Admin API/UI."""
    return scheduler_state
