"""
Metrics API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.db.session import get_db
from app.models.fund import Fund
from app.services.metrics_calculator import MetricsCalculator

router = APIRouter()


@router.get("/funds/{fund_id}/metrics")
async def get_fund_metrics(
    fund_id: int,
    metric: str = Query(None, regex="^(dpi|irr|tvpi|rvpi|pic|all)$"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get fund metrics with optional breakdown
    
    Args:
        fund_id: Fund ID
        metric: Specific metric to calculate (dpi, irr, pic, or all)
    """
    # Verify fund exists
    fund = db.query(Fund).filter(Fund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    
    calculator = MetricsCalculator(db)
    
    if not metric or metric == "all":
        # Return all metrics
        metrics = calculator.calculate_all_metrics(fund_id)
        return {
            "fund_id": fund_id,
            "fund_name": fund.name,
            "metrics": metrics
        }
    else:
        # Return specific metric with breakdown
        if metric == "dpi":
            value = calculator.calculate_dpi(fund_id)
            breakdown = calculator.get_calculation_breakdown(fund_id, "dpi")
        elif metric == "irr":
            value = calculator.calculate_irr(fund_id)
            breakdown = calculator.get_calculation_breakdown(fund_id, "irr")
        elif metric == "pic":
            value = calculator.calculate_pic(fund_id)
            breakdown = calculator.get_calculation_breakdown(fund_id, "pic")
        else:
            raise HTTPException(status_code=400, detail="Unsupported metric")
        
        return {
            "fund_id": fund_id,
            "fund_name": fund.name,
            "metric_name": metric.upper(),
            "value": float(value) if value else 0,
            "breakdown": breakdown
        }
