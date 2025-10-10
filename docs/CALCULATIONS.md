# Fund Metrics Calculations

This document explains the formulas and implementation details for calculating fund performance metrics.

## Overview

The system calculates key private equity fund performance metrics based on transaction data extracted from fund reports. All calculations follow ILPA (Institutional Limited Partners Association) reporting guidelines.

---

## 1. Paid-In Capital (PIC)

### Definition
Paid-In Capital represents the total amount of capital that LPs have actually contributed to the fund, adjusted for any rebalancing.

### Formula
```
PIC = Total Capital Calls - Adjustments
```

### Implementation
```python
def calculate_pic(fund_id: int) -> Decimal:
    # Get total capital calls
    total_calls = db.query(
        func.sum(CapitalCall.amount)
    ).filter(
        CapitalCall.fund_id == fund_id
    ).scalar() or Decimal(0)
    
    # Get total adjustments
    total_adjustments = db.query(
        func.sum(Adjustment.amount)
    ).filter(
        Adjustment.fund_id == fund_id
    ).scalar() or Decimal(0)
    
    pic = total_calls - total_adjustments
    return pic if pic > 0 else Decimal(0)
```

### Example
```
Capital Calls:
- 2024-04-30: $384,710 (Investment)
- 2024-04-30: $37,348 (Management Fee)
- 2024-05-31: $500,000 (Investment)
Total Capital Calls = $922,058

Adjustments:
- 2024-06-15: -$50,000 (Rebalance of Capital Call)
Total Adjustments = -$50,000

PIC = $922,058 - (-$50,000) = $972,058
```

---

## 2. DPI (Distribution to Paid-In)

### Definition
DPI measures how much capital has been returned to LPs relative to the amount they paid in. A DPI of 1.0x means LPs have received back 100% of their invested capital.

### Formula
```
DPI = Cumulative Distributions / Paid-In Capital
```

### Implementation
```python
def calculate_dpi(fund_id: int) -> float:
    pic = calculate_pic(fund_id)
    
    total_distributions = db.query(
        func.sum(Distribution.amount)
    ).filter(
        Distribution.fund_id == fund_id
    ).scalar() or Decimal(0)
    
    if not pic or pic == 0:
        return 0.0
    
    dpi = float(total_distributions) / float(pic)
    return round(dpi, 4)
```

### Interpretation
- **DPI < 1.0x**: LPs have not yet received back all invested capital
- **DPI = 1.0x**: LPs have received back exactly their invested capital
- **DPI > 1.0x**: LPs have received more than their invested capital (profit)

### Example
```
PIC = $972,058
Total Distributions = $700,000

DPI = $700,000 / $972,058 = 0.7201x

Interpretation: LPs have received back 72% of their invested capital.
```

---

## 3. IRR (Internal Rate of Return)

### Definition
IRR is the annualized rate of return that makes the net present value (NPV) of all cash flows equal to zero. It accounts for the timing of cash flows.

### Formula
```
NPV = Σ (Cash Flow_t / (1 + IRR)^t) = 0

Where:
- Cash Flow_t = cash flow at time t
- t = time period
- IRR = internal rate of return (what we solve for)
```

### Implementation
```python
import numpy_financial as npf

def calculate_irr(fund_id: int) -> float:
    # Get all cash flows sorted by date
    cash_flows = []
    
    # Capital calls (negative - money out)
    calls = db.query(
        CapitalCall.call_date,
        CapitalCall.amount
    ).filter(
        CapitalCall.fund_id == fund_id
    ).order_by(
        CapitalCall.call_date
    ).all()
    
    for call in calls:
        cash_flows.append({
            'date': call.call_date,
            'amount': -float(call.amount),  # Negative for outflow
            'type': 'capital_call'
        })
    
    # Distributions (positive - money in)
    distributions = db.query(
        Distribution.distribution_date,
        Distribution.amount
    ).filter(
        Distribution.fund_id == fund_id
    ).order_by(
        Distribution.distribution_date
    ).all()
    
    for dist in distributions:
        cash_flows.append({
            'date': dist.distribution_date,
            'amount': float(dist.amount),  # Positive for inflow
            'type': 'distribution'
        })
    
    # Sort by date
    cash_flows.sort(key=lambda x: x['date'])
    
    # Extract amounts
    amounts = [cf['amount'] for cf in cash_flows]
    
    # Calculate IRR (returns decimal, e.g., 0.15 for 15%)
    irr = npf.irr(amounts)
    
    if irr is None or np.isnan(irr) or np.isinf(irr):
        return None
    
    # Convert to percentage
    return round(float(irr) * 100, 2)
```

### Interpretation
- **IRR > 0%**: Fund is generating positive returns
- **IRR = 0%**: Fund is breaking even
- **IRR < 0%**: Fund is generating negative returns

### Example
```
Cash Flows:
- 2020-01-01: -$1,000,000 (Capital Call)
- 2021-01-01: -$500,000 (Capital Call)
- 2022-01-01: $300,000 (Distribution)
- 2023-01-01: $400,000 (Distribution)
- 2024-01-01: $1,200,000 (Distribution)

IRR = 15.24%

Interpretation: The fund is generating an annualized return of 15.24%.
```

