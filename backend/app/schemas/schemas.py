from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime

# --- Pydantic Schemas ---

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: str = "user"

class User(UserBase):
    id: int
    role: str
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class IndustryBase(BaseModel):
    name: str
    risk_factor: float

class IndustryCreate(IndustryBase):
    pass

class Industry(IndustryBase):
    id: int
    class Config:
        from_attributes = True

class CompanyBase(BaseModel):
    name: str
    industry_id: int

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class OfferBase(BaseModel):
    company_id: int
    employees_count: int
    region: str
    premium_48h: bool
    ml_feature_avg_order_value: float = 0.0 # for ml scoring (simulated)
    ml_feature_offers_count: int = 0  # for ml scoring (simulated)

class OfferCreate(OfferBase):
    pass

class PricingResponse(BaseModel):
    base_price: float
    final_price: float
    ai_score: float
    ml_score: float
    rule_score: float
    priority_level: str
    discount_applied: float

class Offer(OfferBase):
    id: int
    base_price: float
    final_price: float
    ai_score: float
    priority_level: str
    ml_score: float
    rule_score: float
    created_at: datetime
    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    companies_count: int
    offers_count: int
    avg_offer_value: float
    top_5_companies: List[str]
    industry_distribution: dict
    avg_score_per_region: dict


# --- Monte Carlo Schemas ---

class MonteCarloRequest(BaseModel):
    """Request for Monte Carlo simulation"""
    company_id: int
    employees_count: int
    region: str
    premium_48h: bool = False
    ml_feature_avg_order_value: float = 0.0
    ml_feature_offers_count: int = 0
    n_simulations: int = 10000
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_id": 1,
                "employees_count": 100,
                "region": "Mazowieckie",
                "premium_48h": True,
                "ml_feature_avg_order_value": 25000.0,
                "ml_feature_offers_count": 5,
                "n_simulations": 10000
            }
        }


class MonteCarloPercentiles(BaseModel):
    p5: float
    p25: float
    p50: float
    p75: float
    p95: float


class MonteCarloRiskMetrics(BaseModel):
    var_95: float
    cvar_95: float
    interpretation: str


class MonteCarloConfidenceInterval(BaseModel):
    lower: float
    upper: float


class MonteCarloHistogram(BaseModel):
    bins: List[float]
    counts: List[int]


class MonteCarloSimulationQuality(BaseModel):
    n_simulations: int
    convergence_score: float


class MonteCarloResponse(BaseModel):
    """Full Monte Carlo simulation results"""
    mean_price: float
    median_price: float
    std_dev: float
    percentiles: MonteCarloPercentiles
    risk_metrics: MonteCarloRiskMetrics
    confidence_interval_95: MonteCarloConfidenceInterval
    simulation_quality: MonteCarloSimulationQuality
    histogram: MonteCarloHistogram
    
    # Original pricing for reference
    deterministic_price: float
    ai_score: float
    priority_level: str


class ScenarioCase(BaseModel):
    price: float
    probability: str
    description: str


class PriceRange(BaseModel):
    min: float
    max: float
    spread: float
    spread_pct: float


class ScenarioAnalysisResponse(BaseModel):
    """Best/Worst/Expected case scenarios"""
    best_case: ScenarioCase
    expected_case: ScenarioCase
    worst_case: ScenarioCase
    price_range: PriceRange
