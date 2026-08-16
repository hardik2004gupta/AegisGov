from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {
        "status": "healthy",
        "service": "aegisgov-api",
        "version": "0.1.0",
    }
