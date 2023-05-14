import streamlit as st
from src.functions import calculate_solar_pv_economics
from src.utils import *
import plotly.graph_objects as go

st.set_page_config(
    layout="centered", page_icon="⚡", page_title="PV App"
)
st.title("⚡ Photovolataik Rechner | HOLZINGER.TAX")

# Load the data
if 0:
    sheet_id = "1ZRFcyil83dX7jwTFI37AS8zjvrwBinAMwQ8ZMkQnu8s"

    sheet_name = "app_text"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    total_text = pd.read_csv(url, index_col=[0], header=[0])

    sheet_name = "app_data"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    total_data = pd.read_csv(url, index_col=[0], decimal=",")

# input data
st.markdown("## Technische Annahmen")

pv_power = st.number_input(
        label="Größe der PV Anlage in kW",
        value=10,
    )

annual_fullload_hours = st.number_input(
        label="Volllaststunden im Jahr",
        value=1000,
    )

annual_electricity_production = annual_fullload_hours * pv_power

annual_power_consumption = st.number_input(
        label="Eigener Stromverbrauch in kWh",
        value=2000,
    )

self_consumption_rate = st.number_input(
        label="Eigenverbrauchsgrad in %",
        value=10,
    )/100

st.markdown("## Ökonomische Annahmen")
system_cost = st.number_input(
        label="Kosten der Anlage in EUR",
        value=10000,
    )

lifetime = st.number_input(
        label="Lebensdauer der Anlage in Jahren",
        value=20,
    )

depreciation_rate = 1/ st.number_input(
        label="Abschreibedauer der Anlage in Jahren",
        value=20,
    )

electricity_rate = st.number_input(
        label="Kosten des Netzbezugs in EUR/kWh",
        value=0.15,
    )

feed_in_tarif = st.number_input(
        label="Einspeisetarif in EUR/kWh",
        value=0.1,
    )

interest_rate = st.number_input(
        label="Zinssatz in %",
        value=5,
    )/100

st.markdown("## Steuerlichen Annahmen")
tax_power_threshold = st.number_input(
        label="Schwellewert Leistung in kWp",
        value=25,
    )

tax_feedin_threshold = st.number_input(
        label="Schwellewert Einspeisemenge in kWh",
        value=12500,
    )

tax_rate = st.number_input(
        label="Grenzsteuersatz in %",
        value=42,
    )/100


# to do
# - miete
# - gebühren
# - fremdfinanzierung
# - cumulated tax base

st.markdown("## Ergebnis")
e = calculate_solar_pv_economics(system_cost, pv_power, annual_electricity_production, electricity_rate, feed_in_tarif,
                                         interest_rate, depreciation_rate, self_consumption_rate, lifetime,
                                         tax_power_threshold, tax_feedin_threshold, tax_rate)


def format_german_nb(number, decimal=0, unit="EUR"):
    if decimal == 0:
        str_format = "{:,.0f} {}".format(float(number), unit)
    elif decimal == 1:
        str_format = "{:,.1f} {}".format(float(number), unit)
    else:
        str_format = "{:,.2f} {}".format(float(number), unit)
    mystr = str_format.replace(",", ' ').replace(".", ',')
    return mystr

col1, col2, col3 = st.columns(3)
col1.metric("Nettobarwert", format_german_nb(format(e["npv"]), 0, "EUR"), )
col2.metric("Amortisierungszeit", format_german_nb(format(e["payback_period"]), 0, "Jahre"), )
col3.metric("IRR", format_german_nb(format(e["irr"]*100), 2, "%"), )


# Print the results
st.markdown("### Gesamtergebnis")
ncf = e["net_cash_flows"]

fig_and_link(
    ncf/1e3,
    add_on={
        "line": {"data": ncf.sum(axis="columns").cumsum()/1e3,
                 "name": "Kummulierter Netto-Cash-Flow", "color": "darkred", "width": 2},
    },
    title="Entwicklung des Netto-Cash-Flows", unit="Tausend EUR", kind="bar-stacked"
)

st.text("Ergebnis der Investitionsrechnung")
st.table(ncf.fillna(0))


st.markdown("### Steuerlich")
tax_bases = e["tax_bases"]

fig_and_link(
    tax_bases.cumsum()/1e3,
    title="Entwicklung der kummulativen steuerlichen Bemessungsgrundlage", unit="Tausend EUR", kind="bar"
)
import locale

# Set the German locale
locale.setlocale(locale.LC_ALL, 'de_DE')

formatted_df = tax_bases.fillna(0).cumsum().to_frame().applymap(lambda x: locale.format_string("%.2f", x))
st.table(formatted_df)

st.table(tax_bases.fillna(0).cumsum().to_frame("Steuerliche Bemessungsgrundlage").style.format("{:,.0f}"))


