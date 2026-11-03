from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
import app.models # ensure all models are registered

# Automatically create all tables in PostgreSQL if they don't exist
Base.metadata.create_all(bind=engine)

import asyncio
from contextlib import asynccontextmanager
from app.services.scheduler import auto_scrape_loop

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start auto-scraper in background on boot
    task = None
    if settings.AUTO_SCRAPER_ENABLED:
        task = asyncio.create_task(auto_scrape_loop())

    if settings.WARM_EMBEDDINGS_ON_STARTUP:
        from app.core.database import SessionLocal
        from app.services.matching_engine import warm_job_embeddings
        with SessionLocal() as db:
            warm_job_embeddings(db)

    yield
    # Clean shutdown
    if task:
        task.cancel()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    lifespan=lifespan
)

# Enable CORS for Flutter mobile client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.auth import router as auth_router
from app.api.profile import router as profile_router
from app.api.skills import router as skills_router
from app.api.jobs import router as jobs_router
from app.api.sources import router as sources_router
from app.api.saved_jobs import router as saved_jobs_router
from app.api.recommendations import router as recommendations_router
from app.api.admin import router as admin_router

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(profile_router, prefix=settings.API_V1_STR)
app.include_router(skills_router, prefix=settings.API_V1_STR)
app.include_router(sources_router, prefix=settings.API_V1_STR)
app.include_router(jobs_router, prefix=settings.API_V1_STR)
app.include_router(saved_jobs_router, prefix=settings.API_V1_STR)
app.include_router(recommendations_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)

@app.get(f"{settings.API_V1_STR}/health", tags=["System"])
@app.get("/health", tags=["System"])
def health_check():
    """EP-01 Health Check Endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/", tags=["System"])
def root():
    return {
        "message": "Welcome to JobMatch Cambodia API",
        "docs": f"{settings.API_V1_STR}/docs"
    }
