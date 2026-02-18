"""
Offer repository for offer-specific data operations.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app.repositories.base_repository import BaseRepository
from app.models.models import Offer, Company


class OfferRepository(BaseRepository[Offer]):
    """Repository for Offer model operations."""
    
    def __init__(self, db: Session):
        super().__init__(Offer, db)

    def get_by_company_id(self, company_id: int) -> List[Offer]:
        """Get all offers for a specific company."""
        return self.db.query(Offer).filter(Offer.company_id == company_id).all()

    def get_by_user_companies(self, user_id: int) -> List[Offer]:
        """Get all offers for companies owned by a user."""
        return self.db.query(Offer).join(Company).filter(
            Company.user_id == user_id
        ).all()

    def get_by_priority(self, priority_level: str) -> List[Offer]:
        """Get all offers with a specific priority level."""
        return self.db.query(Offer).filter(
            Offer.priority_level == priority_level
        ).all()

    def get_vip_offers(self) -> List[Offer]:
        """Get all VIP priority offers."""
        return self.get_by_priority("VIP")

    def get_by_region(self, region: str) -> List[Offer]:
        """Get all offers for a specific region."""
        return self.db.query(Offer).filter(Offer.region == region).all()

    def get_recent(self, limit: int = 10) -> List[Offer]:
        """Get most recently created offers."""
        return self.db.query(Offer).order_by(
            Offer.created_at.desc()
        ).limit(limit).all()

    def get_top_by_score(self, limit: int = 5) -> List[Offer]:
        """Get offers with highest AI scores."""
        return self.db.query(Offer).order_by(
            Offer.ai_score.desc()
        ).limit(limit).all()

    def get_avg_price(self) -> float:
        """Get average final price across all offers."""
        result = self.db.query(func.avg(Offer.final_price)).scalar()
        return float(result) if result else 0.0

    def get_avg_score(self) -> float:
        """Get average AI score across all offers."""
        result = self.db.query(func.avg(Offer.ai_score)).scalar()
        return float(result) if result else 0.0

    def get_avg_score_by_region(self) -> dict:
        """Get average AI score grouped by region."""
        results = self.db.query(
            Offer.region,
            func.avg(Offer.ai_score)
        ).group_by(Offer.region).all()
        return {region: float(avg) for region, avg in results}

    def get_count_by_priority(self) -> dict:
        """Count offers grouped by priority level."""
        results = self.db.query(
            Offer.priority_level,
            func.count(Offer.id)
        ).group_by(Offer.priority_level).all()
        return {priority: count for priority, count in results}

    def get_offers_in_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Offer]:
        """Get offers created within a date range."""
        return self.db.query(Offer).filter(
            Offer.created_at >= start_date,
            Offer.created_at <= end_date
        ).all()

    def get_offers_last_days(self, days: int = 30) -> List[Offer]:
        """Get offers created in the last N days."""
        start_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(Offer).filter(
            Offer.created_at >= start_date
        ).all()

    def get_total_revenue(self) -> float:
        """Get total revenue from all offers."""
        result = self.db.query(func.sum(Offer.final_price)).scalar()
        return float(result) if result else 0.0

    def get_premium_offers(self) -> List[Offer]:
        """Get all premium (48h) offers."""
        return self.db.query(Offer).filter(Offer.premium_48h == True).all()
