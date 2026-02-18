"""
User repository for user-specific data operations.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.repositories.base_repository import BaseRepository
from app.models.models import User


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""
    
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return self.db.query(User).filter(User.email == email).first()

    def get_admins(self):
        """Get all admin users."""
        return self.db.query(User).filter(User.role == "admin").all()

    def get_regular_users(self):
        """Get all regular users (non-admin)."""
        return self.db.query(User).filter(User.role == "user").all()

    def is_email_taken(self, email: str) -> bool:
        """Check if email is already registered."""
        return self.db.query(User).filter(User.email == email).count() > 0

    def update_role(self, user_id: int, role: str) -> Optional[User]:
        """Update user role."""
        return self.update(user_id, {"role": role})

    def update_password(self, user_id: int, hashed_password: str) -> Optional[User]:
        """Update user password."""
        return self.update(user_id, {"hashed_password": hashed_password})
