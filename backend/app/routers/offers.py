from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Offer, Company, User
from app.schemas.schemas import OfferCreate, Offer as OfferSchema, PricingResponse
from app.services.pricing_service import pricing_service
from app.routers.auth import get_current_user
from typing import List

router = APIRouter()

@router.post("/", response_model=OfferSchema)
def create_offer(offer_data: OfferCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verify company exists if provided
    company = db.query(Company).filter(Company.id == offer_data.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    # Calculate Price & Score
    pricing = pricing_service.calculate_price_and_score(offer_data, db)
    
    # Create Offer
    new_offer = Offer(
        company_id=offer_data.company_id,
        employees_count=offer_data.employees_count,
        region=offer_data.region,
        premium_48h=offer_data.premium_48h,
        base_price=pricing.base_price,
        final_price=pricing.final_price,
        ai_score=pricing.ai_score,
        priority_level=pricing.priority_level,
        ml_score=pricing.ml_score,
        rule_score=pricing.rule_score
    )
    
    db.add(new_offer)
    db.commit()
    db.refresh(new_offer)
    return new_offer

@router.get("/", response_model=List[OfferSchema])
def list_offers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "admin":
        return db.query(Offer).all()
    else:
        # User sees only their companies' offers.
        # But User model is basic: id, email.
        # How is User linked to Company? 
        # Prompt: "User: widzi tylko swoje firmy".
        # Missing link: User <-> Company.
        # I'll assume for MVP that User is linked to Companies? Or Companies have user_id?
        # Re-reading prompt: "Company: id, name, industry_id". "User: ...".
        # No Foreign Key in prompt. I should add `user_id` to `Company`.
        # I will modify the Company model in models.py and add user_id.
        return [] # Placeholder until I fix model