---

## 4. TVPI (Total Value to Paid-In)

### Definition
TVPI measures the total value created by the fund relative to the capital paid in. It includes both distributions and remaining NAV.

### Formula
```
TVPI = (Cumulative Distributions + NAV) / Paid-In Capital
```

### Implementation
```python
def calculate_tvpi(fund_id: int) -> float:
    pic = calculate_pic(fund_id)
    
    total_distributions = db.query(
        func.sum(Distribution.amount)
    ).filter(
        Distribution.fund_id == fund_id
    ).scalar() or Decimal(0)
    
    # NAV would need to be tracked separately
    nav = get_fund_nav(fund_id)  # To be implemented
    
    if not pic or pic == 0:
        return 0.0
    
    tvpi = float(total_distributions + nav) / float(pic)
    return round(tvpi, 4)
```

### Interpretation
- **TVPI < 1.0x**: Fund has lost value
- **TVPI = 1.0x**: Fund has preserved capital
- **TVPI > 1.0x**: Fund has created value

---

## 5. RVPI (Residual Value to Paid-In)

### Definition
RVPI measures the remaining value in the fund relative to capital paid in.

### Formula
```
RVPI = NAV / Paid-In Capital
```

### Implementation
```python
def calculate_rvpi(fund_id: int) -> float:
    pic = calculate_pic(fund_id)
    nav = get_fund_nav(fund_id)
    
    if not pic or pic == 0:
        return 0.0
    
    rvpi = float(nav) / float(pic)
    return round(rvpi, 4)
```

---

## Adjustments and Special Cases

### 1. Rebalance of Distribution
**Nature**: Clawback of over-distributed amounts

**Treatment**:
- Recorded as negative contribution
- Reduces total distributions
- Increases PIC (denominator)
- **Effect on DPI**: Decreases DPI

**Example**:
```
Original Distribution: $100,000
Rebalance (clawback): -$10,000
Net Distribution: $90,000
```

### 2. Rebalance of Capital Call
**Nature**: Refund of over-called capital

**Treatment**:
- Recorded as positive distribution
- Reduces PIC (denominator)
- May require special flag to prevent DPI inflation

**Example**:
```
Original Capital Call: $1,000,000
Rebalance (refund): -$50,000
Net Capital Called: $950,000
```

### 3. Recallable Distributions
**Definition**: Distributions that can be called back by the GP

**Treatment**:
- Tracked with `is_recallable` flag
- Included in distribution totals
- May need separate reporting

---

## Calculation Breakdown API

The system provides detailed calculation breakdowns for transparency:

```python
def get_calculation_breakdown(fund_id: int, metric: str) -> Dict:
    if metric == "dpi":
        pic = calculate_pic(fund_id)
        total_distributions = calculate_total_distributions(fund_id)
        dpi = calculate_dpi(fund_id)
        
        return {
            "metric": "DPI",
            "formula": "Cumulative Distributions / Paid-In Capital",
            "pic": float(pic),
            "total_distributions": float(total_distributions),
            "result": dpi,
            "explanation": f"DPI = {total_distributions} / {pic} = {dpi}"
        }
```

---

## Data Validation

### Pre-calculation Checks
1. **PIC > 0**: Cannot calculate metrics without capital calls
2. **Date Ordering**: Cash flows must be chronologically ordered for IRR
3. **Amount Validation**: All amounts must be numeric and non-null
4. **Type Validation**: Transaction types must be valid

### Error Handling
```python
try:
    irr = calculate_irr(fund_id)
except Exception as e:
    logger.error(f"IRR calculation failed for fund {fund_id}: {e}")
    return None
```

---

## Performance Optimization

### Caching
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def calculate_metrics_cached(fund_id: int, cache_key: str):
    return calculate_all_metrics(fund_id)
```

### Batch Calculation
```python
def calculate_metrics_batch(fund_ids: List[int]) -> Dict[int, Dict]:
    results = {}
    for fund_id in fund_ids:
        results[fund_id] = calculate_all_metrics(fund_id)
    return results
```

---

## Testing

### Unit Tests
```python
def test_dpi_calculation():
    # Setup test data
    fund = create_test_fund()
    create_capital_call(fund.id, amount=1000000)
    create_distribution(fund.id, amount=700000)
    
    # Calculate
    dpi = calculate_dpi(fund.id)
    
    # Assert
    assert dpi == 0.7
```

### Edge Cases
1. **Zero PIC**: Should return 0 or None
2. **Negative Cash Flows Only**: IRR should handle gracefully
3. **Single Cash Flow**: IRR undefined
4. **Very Large Numbers**: Test precision
5. **Date Gaps**: Ensure proper time weighting

---

## References

- [ILPA Reporting Guidelines](https://ilpa.org/)
- [Private Equity Metrics](https://www.investopedia.com/terms/d/dpi.asp)
- [IRR Calculation](https://en.wikipedia.org/wiki/Internal_rate_of_return)
- [numpy-financial Documentation](https://numpy.org/numpy-financial/)
