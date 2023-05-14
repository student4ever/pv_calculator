import pandas as pd
import numpy_financial as npf
import streamlit as st


def calculate_solar_pv_economics(system_cost, pv_power, annual_electricity_production, electricity_rate, feed_in_tarif,
                                interest_rate, depreciation_rate, self_consumption_rate, lifetime,
                                tax_power_threshold=25, tax_feedin_threshold=12500, tax_rate=0.42):
    """
    Calculate the economics of a solar PV system for a residential customer.

    Args:
        system_cost (float): Cost of the solar PV system in dollars.
        pv_power (float):
        annual_electricity_production (float): Annual electricity production in kWh.
        electricity_rate (float): Electricity rate in EUR/kWh.
        feed_in_tarif (float): Electricity rate feedin EUR/kWh.
        interest_rate (float): Annual interest rate as a decimal (e.g., 0.05 for 5%).
        depreciation_rate (float): Annual depreciation rate as a decimal (e.g., 0.10 for 10%).
        self_consumption_rate (float): Self-consumption rate as a decimal (e.g., 0.80 for 80%).
        payback_period (int): payback period in years (e.g. 20 years)
        tax_power_threshold:
        tax_feedin_threshold:

    Returns:
        dict: A dictionary containing the following results:
            - 'net_cash_flows': pd Dataframe including all cash flows in EUR.
            - 'annual_electricity_savings': Annual electricity savings in EUR.
            - 'annual_electricity_revenues': Annual electricity revenues by selling electricity into the grid in EUR.
            - 'payback_period': Payback period in years.
            - 'irr': Return on investment as a percentage.
            - 'npv': Net present value of the investment.

    """

    # Calculate annual electricity savings
    annual_electricity_savings = annual_electricity_production * electricity_rate * self_consumption_rate

    # Calculate annual electricity revenues for selling to the grid
    annual_electricity_feedin = annual_electricity_production * (1-self_consumption_rate)
    annual_electricity_revenues = annual_electricity_feedin * feed_in_tarif

    # Calculate annual depreciation expense
    depreciation_expense = system_cost * depreciation_rate
    depreciation_expense_for_feedin = depreciation_expense * (1-self_consumption_rate)

    # Calculate net cash flow for each year
    years = range(0, lifetime+1)
    years_idx = pd.Index(years, name="Jahre")
    net_cash_flows = pd.DataFrame(index=years_idx, columns=["Investition", "Steuer", "Eigenverbrauch", "Einspeisung"])
    tax_bases = pd.Series(index=years_idx)

    net_cash_flows.loc[years[0], "Investition"] = -system_cost
    net_cash_flows.loc[:, "Eigenverbrauch"] = annual_electricity_savings
    net_cash_flows.loc[:, "Einspeisung"] = annual_electricity_revenues

    if (pv_power > tax_power_threshold) or (annual_electricity_feedin > tax_feedin_threshold):
        tax_base = annual_electricity_revenues - depreciation_expense_for_feedin
        tax = tax_base * tax_rate
        net_cash_flows.loc[:, "Steuer"] = -tax
        tax_bases.loc[:] = tax_base
    else:
        net_cash_flows.loc[:, "Steuer"] = 0
        tax_bases.loc[:] = 0


    sum_of_cash_flows = net_cash_flows.sum(axis="columns")
    cumsum_of_cash_flows = sum_of_cash_flows.cumsum()

    # Calculate payback period
    payback_period = cumsum_of_cash_flows[cumsum_of_cash_flows > 0].idxmin()

    # Calculate net present value (NPV) of the investment
    npv = npf.npv(interest_rate, sum_of_cash_flows.tolist())

    # Calculate return on investment (ROI)
    irr = npf.irr(sum_of_cash_flows.tolist())

    # Create results dictionary
    results = {
        'net_cash_flows': net_cash_flows,
        'annual_electricity_savings': annual_electricity_savings,
        'annual_electricity_revenues': annual_electricity_revenues,
        'payback_period': payback_period,
        'irr': irr,
        'npv': npv,
        'tax_bases': tax_bases
    }

    return results
