import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

# Compatibility alias for external repos calling /ai/query
from app.api.v1.rag import router as rag_router
from app.api.v1.conversation import router as conversation_router
from app.api.v1.document import router as document_router
from app.api.v1.question import router as question_router

app.include_router(rag_router, prefix="/ai", tags=["compatibility"])
app.include_router(conversation_router, prefix="/conversations", tags=["compatibility"])
app.include_router(document_router, prefix="/documents", tags=["compatibility"])
app.include_router(question_router, prefix="/questions", tags=["compatibility"])

@app.get("/health", tags=["compatibility"])
async def health_check():
    return {"status": "ok", "message": "API is healthy"}

@app.get("/")
def root():
    return {"message": "Welcome to AI Tutor RAG API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.BACKEND_PORT, reload=True)
