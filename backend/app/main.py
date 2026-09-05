from fastapi import FastAPI

from .config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="SIH PS 26034 — Legal Metrology (Packaged Commodities) Rules, 2011 compliance assistant.",
)


@app.get("/")
def root():
    return {"app": settings.app_name, "status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.environment}