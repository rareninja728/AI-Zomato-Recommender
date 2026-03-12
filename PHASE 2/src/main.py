from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router

app = FastAPI(
    title="Zomato AI Recommendation API",
    description="Backend API to process user restaurant preferences and return recommendations.",
    version="1.0.0"
)

# Allow CORS for UI deployment (Streamlit/Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Should be tightened for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Zomato AI API. See /docs for the swagger playground."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
