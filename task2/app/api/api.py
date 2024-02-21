from fastapi import APIRouter

from app.api.endpoints import storage, transaction

api_router = APIRouter()

api_router.include_router(storage.router, prefix="/storage", tags=["Storage"])
api_router.include_router(transaction.router, prefix="/transaction", tags=["Transaction"])
