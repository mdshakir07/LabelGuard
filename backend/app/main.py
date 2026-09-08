from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import dashboard, findings, images, inspections, process, reports, rules
from .auth.router import router as auth_router
from .config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="SIH PS 26034 — Legal Metrology (Packaged Commodities) Rules, 2011 compliance assistant.",
    openapi_tags=[
        {"name": "auth", "description": "Authentication & tokens"},
        {"name": "inspections", "description": "Inspection lifecycle & search"},
        {"name": "images", "description": "Image upload, storage, serving"},
        {"name": "process", "description": "OCR/extraction/rules orchestration"},
        {"name": "findings", "description": "Human review of automated findings"},
        {"name": "reports", "description": "Report generation (PDF)"},
        {"name": "dashboard", "description": "KPIs"},
        {"name": "rules", "description": "Versioned rules administration"},
    ],
)

# Dev/demo CORS: the Next.js app (localhost:3000) calls this API directly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(inspections.router)
app.include_router(images.router)
app.include_router(process.router)
app.include_router(findings.router)
app.include_router(reports.router)
app.include_router(dashboard.router)
app.include_router(rules.router)


@app.get("/")
def root():
    return {"app": settings.app_name, "status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.environment}