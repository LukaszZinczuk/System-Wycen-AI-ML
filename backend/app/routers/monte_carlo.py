"""
Monte Carlo Simulation Router

Provides API endpoints for price risk analysis using Monte Carlo methods.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas.schemas import (
    MonteCarloRequest, 
    MonteCarloResponse,
    ScenarioAnalysisResponse,
    OfferCreate
)
from app.services.monte_carlo_service import monte_carlo_service, MonteCarloService
from app.services.pricing_service import pricing_service
from app.models.models import User, Company
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monte-carlo", tags=["Monte Carlo Simulation"])


@router.post("/simulate", response_model=MonteCarloResponse)
def run_monte_carlo_simulation(
    request: MonteCarloRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run Monte Carlo simulation for price risk analysis.
    
    Generates probability distribution of prices based on:
    - Market volatility
    - Regional factors
    - Industry risk
    - AI confidence score
    
    Returns:
    - Price distribution statistics (mean, median, std dev)
    - Risk metrics (VaR, CVaR)
    - Percentiles (P5, P25, P50, P75, P95)
    - Histogram data for visualization
    """
    
    # First, calculate deterministic price
    offer_data = OfferCreate(
        company_id=request.company_id,
        employees_count=request.employees_count,
        region=request.region,
        premium_48h=request.premium_48h,
        ml_feature_avg_order_value=request.ml_feature_avg_order_value,
        ml_feature_offers_count=request.ml_feature_offers_count
    )
    
    pricing_result = pricing_service.calculate_price_and_score(offer_data, db)
    
    # Get industry risk factor
    company_industry_risk = 0.5
    if request.company_id:
        company = db.query(Company).filter(Company.id == request.company_id).first()
        if company and company.industry:
            company_industry_risk = company.industry.risk_factor
    
    # Create service with custom simulation count if needed
    mc_service = MonteCarloService(n_simulations=request.n_simulations)
    
    # Run Monte Carlo simulation
    result = mc_service.simulate_price(
        base_price=pricing_result.final_price,
        employees_count=request.employees_count,
        region=request.region,
        premium=request.premium_48h,
        industry_risk_factor=company_industry_risk,
        ai_score=pricing_result.ai_score
    )
    
    result_dict = result.to_dict()
    
    return MonteCarloResponse(
        mean_price=result_dict["mean_price"],
        median_price=result_dict["median_price"],
        std_dev=result_dict["std_dev"],
        percentiles=result_dict["percentiles"],
        risk_metrics=result_dict["risk_metrics"],
        confidence_interval_95=result_dict["confidence_interval_95"],
        simulation_quality=result_dict["simulation_quality"],
        histogram=result_dict["histogram"],
        deterministic_price=pricing_result.final_price,
        ai_score=pricing_result.ai_score,
        priority_level=pricing_result.priority_level
    )


@router.post("/scenarios", response_model=ScenarioAnalysisResponse)
def get_scenario_analysis(
    request: MonteCarloRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate best/worst/expected case scenarios for pricing.
    
    Useful for:
    - Budget planning
    - Risk assessment
    - Client negotiations
    """
    
    # Calculate deterministic price first
    offer_data = OfferCreate(
        company_id=request.company_id,
        employees_count=request.employees_count,
        region=request.region,
        premium_48h=request.premium_48h,
        ml_feature_avg_order_value=request.ml_feature_avg_order_value,
        ml_feature_offers_count=request.ml_feature_offers_count
    )
    
    pricing_result = pricing_service.calculate_price_and_score(offer_data, db)
    
    # Get industry risk factor
    company_industry_risk = 0.5
    if request.company_id:
        company = db.query(Company).filter(Company.id == request.company_id).first()
        if company and company.industry:
            company_industry_risk = company.industry.risk_factor
    
    # Run scenario analysis
    scenarios = monte_carlo_service.scenario_analysis(
        base_price=pricing_result.final_price,
        employees_count=request.employees_count,
        region=request.region,
        premium=request.premium_48h,
        industry_risk_factor=company_industry_risk,
        ai_score=pricing_result.ai_score
    )
    
    return ScenarioAnalysisResponse(**scenarios)


@router.post("/sensitivity")
def get_sensitivity_analysis(
    request: MonteCarloRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform sensitivity analysis on pricing parameters.
    
    Shows how changes in input parameters affect price variance.
    Useful for understanding key drivers of pricing uncertainty.
    """
    
    # Calculate deterministic price first
    offer_data = OfferCreate(
        company_id=request.company_id,
        employees_count=request.employees_count,
        region=request.region,
        premium_48h=request.premium_48h,
        ml_feature_avg_order_value=request.ml_feature_avg_order_value,
        ml_feature_offers_count=request.ml_feature_offers_count
    )
    
    pricing_result = pricing_service.calculate_price_and_score(offer_data, db)
    
    # Get industry risk factor
    company_industry_risk = 0.5
    if request.company_id:
        company = db.query(Company).filter(Company.id == request.company_id).first()
        if company and company.industry:
            company_industry_risk = company.industry.risk_factor
    
    # Run sensitivity analysis
    sensitivity = monte_carlo_service.sensitivity_analysis(
        base_price=pricing_result.final_price,
        employees_count=request.employees_count,
        region=request.region,
        premium=request.premium_48h,
        industry_risk_factor=company_industry_risk,
        ai_score=pricing_result.ai_score
    )
    
    return {
        "deterministic_price": pricing_result.final_price,
        "ai_score": pricing_result.ai_score,
        **sensitivity
    }


@router.get("/info")
def monte_carlo_info():
    """
    Get information about Monte Carlo simulation methodology.
    """
    return {
        "description": "Monte Carlo simulation for price risk analysis",
        "methodology": {
            "model": "Geometric Brownian Motion inspired with multiple uncertainty sources",
            "default_simulations": 10000,
            "factors": [
                "Market volatility (15% base)",
                "Regional risk factors",
                "Industry risk multiplier",
                "AI confidence adjustment",
                "Demand uncertainty",
                "Cost uncertainty",
                "Rare stress events (5% probability)"
            ]
        },
        "outputs": {
            "percentiles": "P5, P25, P50, P75, P95 price distribution",
            "var_95": "Value at Risk at 95% confidence - maximum expected loss",
            "cvar_95": "Conditional VaR - average loss in worst 5% scenarios",
            "confidence_interval": "95% CI for mean price estimate",
            "convergence_score": "Stability metric for simulation quality"
        },
        "use_cases": [
            "Price risk assessment",
            "Budget planning with uncertainty",
            "Stress testing pricing models",
            "Client negotiation support",
            "Regulatory compliance (VaR reporting)"
        ]
    }
