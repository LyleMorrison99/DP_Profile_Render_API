import os, secrets
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from pydantic import BaseSettings
from sqlalchemy import create_engine, text

class Settings(BaseSettings):
    DATABASE_URL: str
    API_KEY: str
    class Config:
        env_file = ".env"   # optional for local dev

settings = Settings()

# SQLAlchemy sync engine (simple, reliable)
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# API key header dependency
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)
def require_api_key(api_key: str = Depends(api_key_header)):
    if not secrets.compare_digest(api_key, settings.API_KEY):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key")
    return True

# Hide docs in production (optional)
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/view")
def read_view(limit: int = 100, _=Depends(require_api_key)):
    # Use a sync endpoint so blocking DB calls run in a threadpool (FastAPI handles this)
    with engine.connect() as conn:
        q = text("SELECT * FROM consolidated_rankings_site_view LIMIT :limit")
        result = conn.execute(q, {"limit": limit})
        rows = [dict(r._mapping) for r in result]
    return {"rows": rows}
