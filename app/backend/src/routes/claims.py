import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config.database import Claim, ClaimStatus, Policy, PolicyStatus, get_db
from src.services.claims_service import generate_claim_number, validate_claim_against_policy
from src.services.queue_service import enqueue_job

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class ClaimCreate(BaseModel):
    policy_id: uuid.UUID
    claim_type: str
    description: str
    amount_requested: Decimal
    incident_date: date


class ClaimUpdate(BaseModel):
    claim_type: Optional[str] = None
    description: Optional[str] = None
    amount_requested: Optional[Decimal] = None
    status: Optional[ClaimStatus] = None


class ApprovePayload(BaseModel):
    amount_approved: Decimal
    notes: Optional[str] = None


class RejectPayload(BaseModel):
    reason: str


class ClaimOut(BaseModel):
    id: uuid.UUID
    policy_id: uuid.UUID
    claim_number: str
    claim_type: str
    description: str
    amount_requested: Decimal
    amount_approved: Optional[Decimal]
    status: ClaimStatus
    incident_date: date
    filed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/claims", response_model=ClaimOut, status_code=status.HTTP_201_CREATED)
async def file_claim(payload: ClaimCreate, db: AsyncSession = Depends(get_db)):
    # Fetch policy
    policy_result = await db.execute(select(Policy).where(Policy.id == payload.policy_id))
    policy = policy_result.scalars().first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    # Validate claim against policy
    error = validate_claim_against_policy(policy, payload.amount_requested)
    if error:
        raise HTTPException(status_code=422, detail=error)

    claim_number = generate_claim_number()
    claim = Claim(
        policy_id=payload.policy_id,
        claim_number=claim_number,
        claim_type=payload.claim_type,
        description=payload.description,
        amount_requested=payload.amount_requested,
        incident_date=payload.incident_date,
        status=ClaimStatus.SUBMITTED,
    )
    db.add(claim)
    await db.flush()
    await db.refresh(claim)

    # Enqueue background processing
    try:
        enqueue_job("PROCESS_CLAIM", {
            "claim_id": str(claim.id),
            "claim_number": claim.claim_number,
            "policy_id": str(policy.id),
            "amount_requested": str(payload.amount_requested),
        })
    except Exception:
        pass  # Non-fatal for demo

    return claim


@router.get("/claims", response_model=List[ClaimOut])
async def list_claims(
    status: Optional[ClaimStatus] = Query(None),
    policy_id: Optional[uuid.UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    q = select(Claim)
    if status:
        q = q.where(Claim.status == status)
    if policy_id:
        q = q.where(Claim.policy_id == policy_id)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/claims/{claim_id}", response_model=ClaimOut)
async def get_claim(claim_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Claim)
        .options(selectinload(Claim.documents))
        .where(Claim.id == claim_id)
    )
    claim = result.scalars().first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.put("/claims/{claim_id}", response_model=ClaimOut)
async def update_claim(
    claim_id: uuid.UUID,
    payload: ClaimUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalars().first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(claim, field, value)

    await db.flush()
    await db.refresh(claim)
    return claim


@router.post("/claims/{claim_id}/approve", response_model=ClaimOut)
async def approve_claim(
    claim_id: uuid.UUID,
    payload: ApprovePayload,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalars().first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    if claim.status not in (ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW):
        raise HTTPException(status_code=422, detail=f"Cannot approve claim in status {claim.status}")

    claim.status = ClaimStatus.APPROVED
    claim.amount_approved = payload.amount_approved
    await db.flush()
    await db.refresh(claim)
    return claim


@router.post("/claims/{claim_id}/reject", response_model=ClaimOut)
async def reject_claim(
    claim_id: uuid.UUID,
    payload: RejectPayload,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalars().first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    if claim.status not in (ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW):
        raise HTTPException(status_code=422, detail=f"Cannot reject claim in status {claim.status}")

    claim.status = ClaimStatus.REJECTED
    await db.flush()
    await db.refresh(claim)
    return claim
