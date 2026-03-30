import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config.database import Policyholder, get_db
from src.services.queue_service import enqueue_job

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class PolicyholderCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None


class PolicyholderUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class PolicyholderOut(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    date_of_birth: Optional[date]
    address: Optional[str]

    model_config = {"from_attributes": True}


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/policyholders", response_model=PolicyholderOut, status_code=status.HTTP_201_CREATED)
async def create_policyholder(payload: PolicyholderCreate, db: AsyncSession = Depends(get_db)):
    # Check for duplicate email
    existing = await db.execute(
        select(Policyholder).where(Policyholder.email == payload.email)
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Email already registered")

    ph = Policyholder(**payload.model_dump())
    db.add(ph)
    await db.flush()
    await db.refresh(ph)

    # Enqueue welcome email
    try:
        enqueue_job("WELCOME_EMAIL", {
            "policyholder_id": str(ph.id),
            "email": ph.email,
            "first_name": ph.first_name,
        })
    except Exception:
        pass  # Non-fatal for demo

    return ph


@router.get("/policyholders", response_model=List[PolicyholderOut])
async def list_policyholders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Policyholder).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/policyholders/{policyholder_id}", response_model=PolicyholderOut)
async def get_policyholder(policyholder_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Policyholder)
        .options(selectinload(Policyholder.policies))
        .where(Policyholder.id == policyholder_id)
    )
    ph = result.scalars().first()
    if not ph:
        raise HTTPException(status_code=404, detail="Policyholder not found")
    return ph


@router.put("/policyholders/{policyholder_id}", response_model=PolicyholderOut)
async def update_policyholder(
    policyholder_id: uuid.UUID,
    payload: PolicyholderUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Policyholder).where(Policyholder.id == policyholder_id))
    ph = result.scalars().first()
    if not ph:
        raise HTTPException(status_code=404, detail="Policyholder not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ph, field, value)

    await db.flush()
    await db.refresh(ph)
    return ph


@router.delete("/policyholders/{policyholder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policyholder(policyholder_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Policyholder).where(Policyholder.id == policyholder_id))
    ph = result.scalars().first()
    if not ph:
        raise HTTPException(status_code=404, detail="Policyholder not found")
    await db.delete(ph)
