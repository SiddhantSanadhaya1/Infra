import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import Document, get_db
from src.services.document_service import generate_presigned_url, generate_download_url

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class PresignRequest(BaseModel):
    file_name: str
    document_type: str
    content_type: str
    claim_id: Optional[uuid.UUID] = None
    policy_id: Optional[uuid.UUID] = None


class PresignResponse(BaseModel):
    upload_url: str
    file_key: str


class DocumentRegister(BaseModel):
    file_key: str
    file_name: str
    document_type: str
    claim_id: Optional[uuid.UUID] = None
    policy_id: Optional[uuid.UUID] = None


class DocumentOut(BaseModel):
    id: uuid.UUID
    document_type: str
    file_name: str
    claim_id: Optional[uuid.UUID]
    policy_id: Optional[uuid.UUID]

    model_config = {"from_attributes": True}


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/documents/presign", response_model=PresignResponse)
async def get_presigned_url(payload: PresignRequest):
    try:
        upload_url, file_key = generate_presigned_url(
            file_name=payload.file_name,
            document_type=payload.document_type,
            content_type=payload.content_type,
            claim_id=str(payload.claim_id) if payload.claim_id else None,
            policy_id=str(payload.policy_id) if payload.policy_id else None,
        )
        return PresignResponse(upload_url=upload_url, file_key=file_key)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate presigned URL: {exc}")


@router.post("/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def register_document(payload: DocumentRegister, db: AsyncSession = Depends(get_db)):
    doc = Document(
        file_key=payload.file_key,
        file_name=payload.file_name,
        document_type=payload.document_type,
        claim_id=payload.claim_id,
        policy_id=payload.policy_id,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return doc


@router.get("/documents/{document_id}")
async def get_document_download_url(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        download_url = generate_download_url(doc.file_key)
        return {"download_url": download_url, "file_name": doc.file_name}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {exc}")
