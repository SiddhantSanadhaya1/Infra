import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config.database import (
    Claim, Document, Policy, PolicyStatus, PolicyType, get_db,
)
from src.services.policy_service import generate_policy_number

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class PolicyCreate(BaseModel):
    policyholder_id: uuid.UUID
    policy_type: PolicyType
    premium_amount: Decimal
    coverage_amount: Decimal
    start_date: date
    end_date: date
    status: Optional[PolicyStatus] = PolicyStatus.PENDING


class PolicyUpdate(BaseModel):
    premium_amount: Optional[Decimal] = None
    coverage_amount: Optional[Decimal] = None
    end_date: Optional[date] = None
    status: Optional[PolicyStatus] = None


class PolicyOut(BaseModel):
    id: uuid.UUID
    policyholder_id: uuid.UUID
    policy_type: PolicyType
    policy_number: str
    premium_amount: Decimal
    coverage_amount: Decimal
    start_date: date
    end_date: date
    status: PolicyStatus

    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: uuid.UUID
    document_type: str
    file_name: str
    uploaded_at: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/policies", response_model=PolicyOut, status_code=status.HTTP_201_CREATED)
async def create_policy(payload: PolicyCreate, db: AsyncSession = Depends(get_db)):
    policy_number = generate_policy_number(payload.policy_type.value)
    policy = Policy(
        **payload.model_dump(),
        policy_number=policy_number,
    )
    db.add(policy)
    await db.flush()
    await db.refresh(policy)
    return policy


@router.get("/policies", response_model=List[PolicyOut])
async def list_policies(
    status: Optional[PolicyStatus] = Query(None),
    policy_type: Optional[PolicyType] = Query(None),
    policyholder_id: Optional[uuid.UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    q = select(Policy)
    if status:
        q = q.where(Policy.status == status)
    if policy_type:
        q = q.where(Policy.policy_type == policy_type)
    if policyholder_id:
        q = q.where(Policy.policyholder_id == policyholder_id)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/policies/{policy_id}", response_model=PolicyOut)
async def get_policy(policy_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Policy)
        .options(selectinload(Policy.claims))
        .where(Policy.id == policy_id)
    )
    policy = result.scalars().first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.put("/policies/{policy_id}", response_model=PolicyOut)
async def update_policy(
    policy_id: uuid.UUID,
    payload: PolicyUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalars().first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)

    await db.flush()
    await db.refresh(policy)
    return policy


@router.get("/policies/{policy_id}/documents", response_model=List[DocumentOut])
async def list_policy_documents(policy_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document).where(Document.policy_id == policy_id)
    )
    return result.scalars().all()
