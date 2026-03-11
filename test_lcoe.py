#!/usr/bin/env python3
"""Quick test of enhanced calc_solar with LCOE and financing."""
import sys
sys.path.insert(0, 'api')
from services import calc_solar

result = calc_solar(10000, 'Georgia', 0.65, 200, 0.12,
                    include_itc=True, rate_escalation=0.02, financing='cash')

print('=== KEY RESULTS ===')
print(f'Capacity: {result["capacity_kw"]} kW')
print(f'Annual MWh: {result["annual_mwh"]}')
print(f'Net Cost: ${result["install_cost"]:,.0f}')
print(f'Payback: {result["payback_years"]} years')
print(f'25-Year NPV: ${result["npv_25yr"]:,.0f}')
print()
print('=== NEW LCOE METRICS ===')
print(f'Solar LCOE: ${result["lcoe_solar"]:.4f}/kWh')
print(f'Grid LCOE:  ${result["lcoe_grid"]:.4f}/kWh')
print(f'Solar vs Grid: {result["lcoe_savings_pct"]}% cheaper')
print(f'Lifetime Savings: ${result["lifetime_savings"]:,.0f}')
print(f'MACRS Benefit: ${result["macrs_benefit"]:,.0f}')
print(f'Inverter: ${result["inverter_replacement_cost"]:,.0f} at yr {result["inverter_replacement_year"]}')
print()
print('=== YEAR-BY-YEAR (first 3 + last 2) ===')
for yd in result['yearly_cashflow'][:3]:
    print(f'  Yr {yd["year"]}: grid=${yd["grid_cost"]:,.0f} solar=${yd["solar_cost"]:,.0f} savings=${yd["savings"]:,.0f} cum=${yd["cumulative_savings"]:,.0f}')
print('  ...')
for yd in result['yearly_cashflow'][-2:]:
    print(f'  Yr {yd["year"]}: grid=${yd["grid_cost"]:,.0f} solar=${yd["solar_cost"]:,.0f} savings=${yd["savings"]:,.0f} cum=${yd["cumulative_savings"]:,.0f}')
print()

result2 = calc_solar(10000, 'Georgia', 0.65, 200, 0.12, financing='loan')
print(f'=== LOAN ===')
print(f'Monthly: ${result2["monthly_payment"]:,.2f}, Payback yr {result2["payback_years"]}')
print(f'Total loan cost: ${result2["total_loan_cost"]:,.0f}')
