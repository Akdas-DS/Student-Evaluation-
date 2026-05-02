import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "dev-fallback-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kt_risk.db")
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://localhost:5175,"
        "http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175"
    ).split(",")
    if origin.strip()
]
