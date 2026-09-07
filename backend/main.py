from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import engine, Base, ensure_sqlite_schema
from app.core.logging_config import setup_logging, get_logger
from app.core.exceptions import register_exception_handlers

# Routers
from app.routers.analyze import router as analyze_router
from app.routers.history import router as history_router
from app.routers.health import router as health_router
from app.routers.blockchain import router as blockchain_router

# Setup configurations
settings = get_settings()
setup_logging(debug=settings.DEBUG)
logger = get_logger("main")

# Database Initialisation
try:
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_schema()
    logger.info("Database schema initialized successfully.")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

# FastAPI Application
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
)

# CORS Middleware
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Custom Exception Handlers
register_exception_handlers(app)

# Include Routers
app.include_router(analyze_router, prefix="/api", tags=["Analysis"])
app.include_router(history_router, prefix="/api", tags=["History"])
app.include_router(health_router, prefix="/api", tags=["System"])
app.include_router(blockchain_router, prefix="/api/blockchain", tags=["Blockchain"])

@app.get("/", tags=["System"])
async def root():
    return {
        "message": "Welcome to IdentityX API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
