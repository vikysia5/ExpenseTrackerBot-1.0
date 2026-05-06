"""
Expense Tracker - FastAPI Application
Main entrypoint
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.core.logger import logger
from src.api.routers import auth_router, tx_router, cat_router

# ============================================
# APP INIT
# ============================================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Expense Tracker REST API - OpenAPI 3.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ============================================
# MIDDLEWARE
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("Request", method=request.method, path=request.url.path)
    try:
        response = await call_next(request)
        logger.info("Response", status=response.status_code, path=request.url.path)
        return response
    except Exception as e:
        logger.error("Unhandled error", path=request.url.path, error=str(e))
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ============================================
# ROUTERS
# ============================================
app.include_router(auth_router, prefix="/api/v1")
app.include_router(tx_router, prefix="/api/v1")
app.include_router(cat_router, prefix="/api/v1")


# ============================================
# HEALTH CHECK
# ============================================
@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


# ============================================
# STARTUP
# ============================================
@app.on_event("startup")
async def startup():
    logger.info("Starting Expense Tracker API", version=settings.APP_VERSION)
    # Setup Observer listeners
    from src.patterns.patterns import event_bus
    async def on_transaction_created(data: dict):
        logger.info("Observer: transaction.created", user=data.get("user_id"))

    event_bus.subscribe("transaction.created", on_transaction_created)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
