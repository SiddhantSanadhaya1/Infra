import enum
import os
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Column, Date, DateTime, Enum, ForeignKey, Numeric, String, Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/insureco")


engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


# ── Enums ─────────────────────────────────────────────────────────────────────

class PolicyType(str, enum.Enum):
    AUTO = "AUTO"
    HOME = "HOME"
    LIFE = "LIFE"
    COMMERCIAL = "COMMERCIAL"


class PolicyStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"


class ClaimStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"


# ── Models ────────────────────────────────────────────────────────────────────

class Policyholder(Base):
    __tablename__ = "policyholders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(30))
    date_of_birth = Column(Date)
    address = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    policies = relationship("Policy", back_populates="policyholder", lazy="select")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policyholder_id = Column(UUID(as_uuid=True), ForeignKey("policyholders.id", ondelete="RESTRICT"), nullable=False, index=True)
    policy_type = Column(Enum(PolicyType), nullable=False)
    policy_number = Column(String(50), nullable=False, unique=True, index=True)
    premium_amount = Column(Numeric(12, 2), nullable=False)
    coverage_amount = Column(Numeric(14, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(PolicyStatus), nullable=False, default=PolicyStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    policyholder = relationship("Policyholder", back_populates="policies")
    claims = relationship("Claim", back_populates="policy", lazy="select")
    documents = relationship("Document", back_populates="policy", lazy="select")


class Claim(Base):
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id", ondelete="RESTRICT"), nullable=False, index=True)
    claim_number = Column(String(50), nullable=False, unique=True, index=True)
    claim_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    amount_requested = Column(Numeric(14, 2), nullable=False)
    amount_approved = Column(Numeric(14, 2), nullable=True)
    status = Column(Enum(ClaimStatus), nullable=False, default=ClaimStatus.SUBMITTED)
    incident_date = Column(Date, nullable=False)
    filed_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    policy = relationship("Policy", back_populates="claims")
    documents = relationship("Document", back_populates="claim", lazy="select")


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="SET NULL"), nullable=True, index=True)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id", ondelete="SET NULL"), nullable=True, index=True)
    document_type = Column(String(100), nullable=False)
    file_key = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    claim = relationship("Claim", back_populates="documents")
    policy = relationship("Policy", back_populates="documents")


# ── Session dependency ─────────────────────────────────────────────────────────

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
