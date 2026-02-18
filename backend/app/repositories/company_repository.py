"""
Company repository for company-specific data operations.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.repositories.base_repository import BaseRepository
from app.models.models import Company, Industry


class CompanyRepository(BaseRepository[Company]):
    """Repository for Company model operations."""
    
    def __init__(self, db: Session):
        super().__init__(Company, db)

    def get_by_user_id(self, user_id: int) -> List[Company]:
        """Get all companies belonging to a user."""
        return self.db.query(Company).filter(Company.user_id == user_id).all()

    def get_by_industry_id(self, industry_id: int) -> List[Company]:
        """Get all companies in a specific industry."""
        return self.db.query(Company).filter(Company.industry_id == industry_id).all()

    def get_by_name(self, name: str) -> Optional[Company]:
        """Get company by name."""
        return self.db.query(Company).filter(Company.name == name).first()

    def search_by_name(self, name_query: str) -> List[Company]:
        """Search companies by partial name match."""
        return self.db.query(Company).filter(
            Company.name.ilike(f"%{name_query}%")
        ).all()

    def get_with_industry(self, company_id: int) -> Optional[Company]:
        """Get company with eagerly loaded industry."""
        return self.db.query(Company).filter(
            Company.id == company_id
        ).first()

    def count_by_industry(self) -> dict:
        """Count companies grouped by industry."""
        results = self.db.query(
            Industry.name,
            func.count(Company.id)
        ).join(Company).group_by(Industry.name).all()
        return {name: count for name, count in results}

    def get_recent(self, limit: int = 10) -> List[Company]:
        """Get most recently created companies."""
        return self.db.query(Company).order_by(
            Company.created_at.desc()
        ).limit(limit).all()
