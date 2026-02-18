from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import Company, User, Industry
from app.schemas.schemas import CompanyCreate, Company as CompanySchema
from app.routers.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=CompanySchema)
def create_company(company: CompanyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verify industry
    industry = db.query(Industry).filter(Industry.id == company.industry_id).first()
    if not industry:
        raise HTTPException(status_code=404, detail="Industry not found")
        
    new_company = Company(
        name=company.name,
        industry_id=company.industry_id,
        user_id=current_user.id
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return new_company

@router.get("/", response_model=List[CompanySchema])
def list_companies(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "admin":
        return db.query(Company).all()
    return db.query(Company).filter(Company.user_id == current_user.id).all()
