# backend/app/services/metrics_calculator.py

"""
Fund metrics calculator service
"""
from typing import Dict, Any, Optional
from decimal import Decimal
import numpy as np
from scipy.optimize import newton
import numpy_financial as npf
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.transaction import CapitalCall, Distribution, Adjustment


class MetricsCalculator:
    """Calculate fund performance metrics"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_all_metrics(self, fund_id: int) -> Dict[str, Any]:
        """Calculate all metrics for a fund"""
        pic = self.calculate_pic(fund_id)
        total_distributions = self.calculate_total_distributions(fund_id)
        dpi = self.calculate_dpi(fund_id)
        irr = self.calculate_irr(fund_id)

        return {
            "pic": float(pic) if pic else 0,
            "total_distributions": float(total_distributions) if total_distributions else 0,
            "dpi": float(dpi) if dpi else 0,
            "irr": float(irr) if irr else 0,
            "tvpi": None,
            "rvpi": None,
            "nav": None,
        }

    def calculate_pic(self, fund_id: int) -> Optional[Decimal]:
        """
        Calculate Paid-In Capital (PIC)
        PIC = Total Capital Calls - Adjustments
        """
        total_calls = self.db.query(
            func.sum(CapitalCall.amount)
        ).filter(
            CapitalCall.fund_id == fund_id
        ).scalar() or Decimal(0)

        total_adjustments = self.db.query(
            func.sum(Adjustment.amount)
        ).filter(
            Adjustment.fund_id == fund_id
        ).scalar() or Decimal(0)

        pic = total_calls - total_adjustments
        print(f"🔍 PIC Calculation: Total Calls = {total_calls}, Total Adjustments = {total_adjustments}, PIC = {pic}")
        return pic if pic > 0 else Decimal(0)

    def calculate_total_distributions(self, fund_id: int) -> Optional[Decimal]:
        """Calculate total distributions"""
        total = self.db.query(
            func.sum(Distribution.amount)
        ).filter(
            Distribution.fund_id == fund_id
        ).scalar() or Decimal(0)
        print(f"🔍 Total Distributions = {total}")
        return total

    def calculate_dpi(self, fund_id: int) -> Optional[float]:
        """
        Calculate DPI (Distribution to Paid-In)
        DPI = Cumulative Distributions / PIC
        """
        pic = self.calculate_pic(fund_id)
        total_distributions = self.calculate_total_distributions(fund_id)

        if not pic or pic == 0:
            print("⚠️ DPI: PIC is zero or None → returning 0.0")
            return 0.0

        dpi = float(total_distributions) / float(pic)
        dpi_rounded = round(dpi, 4)
        print(f"🔍 DPI Calculation: {float(total_distributions):,.2f} / {float(pic):,.2f} = {dpi_rounded:.4f}")
        return dpi_rounded

    def calculate_irr(self, fund_id: int) -> Optional[float]:
        """
        Calculate IRR (Internal Rate of Return) using XIRR (exact dates).
        Uses only capital calls (negative) and distributions (positive).
        Adjustments are excluded per CALCULATIONS.md.
        """
        try:
            cash_flows = []
            dates = []

            # Capital calls (negative / money out)
            calls = self.db.query(
                CapitalCall.call_date,
                CapitalCall.amount
            ).filter(
                CapitalCall.fund_id == fund_id
            ).order_by(CapitalCall.call_date).all()

            for call in calls:
                dates.append(call.call_date)
                cash_flows.append(-float(call.amount))

            # Distributions (positive / money in)
            distributions = self.db.query(
                Distribution.distribution_date,
                Distribution.amount
            ).filter(
                Distribution.fund_id == fund_id
            ).order_by(Distribution.distribution_date).all()

            for dist in distributions:
                dates.append(dist.distribution_date)
                cash_flows.append(float(dist.amount))

            print("\n=== CASH FLOW DEBUG (CALCULATE_IRR - XIRR) ===")
            for date, amount in zip(dates, cash_flows):
                print(f"{date} | {amount}")
            print("==============================================\n")

            if len(cash_flows) < 2:
                print("⚠️ IRR: Less than 2 cash flows → returning None")
                return None

            # Konversi tanggal ke jumlah hari sejak tanggal pertama
            from datetime import date
            first_date = min(dates)
            days_from_start = [(d - first_date).days for d in dates]

            # Fungsi NPV untuk XIRR
            def npv(rate):
                total = 0.0
                for cf, days in zip(cash_flows, days_from_start):
                    if rate <= -1:
                        # Jika rate <= -100%, maka (1 + rate) <= 0, tidak valid
                        return float('inf') if cf > 0 else float('-inf')
                    try:
                        total += cf / ((1 + rate) ** (days / 365.0))
                    except (ZeroDivisionError, OverflowError, ValueError):
                        # Jika terjadi error numerik, kembalikan infinity
                        return float('inf') if cf > 0 else float('-inf')
                return total

            # Cari akar dari fungsi NPV (yaitu, NPV = 0)
            # Gunakan beberapa tebakan awal
            guesses = [0.1, 0.0, -0.1, 0.2, -0.2, 0.5, -0.5]
            for guess in guesses:
                try:
                    irr = newton(npv, guess, maxiter=100, tol=1e-6)
                    # Pastikan hasilnya masuk akal
                    if np.isfinite(irr):
                        print(f"🧮 Raw XIRR (decimal) from guess {guess}: {irr}")
                        break
                except (RuntimeError, ValueError):
                    continue
            else:
                # Jika semua tebakan gagal
                print("❌ XIRR calculation failed to converge after multiple guesses.")
                return None

            if np.isnan(irr) or np.isinf(irr):
                print("❌ XIRR calculation returned NaN or Inf.")
                return None

            irr_pct = round(float(irr) * 100, 2)
            print(f"✅ Final XIRR: {irr_pct}%")
            return irr_pct

        except Exception as e:
            print(f"💥 Error calculating XIRR: {e}")
            return None

    def get_calculation_breakdown(self, fund_id: int, metric: str) -> Dict[str, Any]:
        """
        Get detailed breakdown of a calculation with cash flows for debugging
        """
        if metric == "dpi":
            pic = self.calculate_pic(fund_id)
            total_distributions = self.calculate_total_distributions(fund_id)
            dpi = self.calculate_dpi(fund_id)

            capital_calls = self.db.query(CapitalCall).filter(
                CapitalCall.fund_id == fund_id
            ).order_by(CapitalCall.call_date).all()

            distributions = self.db.query(Distribution).filter(
                Distribution.fund_id == fund_id
            ).order_by(Distribution.distribution_date).all()

            adjustments = self.db.query(Adjustment).filter(
                Adjustment.fund_id == fund_id
            ).order_by(Adjustment.adjustment_date).all()

            return {
                "metric": "DPI",
                "formula": "Cumulative Distributions / Paid-In Capital",
                "pic": float(pic) if pic else 0.0,
                "total_distributions": float(total_distributions) if total_distributions else 0.0,
                "result": dpi,
                "explanation": f"DPI = {float(total_distributions):,.2f} / {float(pic):,.2f} = {dpi:.4f}",
                "transactions": {
                    "capital_calls": [
                        {
                            "date": str(call.call_date),
                            "amount": float(call.amount),
                            "description": call.description or ""
                        } for call in capital_calls
                    ],
                    "distributions": [
                        {
                            "date": str(dist.distribution_date),
                            "amount": float(dist.amount),
                            "is_recallable": dist.is_recallable,
                            "description": dist.description or ""
                        } for dist in distributions
                    ],
                    "adjustments": [
                        {
                            "date": str(adj.adjustment_date),
                            "amount": float(adj.amount),
                            "type": adj.adjustment_type or "",
                            "description": adj.description or ""
                        } for adj in adjustments
                    ]
                }
            }

        elif metric == "irr":
            cash_flows = []
            calls = self.db.query(
                CapitalCall.call_date,
                CapitalCall.amount
            ).filter(
                CapitalCall.fund_id == fund_id
            ).order_by(CapitalCall.call_date).all()

            for call in calls:
                cash_flows.append({
                    'date': call.call_date,
                    'amount': -float(call.amount),
                    'type': 'capital_call'
                })

            distributions = self.db.query(
                Distribution.distribution_date,
                Distribution.amount
            ).filter(
                Distribution.fund_id == fund_id
            ).order_by(Distribution.distribution_date).all()

            for dist in distributions:
                cash_flows.append({
                    'date': dist.distribution_date,
                    'amount': float(dist.amount),
                    'type': 'distribution'
                })

            cash_flows.sort(key=lambda x: x['date'])
            irr = self.calculate_irr(fund_id)

            return {
                "metric": "IRR",
                "formula": "Internal Rate of Return (NPV = 0)",
                "cash_flows": [
                    {
                        "date": str(cf["date"]),
                        "amount": cf["amount"],
                        "type": cf["type"]
                    } for cf in cash_flows
                ],
                "result": irr,
                "explanation": f"IRR calculated from {len(cash_flows)} cash flows = {irr:.2f}%" if irr is not None else "IRR could not be calculated",
                "cash_flow_summary": {
                    "total_outflows": sum(cf['amount'] for cf in cash_flows if cf['amount'] < 0),
                    "total_inflows": sum(cf['amount'] for cf in cash_flows if cf['amount'] > 0),
                    "net_cash_flow": sum(cf['amount'] for cf in cash_flows)
                }
            }

        elif metric == "pic":
            capital_calls = self.db.query(CapitalCall).filter(
                CapitalCall.fund_id == fund_id
            ).order_by(CapitalCall.call_date).all()

            adjustments = self.db.query(Adjustment).filter(
                Adjustment.fund_id == fund_id
            ).order_by(Adjustment.adjustment_date).all()

            total_calls = sum(float(call.amount) for call in capital_calls)
            total_adjustments = sum(float(adj.amount) for adj in adjustments)
            pic = self.calculate_pic(fund_id)

            return {
                "metric": "PIC",
                "formula": "Total Capital Calls - Adjustments",
                "total_calls": total_calls,
                "total_adjustments": total_adjustments,
                "result": float(pic) if pic else 0.0,
                "explanation": f"PIC = {total_calls:,.2f} - ({total_adjustments:,.2f}) = {float(pic):,.2f}",
                "transactions": {
                    "capital_calls": [
                        {
                            "date": str(call.call_date),
                            "amount": float(call.amount),
                            "description": call.description or ""
                        } for call in capital_calls
                    ],
                    "adjustments": [
                        {
                            "date": str(adj.adjustment_date),
                            "amount": float(adj.amount),
                            "type": adj.adjustment_type or "",
                            "description": adj.description or ""
                        } for adj in adjustments
                    ]
                }
            }

        return {"error": "Unknown metric", "supported_metrics": ["pic", "dpi", "irr"]}