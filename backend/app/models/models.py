from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Numeric, Date, DateTime, ForeignKey, CheckConstraint, Float, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    saved_jobs = relationship("SavedJob", back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    full_name = Column(String(150), nullable=False)
    education = Column(String(150), nullable=True)
    experience_level = Column(String(50), default="entry", nullable=False)
    preferred_role = Column(String(100), nullable=False)
    preferred_location = Column(String(100), default="Phnom Penh", nullable=False)
    expected_salary = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="profile")
    skills = relationship("ProfileSkill", back_populates="profile", cascade="all, delete-orphan")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    category = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    profile_skills = relationship("ProfileSkill", back_populates="skill", cascade="all, delete-orphan")
    job_skills = relationship("JobSkill", back_populates="skill", cascade="all, delete-orphan")


class ProfileSkill(Base):
    __tablename__ = "profile_skills"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    profile = relationship("Profile", back_populates="skills")
    skill = relationship("Skill", back_populates="profile_skills")


# -----------------------------------------------------------------------------
# Master Sources Table (Data Aggregation Channels & Portals)
# -----------------------------------------------------------------------------
class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    platform_type = Column(String(50), nullable=False)  # telegram | web_portal | api
    url = Column(Text, nullable=False)
    logo_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    scrape_interval_minutes = Column(Integer, default=60, nullable=False)
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    jobs = relationship("JobListing", back_populates="job_source")


