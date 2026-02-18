import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, SessionLocal
from app.routers import auth, companies, offers, admin
from app.routers.health import router as health_router
from app.routers.monte_carlo import router as monte_carlo_router
from app.models import models
from app.services.ml_service import ml_service
from app.core.logging import setup_logging, get_logger
from app.middleware.logging_middleware import RequestLoggingMiddleware, MetricsMiddleware
from app.middleware.security_middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    InputSanitizationMiddleware
)

# Setup logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
JSON_LOGS = os.environ.get("JSON_LOGS", "false").lower() == "true"
setup_logging(level=LOG_LEVEL, json_output=JSON_LOGS)

logger = get_logger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="System Wycen AI+ML",
    description="""
    ## B2B Pricing System with AI Scoring
    
    This API provides:
    * **Pricing Calculations** - AI-powered pricing for B2B offers
    * **Company Management** - CRUD operations for companies
    * **Offer Management** - Create and track pricing offers
    * **Admin Dashboard** - Analytics and reporting
    
    ### Authentication
    Use JWT Bearer token authentication. Get token via `/api/auth/login`.
    
    ### AI Scoring
    - **ML Score (70%)**: Random Forest model trained on historical data
    - **Rule Score (30%)**: Business rules based on company attributes
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    }
)

# Security Middleware (order matters - first added = last executed)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(InputSanitizationMiddleware, block_suspicious=False)
app.add_middleware(RateLimitMiddleware, requests_per_minute=100, requests_per_hour=2000)

# Observability Middleware
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# CORS
origins = [
    "http://localhost",
    "http://localhost:4200",
    "http://localhost:8080",
    os.environ.get("FRONTEND_URL", "http://localhost:4200"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID", "X-Request-Duration-Ms", "X-RateLimit-Remaining"],
)

# Seed Industries and Admin User (for demo)
@app.on_event("startup")
def startup_event():
    logger.info("Application starting up...")
    db = SessionLocal()
    # Seed Industries
    if not db.query(models.Industry).first():
        industries = [
            {"name": "IT", "risk_factor": 0.2},
            {"name": "Produkcja", "risk_factor": 0.7},
            {"name": "Budownictwo", "risk_factor": 0.8},
            {"name": "Medyczna", "risk_factor": 0.4},
            {"name": "Usługi", "risk_factor": 0.5},
        ]
        for ind in industries:
            db_ind = models.Industry(**ind)
            db.add(db_ind)
        db.commit()
        logger.info("Seeded Industries")
        
    # Seed Admin
    from app.core.security import get_password_hash
    admin_user = db.query(models.User).filter(models.User.email == "admin@example.com").first()
    if not admin_user:
        admin_user = models.User(
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            role="admin"
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        logger.info("Seeded Admin User: admin@example.com / admin123")
    
    # Seed Demo Company for Admin
    if not db.query(models.Company).filter(models.Company.name == "Demo Company").first():
        # Get an industry, e.g. IT (which we know we seeded first)
        it_industry = db.query(models.Industry).filter(models.Industry.name == "IT").first()
        if it_industry and admin_user:
            demo_company = models.Company(
                name="Demo Company",
                industry_id=it_industry.id,
                user_id=admin_user.id
            )
            db.add(demo_company)
            db.commit()
            logger.info("Seeded Demo Company for Admin")
    
    db.close()
    logger.info("Application startup complete")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("Application shutting down...")


# Health & Metrics Routers (no auth required)
app.include_router(health_router, tags=["health"])

# API Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(offers.router, prefix="/api/offers", tags=["offers"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(monte_carlo_router, tags=["monte-carlo"])

@app.get("/")
def read_root():
    return {"message": "Welcome to System Wycen AI+ML API"}
