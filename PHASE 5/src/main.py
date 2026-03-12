import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env FIRST — before any other import touches os.environ ────────────
_env_file = Path(__file__).resolve().parent.parent / ".env"
_loaded = load_dotenv(dotenv_path=_env_file, override=True)
print(f"[startup] .env loaded from: {_env_file}  (found={_loaded})")
print("Groq API key loaded:", os.getenv("GROQ_API_KEY") is not None)

# ── Startup diagnostics ──────────────────────────────────────────────────────
_groq_key = os.getenv("GROQ_API_KEY", "")
print(f"[startup] Groq API key loaded (bool): {bool(_groq_key)}")
print(f"[startup] DB_PATH env         : {os.getenv('DB_PATH', '(using default)')}")

# ── Application imports (after env is loaded) ────────────────────────────────
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.api.routes import router
from src.services.analytics_service import init_analytics_db

app = FastAPI(
    title="Zomato AI Recommendation API",
    description="Personalized restaurant recommendations powered by Groq LLM + SQLite.",
    version="1.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Tighten to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# ── Mounting Logic ──────────────────────────────────────────────────────────
frontend_path = (Path(__file__).resolve().parents[2] / "PHASE 4" / "frontend").resolve()

# Serve assets (CSS, JS, etc.) at /static
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

@app.get("/")
async def serve_index():
    from fastapi.responses import FileResponse
    index_file = frontend_path / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"error": "Frontend index.html not found."}

@app.on_event("startup")
async def startup_event():
    init_analytics_db()
    print("[startup] Analytics DB ready.")
    print(f"[startup] Server running on http://0.0.0.0:8000")

@app.get("/api/test-groq")
async def test_groq():
    from src.services.llm_service import get_groq_client
    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Hello, are you working?"}],
            max_tokens=20
        )
        return {
            "status": "success",
            "response": response.choices[0].message.content,
            "api_key_loaded": bool(os.getenv("GROQ_API_KEY"))
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "api_key_loaded": bool(os.getenv("GROQ_API_KEY"))
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
