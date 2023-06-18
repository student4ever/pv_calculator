import pandas as pd
import numpy_financial as npf
import streamlit as st
from .utils import fig_and_link


def get_color_pre_and_post_str(color):
    if color is not None:
        return ":{}[".format(color), "]"
    else:
        return "", ""


def get_technical_inputs(col, color=None):

    color_pre_str, color_post_str = get_color_pre_and_post_str(color)

    with col:
        pv_power = st.number_input(
            label=color_pre_str+"Größe der PV Anlage in kW"+color_post_str,
            value=10,
            key=col
        )

        annual_fullload_hours = st.number_input(
            label=color_pre_str+"Jährliche Volllaststunden in h " + color_post_str +""" (*Maßgeblicher Parameter für die jährliche Produktionsmenge, 
            welche sich aus dem Produkt aus Volllaststunden und Größe der PV Anlage ergibt (h * kW = kWh).*)""",
            value=1000,
            key=col
        )

        annual_electricity_production = annual_fullload_hours * pv_power

        st.write("➡ Jährliche Produktionsmenge {:,.2f} kWh".format(annual_electricity_production))

        # annual_power_consumption = st.number_input(
        #     label="Eigener Stromverbrauch in kWh",
        #     value=2000,
        #     key=col
        # )

        self_consumption_rate = st.number_input(
            label=color_pre_str+"Eigenverbrauchsgrad in %"+color_post_str,
            value=10,
            key=col
        ) / 100

    inputs = {
        "pv_power": pv_power,
        # "annual_fullload_hours": annual_fullload_hours,
        "annual_electricity_production": annual_electricity_production,
        # "annual_power_consumption": annual_power_consumption,
        "self_consumption_rate": self_consumption_rate
    }

    return inputs


def get_economic_inputs(col, color=None):

    color_pre_str, color_post_str = get_color_pre_and_post_str(color)

    with col:
        system_cost = st.number_input(
                label=color_pre_str+"Kosten der Anlage in EUR"+color_post_str,
                value=10000,
                key=col
            )

        subsidy = st.number_input(
                label=color_pre_str+"Förderung der Anlage in EUR"+color_post_str,
                value=0,
                key=col
            )

        depreciation_period = st.number_input(
                label=color_pre_str+"Abschreibedauer der Anlage in Jahren"+color_post_str,
                value=20,
                key=col
            )

        electricity_rate = st.number_input(
                label=color_pre_str+"Kosten des Netzbezugs in EUR/kWh"+color_post_str,
                value=0.15,
                key=col
            )

        feed_in_tarif = st.number_input(
                label=color_pre_str+"Einspeisetarif in EUR/kWh"+color_post_str,
                value=0.1,
                key=col
            )

        interest_rate = st.number_input(
                label=color_pre_str+"Zinssatz in %"+color_post_str,
                value=5,
                key=col
            )/100

    inputs = {
        "system_cost": system_cost,
        "subsidy": subsidy,
        "depreciation_period": depreciation_period,
        "electricity_rate": electricity_rate,
        "feed_in_tarif": feed_in_tarif,
        "interest_rate": interest_rate,
    }

    return inputs


def get_tax_inputs(col, color=None):

    color_pre_str, color_post_str = get_color_pre_and_post_str(color)

    with col:

        tax_power_threshold = st.number_input(
                label=color_pre_str+"Schwellenwert Leistung in kWp"+color_post_str,
                value=25,
                key=col
            )

        tax_feedin_threshold = st.number_input(
                label=color_pre_str+"Schwellenwert Einspeisemenge in kWh (Freibetrag)"+color_post_str,
                value=12500,
                key=col
            )

        tax_rate = st.number_input(
                label=color_pre_str+"Grenzsteuersatz in %"+color_post_str,
                value=42,
                key=col
            )/100

    inputs = {
        "tax_power_threshold": tax_power_threshold,
        "tax_feedin_threshold": tax_feedin_threshold,
        "tax_rate": tax_rate
    }

    return inputs


