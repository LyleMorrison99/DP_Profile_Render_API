import os
import secrets
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine, text
from fastapi.responses import JSONResponse

# Load settings from environment variables
class Settings(BaseSettings):
    DATABASE_URL: str
    API_KEY: str
    class Config:
        env_file = ".env"  # local dev only

settings = Settings()

# Create DB engine
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# API key header dependency
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

def require_api_key(api_key: str = Depends(api_key_header)):
    if not secrets.compare_digest(api_key, settings.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    return True

# Create FastAPI app and enable CORS
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <-- Change to specific domains in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/view")
def read_view(limit: int = 100, _=Depends(require_api_key)):
    try:
        with engine.connect() as conn:
            # Replace 'your_view_name' with your actual MySQL view name
            q = text("SELECT * FROM your_view_name LIMIT :limit")
            result = conn.execute(q, {"limit": limit})
            rows = [dict(r._mapping) for r in result]
        return {"rows": rows}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/")
def root():
    return {"message": "FastAPI running. Use /view with API key to get data."}

