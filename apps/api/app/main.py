from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.settings import settings

app = FastAPI(title="MediTalk API", description="API foundation for the MediTalk platform.", version="0.1.0", docs_url="/docs" if settings.app_env == "development" else None, redoc_url=None)
# Development CORS only; restrict origins before deployment.
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=False, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])

@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "meditalk-api", "version": "0.1.0"}
