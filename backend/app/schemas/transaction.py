"""
Transaction Pydantic schemas
"""
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from decimal import Decimal


class CapitalCallBase(BaseModel):
    """Base capital call schema"""
    fund_id: int
    call_date: date
    call_type: Optional[str] = None
    amount: Decimal
    description: Optional[str] = None


class CapitalCallCreate(CapitalCallBase):
    """Capital call creation schema"""
    pass


class CapitalCall(CapitalCallBase):
    """Capital call response schema"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class DistributionBase(BaseModel):
    """Base distribution schema"""
    fund_id: int
    distribution_date: date
    distribution_type: Optional[str] = None
    is_recallable: bool = False
    amount: Decimal
    description: Optional[str] = None


class DistributionCreate(DistributionBase):
    """Distribution creation schema"""
    pass


class Distribution(DistributionBase):
    """Distribution response schema"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class AdjustmentBase(BaseModel):
    """Base adjustment schema"""
    fund_id: int
    adjustment_date: date
    adjustment_type: Optional[str] = None
    category: Optional[str] = None
    amount: Decimal
    is_contribution_adjustment: bool = False
    description: Optional[str] = None


class AdjustmentCreate(AdjustmentBase):
    """Adjustment creation schema"""
    pass


class Adjustment(AdjustmentBase):
    """Adjustment response schema"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class TransactionList(BaseModel):
    """Transaction list response"""
    items: list
    total: int
    page: int
    pages: int
