"""
Base repository with common CRUD operations.
Implements Repository Pattern for clean separation of data access logic.
"""
from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository providing common CRUD operations.
    
    Implements the Repository Pattern to abstract database operations
    and provide a clean interface for data access.
    """
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get a single record by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all records with pagination."""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def get_multi_by_ids(self, ids: List[int]) -> List[ModelType]:
        """Get multiple records by list of IDs."""
        return self.db.query(self.model).filter(self.model.id.in_(ids)).all()

    def create(self, obj_in: dict) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, id: int, obj_in: dict) -> Optional[ModelType]:
        """Update an existing record."""
        db_obj = self.get_by_id(id)
        if db_obj:
            for field, value in obj_in.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> bool:
        """Delete a record by ID."""
        db_obj = self.get_by_id(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False

    def exists(self, id: int) -> bool:
        """Check if a record exists."""
        return self.db.query(self.model).filter(self.model.id == id).count() > 0

    def count(self) -> int:
        """Count all records."""
        return self.db.query(self.model).count()

    def filter_by(self, **kwargs) -> List[ModelType]:
        """Filter records by given criteria."""
        filters = [getattr(self.model, k) == v for k, v in kwargs.items() if hasattr(self.model, k)]
        return self.db.query(self.model).filter(and_(*filters)).all()

    def first_by(self, **kwargs) -> Optional[ModelType]:
        """Get first record matching criteria."""
        filters = [getattr(self.model, k) == v for k, v in kwargs.items() if hasattr(self.model, k)]
        return self.db.query(self.model).filter(and_(*filters)).first()