class JobListing(Base):
    __tablename__ = "job_listings"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), default="Phnom Penh", nullable=False)
    experience_level = Column(String(50), default="entry", nullable=False)
    job_type = Column(String(50), default="full-time", nullable=False)
    salary_min = Column(Numeric(10, 2), nullable=True)
    salary_max = Column(Numeric(10, 2), nullable=True)
    salary_currency = Column(String(10), default="USD", nullable=False)
    salary_period = Column(String(20), default="monthly", nullable=True)  # monthly | yearly | hourly | daily
    is_negotiable = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=False)
    source = Column(String(50), nullable=False)
    source_url = Column(Text, unique=True, nullable=False)
    company_url = Column(Text, nullable=True)                       # company website link
    company_logo_url = Column(Text, nullable=True)                  # company logo image URL
    raw_title = Column(String(255), nullable=True)                  # original uncleaned title
    normalized_location = Column(String(255), nullable=True)        # standardized location for filtering
    openings = Column(Integer, default=1, nullable=True)            # total number of available openings
    source_post_id = Column(String(100), nullable=True, index=True) # external platform post ID
    posted_at = Column(Date, nullable=True)
    deadline = Column(Date, nullable=True)
    work_arrangement = Column(String(50), nullable=True)            # on-site | hybrid | remote
    job_category = Column(String(100), default="Unknown", nullable=False, index=True)
    job_subcategory = Column(String(100), default="Unknown", nullable=False)
    job_level = Column(String(50), default="Unknown", nullable=False, index=True)
    classification_confidence = Column(Float, nullable=True)
    classification_source = Column(String(20), default="rule", nullable=False)     # jev | rule
    scraped_at = Column(DateTime(timezone=True), nullable=True)     # when the scraper last collected this
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String(20), default="active", nullable=False)   # active | expired | closed
    application_url = Column(Text, nullable=True)                   # direct apply link (if different from source_url)
    apply_email = Column(String(255), nullable=True)
    apply_phone = Column(String(100), nullable=True)
    apply_telegram = Column(String(100), nullable=True)
    dedup_hash = Column(String(64), nullable=True, index=True)      # SHA-256 fingerprint for duplicate detection
    duplicate_of = Column(Integer, ForeignKey("job_listings.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    skills = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")
    saved_by = relationship("SavedJob", back_populates="job", cascade="all, delete-orphan")
    job_source = relationship("Source", back_populates="jobs")

    __table_args__ = (
        UniqueConstraint("source", "source_post_id", name="uq_job_listings_source_post_id"),
    )


class JobSkill(Base):
    __tablename__ = "job_skills"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    job = relationship("JobListing", back_populates="skills")
    skill = relationship("Skill", back_populates="job_skills")


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("job_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="saved_jobs")
    job = relationship("JobListing", back_populates="saved_by")


class EmailOTP(Base):
    __tablename__ = "email_otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    code = Column(String(6), nullable=False)
    purpose = Column(String(50), default="login_or_verify", nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# -----------------------------------------------------------------------------
# Dedicated Telegram Jobs Table (all 33 fields, multi-job support)
# -----------------------------------------------------------------------------
class TelegramJob(Base):
    __tablename__ = "telegram_jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=True, index=True)
    location = Column(String(255), nullable=True)
    normalized_location = Column(String(255), nullable=True)
    work_arrangement = Column(String(50), nullable=True)     # onsite | hybrid | remote
    job_type = Column(String(50), nullable=True)             # internship | full_time | part_time | contract
    experience_level = Column(String(50), nullable=True)     # entry | junior | mid | senior
    description = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=False)                  # Original message for re-parsing
    language = Column(String(20), nullable=True)             # en | km | mixed

    # Salary
    salary_min = Column(Numeric(10, 2), nullable=True)
    salary_max = Column(Numeric(10, 2), nullable=True)
    salary_currency = Column(String(10), default="USD", nullable=True)
    salary_period = Column(String(20), default="month", nullable=True)
    is_negotiable = Column(Boolean, default=False, nullable=True)

    # Dates
    posted_at = Column(Date, nullable=False)
    deadline = Column(Date, nullable=True)
    message_edited_at = Column(DateTime(timezone=True), nullable=True)

    # Application / Contact methods
    application_url = Column(Text, nullable=True)
    apply_email = Column(String(255), nullable=True)
    apply_phone = Column(String(100), nullable=True)
    apply_telegram = Column(String(100), nullable=True)      # @recruiter username

    # Source
    source_platform = Column(String(50), default="telegram", nullable=False)
    source = Column(String(100), nullable=False, index=True) # e.g. @internshipscambodia
    source_post_id = Column(String(100), nullable=False, index=True)
    job_index = Column(Integer, default=0, nullable=False)   # 0 for single; 0, 1, 2 for multi-job posts
    source_url = Column(Text, nullable=True)

    # Quality & Lifecycle
    dedup_hash = Column(String(64), nullable=False, index=True)
    parse_confidence = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expired_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("source", "source_post_id", "job_index", name="uq_telegram_channel_post_job"),
    )


# -----------------------------------------------------------------------------
# Dedicated Web Jobs Table (Web portals: BongThom, JobNet, CamboJob, Khmer24)
# -----------------------------------------------------------------------------
class WebJob(Base):
    __tablename__ = "web_jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    raw_title = Column(String(255), nullable=True)
    company = Column(String(255), nullable=False, index=True)
    company_url = Column(Text, nullable=True)
    company_logo_url = Column(Text, nullable=True)
    location = Column(String(255), default="Phnom Penh", nullable=False)
    normalized_location = Column(String(255), nullable=True)
    work_arrangement = Column(String(50), nullable=True)
    job_type = Column(String(50), default="full_time", nullable=True)
    experience_level = Column(String(50), default="entry", nullable=True)

    # Salary
    salary_min = Column(Numeric(10, 2), nullable=True)
    salary_max = Column(Numeric(10, 2), nullable=True)
    salary_currency = Column(String(10), default="USD", nullable=True)
    salary_period = Column(String(20), default="month", nullable=True)
    is_negotiable = Column(Boolean, default=False, nullable=True)
    openings = Column(Integer, default=1, nullable=True)

    description = Column(Text, nullable=False)
    source_portal = Column(String(100), nullable=False, index=True)  # BongThom, JobNet, etc.
    source_url = Column(Text, unique=True, nullable=False)
    source_job_id = Column(String(100), nullable=True)
    application_url = Column(Text, nullable=True)

    # Dates
    posted_at = Column(Date, nullable=True)
    deadline = Column(Date, nullable=True)

    # Quality & Lifecycle
    dedup_hash = Column(String(64), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

