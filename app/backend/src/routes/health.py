from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "InsureCo Insurance Portal API",
        "version": "1.0.0",
    }
