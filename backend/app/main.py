import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agent import router as agent_router
from app.api.approvals import router as approvals_router
from app.api.audit import router as audit_router
from app.api.health import router as health_router
from app.api.runtime import router as runtime_router
from app.core.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "AegisGov API starting — env=%s port=%s",
        settings.app_env,
        settings.app_port,
    )
    yield
    logger.info("AegisGov API shutting down")


app = FastAPI(
    title="AegisGov API",
    description=(
        "Secure Runtime Governance & Zero-Trust Execution Gateway for Agentic AI. "
        "Agents propose actions; AegisGov owns execution authority."
    ),
    version="0.1.0",
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url="/redoc" if settings.app_env == "development" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://frontend:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Trace-ID"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(health_router)
app.include_router(agent_router, prefix="/api/v1")
app.include_router(approvals_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(runtime_router, prefix="/api/v1")
