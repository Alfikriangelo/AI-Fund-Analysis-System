"""
Transaction database models (Capital Calls, Distributions, Adjustments)
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class CapitalCall(Base):
    """Capital Call model"""
    
    __tablename__ = "capital_calls"
    
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(Integer, ForeignKey("funds.id"), nullable=False)
    call_date = Column(Date, nullable=False)
    call_type = Column(String(100))
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    fund = relationship("Fund", back_populates="capital_calls")


class Distribution(Base):
    """Distribution model"""
    
    __tablename__ = "distributions"
    
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(Integer, ForeignKey("funds.id"), nullable=False)
    distribution_date = Column(Date, nullable=False)
    distribution_type = Column(String(100))
    is_recallable = Column(Boolean, default=False)
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    fund = relationship("Fund", back_populates="distributions")


class Adjustment(Base):
    """Adjustment model"""
    
    __tablename__ = "adjustments"
    
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(Integer, ForeignKey("funds.id"), nullable=False)
    adjustment_date = Column(Date, nullable=False)
    adjustment_type = Column(String(100))
    category = Column(String(100))
    amount = Column(Numeric(15, 2), nullable=False)
    is_contribution_adjustment = Column(Boolean, default=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    fund = relationship("Fund", back_populates="adjustments")
