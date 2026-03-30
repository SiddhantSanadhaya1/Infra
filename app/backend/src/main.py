import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes import health, policyholders, policies, claims, documents, quotes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("InsureCo Insurance API starting")
    yield
    logger.info("InsureCo Insurance API shutting down")


app = FastAPI(
    title="InsureCo Insurance Portal API",
    description="Policy management and claims processing system for InsureCo Insurance",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(policyholders.router, prefix="/api", tags=["Policyholders"])
app.include_router(policies.router, prefix="/api", tags=["Policies"])
app.include_router(claims.router, prefix="/api", tags=["Claims"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(quotes.router, prefix="/api", tags=["Quotes"])
