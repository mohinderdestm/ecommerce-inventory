from fastapi import APIRouter
from app.core.kafka import kafka_manager

router = APIRouter()


@router.get("/")
async def health_check():
    return {"status": "OK", "kafka": kafka_manager.status()}
