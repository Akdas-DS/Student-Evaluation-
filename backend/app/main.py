import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.config import CORS_ORIGINS
from app.routers import auth_router, admin_router, teacher_router, student_router
from app.seed import seed_database

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="K.T. Risk Prediction System",
    description="Student K.T. Risk Prediction & Adaptive Learning Recommendation System",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(teacher_router.router)
app.include_router(student_router.router)


@app.on_event("startup")
def on_startup():
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Running seed data...")
    seed_database()
    logger.info("Server ready.")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "kt-risk-prediction"}
