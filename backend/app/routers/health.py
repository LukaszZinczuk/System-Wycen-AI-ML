"""
Health check and metrics endpoints.
Provides endpoints for monitoring, load balancers, and orchestrators.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import os
import platform
import psutil
from typing import Dict, Any

from app.database import get_db
from app.services.ml_service import ml_service

router = APIRouter()


@router.get("/health")
def health_check():
    """
    Basic health check endpoint.
    Used by load balancers and orchestrators (K8s, ECS) for liveness probes.
    
    Returns:
        dict: Simple health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check endpoint.
    Verifies all dependencies are ready to serve traffic.
    Used by K8s/ECS for readiness probes.
    
    Returns:
        dict: Readiness status with component details
    """
    checks = {
        "database": False,
        "ml_model": False,
    }
    all_healthy = True
    
    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        all_healthy = False
        checks["database_error"] = str(e)
    
    # Check ML model availability
    try:
        if ml_service.model is not None and ml_service.encoder is not None:
            checks["ml_model"] = True
        else:
            all_healthy = False
            checks["ml_model_error"] = "Model not loaded"
    except Exception as e:
        all_healthy = False
        checks["ml_model_error"] = str(e)
    
    status_code = 200 if all_healthy else 503
    
    if not all_healthy:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "checks": checks,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
    
    return {
        "status": "ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/health/live")
def liveness_check():
    """
    Liveness check endpoint.
    Simple check to verify the application is running.
    
    Returns:
        dict: Liveness status
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/health/detailed")
def detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed health check with system metrics.
    For internal monitoring and debugging.
    
    Returns:
        dict: Comprehensive health information
    """
    # System metrics
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": os.environ.get("APP_VERSION", "1.0.0"),
        "environment": os.environ.get("ENVIRONMENT", "development"),
        
        "system": {
            "hostname": platform.node(),
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
        },
        
        "memory": {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_percent": memory.percent,
        },
        
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "used_percent": round(disk.percent, 1),
        },
        
        "components": {
            "database": {"status": "unknown"},
            "ml_model": {"status": "unknown"},
        }
    }
    
    # Check database
    try:
        start = datetime.utcnow()
        db.execute(text("SELECT 1"))
        latency = (datetime.utcnow() - start).total_seconds() * 1000
        health_data["components"]["database"] = {
            "status": "healthy",
            "latency_ms": round(latency, 2)
        }
    except Exception as e:
        health_data["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_data["status"] = "degraded"
    
    # Check ML model
    try:
        if ml_service.model is not None:
            # Test prediction
            start = datetime.utcnow()
            ml_service.predict(100, "Mazowieckie", True, 20000, 3, 0.3)
            latency = (datetime.utcnow() - start).total_seconds() * 1000
            health_data["components"]["ml_model"] = {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "model_type": type(ml_service.model).__name__
            }
        else:
            health_data["components"]["ml_model"] = {
                "status": "unhealthy",
                "error": "Model not loaded"
            }
            health_data["status"] = "degraded"
    except Exception as e:
        health_data["components"]["ml_model"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_data["status"] = "degraded"
    
    return health_data


@router.get("/metrics")
def get_metrics():
    """
    Prometheus-compatible metrics endpoint.
    
    Returns:
        str: Metrics in Prometheus format
    """
    from app.middleware.logging_middleware import MetricsMiddleware
    
    metrics = MetricsMiddleware.get_metrics()
    memory = psutil.virtual_memory()
    
    # Format as Prometheus metrics
    prometheus_output = f"""# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total {metrics['total_requests']}

# HELP http_errors_total Total number of HTTP errors
# TYPE http_errors_total counter
http_errors_total {metrics['total_errors']}

# HELP http_request_duration_seconds Average HTTP request duration
# TYPE http_request_duration_seconds gauge
http_request_duration_seconds {metrics['average_duration_seconds']}

# HELP process_memory_bytes Process memory usage
# TYPE process_memory_bytes gauge
process_memory_bytes {memory.used}

# HELP process_cpu_percent Process CPU usage
# TYPE process_cpu_percent gauge
process_cpu_percent {psutil.cpu_percent()}
"""
    
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content=prometheus_output, media_type="text/plain")
