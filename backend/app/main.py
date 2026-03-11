from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging

from app.routers import upload
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import SecurityHeadersMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Sales Insight Automator API starting up...")
    yield
    logger.info("Sales Insight Automator API shutting down...")


app = FastAPI(
    title="Sales Insight Automator API",
    description="""
## Sales Insight Automator

Upload CSV/Excel sales data files and receive AI-generated executive summaries delivered to your inbox.

### Features
- 📊 **File Upload** – Supports `.csv` and `.xlsx` formats (max 10MB)
- 🤖 **AI Analysis** – Powered by OpenAI GPT for intelligent narrative summaries
- 📧 **Email Delivery** – Sends polished reports via SMTP
- 🔒 **Secured Endpoints** – Rate limiting, CORS, input validation, and security headers

### Flow
1. POST `/api/v1/upload` with your data file and recipient email
2. The API parses the data, sends it to the LLM engine
3. A formatted summary is emailed to the recipient

### Security
All endpoints are protected by:
- Rate limiting (10 requests/minute per IP)
- File type and size validation
- Input sanitization
- Security headers (X-Frame-Options, CSP, etc.)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to specific domains in production
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# Rate Limiting
app.add_middleware(RateLimitMiddleware, max_requests=10, window_seconds=60)

# Include routers
app.include_router(upload.router, prefix="/api/v1", tags=["Analysis"])


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint – service health check."""
    return {
        "service": "Sales Insight Automator",
        "status": "operational",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "components": {
            "api": "up",
            "ai_engine": "ready",
            "email_service": "ready",
        }
    }
