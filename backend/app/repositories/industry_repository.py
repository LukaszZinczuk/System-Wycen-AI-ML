"""
Industry repository for industry-specific data operations.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.repositories.base_repository import BaseRepository
from app.models.models import Industry


class IndustryRepository(BaseRepository[Industry]):
    """Repository for Industry model operations."""
    
    def __init__(self, db: Session):
        super().__init__(Industry, db)

    def get_by_name(self, name: str) -> Optional[Industry]:
        """Get industry by name."""
        return self.db.query(Industry).filter(Industry.name == name).first()

    def get_high_risk(self, threshold: float = 0.6) -> List[Industry]:
        """Get industries with risk factor above threshold."""
        return self.db.query(Industry).filter(
            Industry.risk_factor >= threshold
        ).all()

    def get_low_risk(self, threshold: float = 0.3) -> List[Industry]:
        """Get industries with risk factor below threshold."""
        return self.db.query(Industry).filter(
            Industry.risk_factor <= threshold
        ).all()

    def get_ordered_by_risk(self, ascending: bool = True) -> List[Industry]:
        """Get all industries ordered by risk factor."""
        if ascending:
            return self.db.query(Industry).order_by(Industry.risk_factor.asc()).all()
        return self.db.query(Industry).order_by(Industry.risk_factor.desc()).all()

    def update_risk_factor(self, industry_id: int, risk_factor: float) -> Optional[Industry]:
        """Update industry risk factor."""
        return self.update(industry_id, {"risk_factor": risk_factor})
