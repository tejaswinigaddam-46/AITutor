from fastapi import APIRouter, Depends
from app.api.v1.endpoints import rag, document
from app.core.security import get_api_key

api_router = APIRouter(dependencies=[Depends(get_api_key)])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(document.router, prefix="/documents", tags=["documents"])

@api_router.get("/health")
async def health_check():
    return {"status": "ok", "message": "API V1 is healthy"}
