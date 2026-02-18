"""
Repository package - implements Repository Pattern for data access.
"""
from app.repositories.base_repository import BaseRepository
from app.repositories.user_repository import UserRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.offer_repository import OfferRepository
from app.repositories.industry_repository import IndustryRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "CompanyRepository",
    "OfferRepository",
    "IndustryRepository",
]
