"""
Fund Pydantic schemas
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FundBase(BaseModel):
    """Base fund schema"""
    name: str
    gp_name: Optional[str] = None
    fund_type: Optional[str] = None
    vintage_year: Optional[int] = None


class FundCreate(FundBase):
    """Fund creation schema"""
    pass


class FundUpdate(BaseModel):
    """Fund update schema"""
    name: Optional[str] = None
    gp_name: Optional[str] = None
    fund_type: Optional[str] = None
    vintage_year: Optional[int] = None


class FundMetrics(BaseModel):
    """Fund metrics schema"""
    dpi: Optional[float] = None
    irr: Optional[float] = None
    tvpi: Optional[float] = None
    rvpi: Optional[float] = None
    pic: Optional[float] = None
    total_distributions: Optional[float] = None
    nav: Optional[float] = None


class Fund(FundBase):
    """Fund response schema"""
    id: int
    created_at: datetime
    metrics: Optional[FundMetrics] = None
    
    class Config:
        from_attributes = True
