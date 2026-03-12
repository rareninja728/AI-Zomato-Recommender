import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router

app = FastAPI(
    title="Zomato AI Recommendation API - Phase 3 (Groq LLM)",
    description="Backend API augmenting strict database filters with Groq LLM (Llama 3) for personalized reasoning.",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Welcome to Zomato AI API Phase 3! Endpoints: /api/metadata, /api/recommend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
