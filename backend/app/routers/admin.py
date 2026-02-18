from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import Offer, Company, User, Industry
from app.schemas.schemas import DashboardStats, Industry
from app.routers.auth import get_current_user

router = APIRouter()

@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    companies_count = db.query(Company).count()
    offers_count = db.query(Offer).count()
    avg_value = db.query(func.avg(Offer.final_price)).scalar() or 0.0
    
    # Top 5 by AI Score
    top_5 = db.query(Offer).order_by(Offer.ai_score.desc()).limit(5).all()
    top_5_names = [f"{o.company.name} ({o.ai_score})" for o in top_5 if o.company]
    
    # Industry Distribution
    industries = db.query(Industry.name, func.count(Company.id))\
        .join(Company)\
        .group_by(Industry.name).all()
    industry_dist = {i[0]: i[1] for i in industries}
    
    # Region Scores
    region_scores = db.query(Offer.region, func.avg(Offer.ai_score))\
        .group_by(Offer.region).all()
    region_avg = {r[0]: float(r[1]) for r in region_scores}
    
    return DashboardStats(
        companies_count=companies_count,
        offers_count=offers_count,
        avg_offer_value=float(avg_value),
        top_5_companies=top_5_names,
        industry_distribution=industry_dist,
        avg_score_per_region=region_avg
    )

@router.post("/recalc_scores")
def recalc_scores():
    # Placeholder for batch recalculation if needed
    return {"message": "Recalculation started"}
