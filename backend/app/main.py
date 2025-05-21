from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router
from app.core.config import settings
from app.services.llm import vector_search_available, embedding_model

app = FastAPI(
    title="AI Chat Agent Platform",
    description="Multi-tenant SaaS platform for AI chat agents",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["Authorization"]
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to the AI Chat Agent Platform API"}

@app.get("/vector-status")
async def vector_status():
    """Check if vector search is available and working"""
    status = {
        "vector_search_available": vector_search_available,
        "model_loaded": embedding_model is not None,
        "model_name": embedding_model.__class__.__name__ if embedding_model else None
    }
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)