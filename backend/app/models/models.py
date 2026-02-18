from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user") # "admin" or "user"
    
    companies = relationship("Company", back_populates="user")

class Industry(Base):
    __tablename__ = "industries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    risk_factor = Column(Float, default=0.5)
    
    companies = relationship("Company", back_populates="industry")

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    industry_id = Column(Integer, ForeignKey("industries.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="companies")
    industry = relationship("Industry", back_populates="companies")
    offers = relationship("Offer", back_populates="company")

class Offer(Base):
    __tablename__ = "offers"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    employees_count = Column(Integer)
    region = Column(String) # Mazowieckie, Slaskie, Malopolskie, Inne
    premium_48h = Column(Boolean, default=False)
    base_price = Column(Float)
    final_price = Column(Float)
    ai_score = Column(Float)
    priority_level = Column(String) # LOW, STANDARD, VIP
    ml_score = Column(Float)
    rule_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    company = relationship("Company", back_populates="offers")
