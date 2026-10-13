# Calculation methodology

The backend `app/services/solar.py` is the source of truth. Every stored calculation includes the input snapshot, output, and assumptions version.

- A planning tariff proxy of ₹8/kWh estimates units only when the user does not provide consumption. It is not a verified tariff for any DISCOM.
- Annual generation uses a generic 1,450 kWh per installed kW per year and should not be interpreted as a location or site forecast.
- Customer-type self-consumption factors are scenario assumptions. Export credit is ₹0 until a verified local settlement rule is configured.
- Indicative cost is a category-level planning amount per kW. Quote only after current equipment pricing and site inspection.
- Projected cash flow uses 5% annual tariff escalation, 0.5% degradation and 1% annual maintenance on initial cost; financing, taxes, demand charges, fixed charges, replacement costs and discounting are not modeled.
- The emissions illustration uses 0.70 kg CO₂e/kWh. Verify the factor and reporting boundary before public sustainability reporting.
- Subsidy is never deducted. Residential eligibility is marked for verification; commercial and industrial calculations do not receive residential assistance.

This model is suitable for initial lead qualification only. It is not an engineering design, bill guarantee, quotation, or financial advice.
