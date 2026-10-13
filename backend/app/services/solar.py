"""Transparent planning model. Defaults are illustrative; verify before quoting."""
from math import ceil, isfinite

ASSUMPTIONS = {
    "version": "2026.1-illustrative",
    "annual_yield_kwh_per_kw": 1450,
    "tariff_inr_per_kwh": 8.0,
    "self_consumption": {"residential": .70, "commercial": .82, "industrial": .85},
    "export_credit_inr_per_kwh": 0.0,
    "cost_inr_per_kw": {"residential": 62000, "commercial": 52000, "industrial": 48000},
    "annual_escalation": .05,
    "degradation": .005,
    "annual_maintenance_fraction": .01,
    "emissions_kg_per_kwh": .70,
    "illustrative_bill_offset": .85,
    "illustrative_bill_offset_high": .90,
}

def calculate(category: str, monthly_bill: float, roof_area: float | None = None,
              monthly_units: float | None = None, operating_hours: float = 10,
              language: str = "en") -> dict:
    if category not in ASSUMPTIONS["self_consumption"]:
        raise ValueError("Unsupported customer category")
    if not isfinite(monthly_bill) or monthly_bill <= 0 or monthly_bill > 100_000_000:
        raise ValueError("Monthly bill must be between ₹1 and ₹10 crore")
    if roof_area is not None and (not isfinite(roof_area) or roof_area < 0 or roof_area > 10_000_000):
        raise ValueError("Roof area is outside the supported range")
    bill_units = monthly_units if monthly_units and monthly_units > 0 else monthly_bill / ASSUMPTIONS["tariff_inr_per_kwh"]
    # Longer business operating hours generally allow more on-site solar use;
    # use this only as a modest planning adjustment, capped conservatively.
    load_match = min(1.1, max(.7, operating_hours / 10))
    self_consumption_rate = min(.95, ASSUMPTIONS["self_consumption"][category] * load_match)
    bill_based_kw = bill_units * 12 / (ASSUMPTIONS["annual_yield_kwh_per_kw"] * self_consumption_rate)
    roof_kw = roof_area / 9 if roof_area and roof_area > 0 else None
    if category == "residential":
        if monthly_bill < 1000:
            recommended_kw = 2
        elif monthly_bill < 2500:
            recommended_kw = 3
        elif monthly_bill < 4000:
            recommended_kw = 5
        elif monthly_bill < 6000:
            recommended_kw = 6
        else:
            recommended_kw = 6 + ceil((monthly_bill - 6000) / 1500)
        # A supplied roof area can constrain the practical system estimate.
        proposed = min(float(recommended_kw), roof_kw) if roof_kw else float(recommended_kw)
    else:
        # Business categories use a usage-based size estimate.
        proposed = min(bill_based_kw * .85, roof_kw) if roof_kw else bill_based_kw * .85
    # Recommend one whole-kW system size, never a decimal or range.
    capacity = max(1, int(proposed + .5))
    capacity_low = capacity_high = capacity
    annual_generation = round(capacity * ASSUMPTIONS["annual_yield_kwh_per_kw"])
    self_use = min(annual_generation * self_consumption_rate, bill_units * 12)
    exported = max(0, annual_generation - self_use)
    # Keep the cashflow model conservative at the 85% low end while showing
    # the requested 85–90% illustrative savings range in the estimate.
    savings_low = round(monthly_bill * 12 * ASSUMPTIONS["illustrative_bill_offset"])
    savings_high = round(monthly_bill * 12 * ASSUMPTIONS["illustrative_bill_offset_high"])
    gross_cost = round(capacity * ASSUMPTIONS["cost_inr_per_kw"][category])
    maintenance = round(gross_cost * ASSUMPTIONS["annual_maintenance_fraction"])
    net_savings = max(0, savings_low - maintenance)
    payback = round(gross_cost / net_savings, 1) if net_savings > 0 else None
    projection = []
    cumulative = -gross_cost
    for year in range(1, 26):
        year_savings = savings_low * ((1 + ASSUMPTIONS["annual_escalation"]) ** (year - 1)) * ((1 - ASSUMPTIONS["degradation"]) ** (year - 1)) - maintenance
        cumulative += year_savings
        projection.append({"year": year, "net_savings": round(year_savings), "cumulative_net": round(cumulative)})
    subsidy_status = "not_assessed" if category == "residential" else "not_applicable_to_rooftop_estimate"
    return {
        "category": category, "capacity_kw": {"low": capacity_low, "high": capacity_high},
        "annual_generation_kwh": annual_generation, "self_consumption_kwh": round(self_use),
        "export_kwh": round(exported), "monthly_savings_inr": round(savings_low / 12),
        "monthly_savings_range_inr": {"low": round(monthly_bill * ASSUMPTIONS["illustrative_bill_offset"]), "high": round(monthly_bill * ASSUMPTIONS["illustrative_bill_offset_high"])},
        "annual_savings_inr": savings_low,
        "annual_savings_range_inr": {"low": savings_low, "high": savings_high},
        "bill_reduction_percent": round(ASSUMPTIONS["illustrative_bill_offset"] * 100),
        "bill_reduction_range_percent": {"low": round(ASSUMPTIONS["illustrative_bill_offset"] * 100), "high": round(ASSUMPTIONS["illustrative_bill_offset_high"] * 100)},
        "gross_cost_inr": gross_cost, "subsidy_inr": 0,
        "subsidy_status": subsidy_status, "net_cost_inr": gross_cost,
        "payback_years": payback, "carbon_reduction_tonnes_year": round(annual_generation * ASSUMPTIONS["emissions_kg_per_kwh"] / 1000, 1),
        "projection": projection, "assumptions": {**ASSUMPTIONS, "estimated_self_consumption_rate": round(self_consumption_rate, 3)},
        "quality": "indicative", "uncertainties": [
            "Tariff is a generic planning proxy, not a verified DISCOM tariff.",
            "Generation depends on site irradiation, orientation, shading, temperature and system losses.",
            "Export credit is set to ₹0 because applicable settlement rules are unverified.",
            "Capacity, roof structure, sanctioned load and bill savings require professional assessment.",
            "Business operating hours are only a rough indicator of on-site solar use.",
            "Bill savings are illustrated at 85–90% of the entered bill; actual savings are not guaranteed.",
            "Residential kW follows the requested bill tiers; validate the recommended size and 85–90% illustrative savings range against actual site generation and the utility tariff.",
            "Subsidy eligibility is not determined; no incentive is deducted from project cost.",
        ],
    }
