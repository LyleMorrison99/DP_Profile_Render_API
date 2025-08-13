from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import os

# -------------------
# Environment Variables
# -------------------
API_KEY = os.getenv("db5297c2-54a3-4d3a-9a3b-cf1b972d8e8f")
DB_USER = os.getenv("ugopzqgagai7h")
DB_PASSWORD = os.getenv("StankySushiBigMomma2025?")
DB_HOST = os.getenv("giowm1136.siteground.biz")
DB_NAME = os.getenv("dbhutvbrbdxm0c")

DATABASE_URL =mysql+pymysql://ugopzqgagai7h:StankySushiBigMomma2025?@giowm1136.siteground.biz:3306/dbhutvbrbdxm0c
engine = create_engine(DATABASE_URL)

# -------------------
# API Key Security
# -------------------
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

def require_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return api_key

# -------------------
# App init + CORS
# -------------------
app = FastAPI()

origins = [
    "https://dynastypulse.com",  # Your WordPress site URL
    # Add other allowed origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins= origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------
# Cache: per limit value
# -------------------
cache_store = {}  # { limit: { "data": [...], "expiry": datetime } }

# -------------------
# Routes
# -------------------
@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/view")
def get_view(limit: int = 100, _=Depends(require_api_key)):
    now = datetime.utcnow()

    # Check cache for this limit
    if limit in cache_store:
        cache_entry = cache_store[limit]
        if cache_entry["expiry"] > now:
            return {"rows": cache_entry["data"], "cached": True}

    try:
        with engine.connect() as conn:
            query = text("SELECT * FROM consolidated_rankings_site_view LIMIT :limit")
            result = conn.execute(query, {"limit": limit})
            rows = [dict(row._mapping) for row in result]

        # Store in cache
        cache_store[limit] = {
            "data": rows,
            "expiry": now + timedelta(minutes=5)  # adjust cache time
        }

        return {"rows": rows, "cached": False}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