def calculate_solar_pv_economics(system_cost, subsidy, pv_power, annual_electricity_production, electricity_rate, feed_in_tarif,
                                interest_rate, depreciation_period, self_consumption_rate,
                                tax_power_threshold=25, tax_feedin_threshold=12500, tax_rate=0.42):
    """
    Calculate the economics of a solar PV system for a residential customer.

    Args:
        system_cost (float): Cost of the solar PV system in EUR.
        subsidy (float): Subsity of the solar PV system in EUR
        pv_power (float): Installed Power of the solar PV system in kWp
        annual_electricity_production (float): Annual electricity production in kWh.
        electricity_rate (float): Electricity rate in EUR/kWh.
        feed_in_tarif (float): Electricity rate feedin EUR/kWh.
        interest_rate (float): Annual interest rate as a decimal (e.g., 0.05 for 5%).
        depreciation_period (float): Annual depreciation period as a decimal (e.g., 10 for 10 years).
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
    depreciation_rate = 1/depreciation_period
    depreciation_expense = system_cost * depreciation_rate
    depreciation_expense_for_feedin = depreciation_expense * (1-self_consumption_rate)

    # Calculate net cash flow for each year
    years = range(0, depreciation_period+1)
    years_idx = pd.Index(years, name="Jahre")
    net_cash_flows = pd.DataFrame(index=years_idx, columns=["Investition in EUR", "Steuer in EUR", "Eigenverbrauch in EUR", "Einspeisung in EUR"])
    tax_bases = pd.Series(index=years_idx)

    net_cash_flows.loc[years[0], "Investition in EUR"] = -system_cost
    net_cash_flows.loc[years[0], "Förderung in EUR"] = subsidy
    net_cash_flows.loc[:, "Eigenverbrauch in EUR"] = annual_electricity_savings
    net_cash_flows.loc[:, "Einspeisung in EUR"] = annual_electricity_revenues

    if (pv_power > tax_power_threshold) or (annual_electricity_feedin > tax_feedin_threshold):
        tax_base = annual_electricity_revenues - depreciation_expense_for_feedin
        tax = tax_base * tax_rate
        net_cash_flows.loc[:, "Steuer in EUR"] = -tax
        tax_bases.loc[:] = tax_base
    else:
        net_cash_flows.loc[:, "Steuer in EUR"] = 0
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


def format_german_nb(number, decimal=0, unit="EUR"):
    if decimal == 0:
        str_format = "{:,.0f} {}".format(float(number), unit)
    elif decimal == 1:
        str_format = "{:,.1f} {}".format(float(number), unit)
    else:
        str_format = "{:,.2f} {}".format(float(number), unit)
    mystr = str_format.replace(",", ' ').replace(".", ',')
    return mystr


def rename_columns(dataframe, old_part, new_part):
    df = dataframe.copy()
    new_columns = [col.replace(old_part, new_part) for col in df.columns]
    df.columns = new_columns
    return df


def show_one_scenario(e, key):

    col1, col2, col3 = st.columns(3)
    col1.metric("Nettobarwert", format_german_nb(format(e["npv"]), 0, "EUR"), )
    col2.metric("Amortisierungszeit", format_german_nb(format(e["payback_period"]), 0, "Jahre"), )
    col3.metric("IRR", format_german_nb(format(e["irr"] * 100), 2, "%"), )

    # Print the results
    st.markdown("### Gesamtergebnis")
    ncf = e["net_cash_flows"]

    fig_and_link(
        rename_columns(ncf, "EUR", "Tausend EUR") / 1e3,
        add_on={
            "line": {"data": ncf.sum(axis="columns").cumsum() / 1e3,
                     "name": "Kummulierter Netto-Cash-Flow", "color": "darkred", "width": 2},
        },
        title="Entwicklung des Netto-Cash-Flows", unit="Tausend EUR", kind="bar-stacked",
        download_link=False
    )

    if st.checkbox("Tabelle der Investitionsrechnung anzeigen", False, key=key):
        st.markdown("Ergebnis der Investitionsrechnung im internationalen Zahlenformat (Tausender Trennzeichen ',' und Komma '.'")
        st.table(ncf.fillna(0).style.format("{:,.2f}"))

    st.markdown("### Steuerlich")
    tax_bases = e["tax_bases"]

    fig_and_link(
        tax_bases.cumsum() / 1e3,
        title="Entwicklung der kummulativen Steuerlichen Bemessungsgrundlage", unit="Tausend EUR", kind="bar",
        download_link=False
    )

    if st.checkbox("Tabelle der Steuerlichen Bemessungsgrundlage anzeigen", False, key=key):
        st.markdown("Ergebnis der Investitionsrechnung im internationalen Zahlenformat (Tausender Trennzeichen ',' und Komma '.'")
        st.table(tax_bases.fillna(0).cumsum().to_frame("Steuerliche Bemessungsgrundlage").style.format("{:,.2f}"))

