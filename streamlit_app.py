import streamlit as st
from src.functions import *
from src.utils import *
import plotly.graph_objects as go

st.set_page_config(
    layout="centered", page_icon="⚡", page_title="PV App"
)
st.title("⚡ Photovoltaik Rechner | HOLZINGER.TAX")

# Description
with st.expander("Beschreibung"):
    st.markdown("""
        Der Rechner berechnet die Wirtschaftlichkeit einer Photovolatikanlage für einen Verbraucher. 
        Er berücksichtigt dynamische wirtschaftliche Analysen wie den Zinssatz und die Abschreibung. 
        Zudem wird die Eigenverbrauchsquote in Betracht gezogen. 
        Basierend auf den angegebenen Parametern und Eingabedaten wird der **Nettobarwert (NPV)**, der **interne Zinssatz (IRR)** und die **Amortisationszeit**  der Photovoltaikanlage ermittelt.

        Der Rechner summiert die erwarteten Einnahmen und Ausgaben im Laufe der Lebensdauer der Photovoltaikanlage. 
        Hierbei werden der Stromverkauf (Netzeinspeisung), die eingesparten Stromkosten durch Eigenverbrauch und mögliche Förderungen oder Steuervorteile berücksichtigt. 
        
        Anschließend werden die Barwerte der Cashflows unter Berücksichtigung des Diskontierungssatzes berechnet, um den NPV zu ermitteln.
    
        Der Rechner hilft die Rentabilität der Solaranlage abzuschätzen und fundierte Entscheidungen über die Investition in erneuerbare Energien zu treffen.
    """)

import streamlit as st
from PIL import Image

image = Image.open('schema.png')

st.image(image, caption='Schematische Beschreibung der Berechnungsmethode. ')


# input data
st.markdown("## Annahmen")
number_of_simulation = st.radio(label="Anzahl an Szenarien", options=[1, 2, 3])
# array of dicts for the input
inputs = [dict() for x in range(number_of_simulation)]
colors_scenarios = ["blue", "orange", "green"]

tab1, tab2, tab3 = st.tabs(["Technisch", "Wirtschaftlich", "Steuerlich"])

with tab1:
    st.markdown("Technische Annahmen")

    cols = st.columns(number_of_simulation)
    for c, i, color in zip(cols, range(number_of_simulation), colors_scenarios):
        with c:
            d = get_technical_inputs(c, color)
            inputs[i] = {**inputs[i], **d}


with tab2:
    st.markdown("Wirtschafliche Annahmen")

    cols = st.columns(number_of_simulation)
    for c, i, color in zip(cols, range(number_of_simulation), colors_scenarios):
        with c:
            d = get_economic_inputs(c, color)
            inputs[i] = {**inputs[i], **d}

with tab3:
    st.markdown("Steuerlichen Annahmen")

    cols = st.columns(number_of_simulation)
    for c, i, color in zip(cols, range(number_of_simulation), colors_scenarios):
        with c:
            d = get_tax_inputs(c, color)
            inputs[i] = {**inputs[i], **d}

# to do
# - miete
# - gebühren
# - fremdfinanzierung
# - download als csv

st.markdown("## Ergebnis")

economics = [dict() for x in range(number_of_simulation)]

scenario_names = ["Szenario {}".format((int(x+1))) for x in range(number_of_simulation)]

cumulative_ncf = pd.DataFrame(columns=scenario_names)
for i in range(number_of_simulation):
    economics[i] = calculate_solar_pv_economics(**inputs[i])
    cumulative_ncf.iloc[:, i] = economics[i]["net_cash_flows"].sum(axis="columns").cumsum()

if number_of_simulation > 1:
    fig_and_link(
        cumulative_ncf / 1e3,
        title="Entwicklung des Netto-Cash-Flows aller Szenarien", unit="Tausend EUR", kind="line",
        download_link=False
    )

result_tabs = st.tabs(scenario_names)

for result_tab, i in zip(result_tabs, range(number_of_simulation)):
    with result_tab:
        show_one_scenario(economics[i], result_tab)

with st.expander("Haftungsausschluss"):
    st.markdown("""
        Die Nutzung dieser App erfolgt auf eigene Gefahr. 
        Wir übernehmen keinerlei Verantwortung oder Haftung für eventuelle Schäden, die durch die Verwendung dieser App entstehen könnten. 
        Dieser Haftungsausschluss gilt für alle Funktionen, Inhalte und Informationen innerhalb der App.
        
        Die in dieser App bereitgestellten Informationen dienen ausschließlich zu Informationszwecken. 
        Wir bemühen uns, genaue und aktuelle Informationen bereitzustellen, können jedoch keine Gewähr für die Richtigkeit, Vollständigkeit oder Aktualität der Informationen übernehmen.
        
        Diese App stellt keine Rechts-, Finanz- oder technische Beratung dar. 
        Sie sollte nicht als Ersatz für professionelle Beratung oder Fachkenntnisse herangezogen werden. 
        Wir empfehlen Ihnen dringend, sich bei Bedarf von qualifizierten Fachleuten beraten zu lassen.
        
        Wir haften nicht für etwaige Verluste, Schäden oder Konsequenzen, die sich aus der Nutzung dieser App ergeben. 
        Dies schließt direkte, indirekte, zufällige, besondere oder Folgeschäden ein, auch wenn wir auf die Möglichkeit solcher Schäden hingewiesen wurden.
        
        Wir behalten uns das Recht vor, den Inhalt dieser App jederzeit und ohne vorherige Ankündigung zu ändern, zu aktualisieren oder zu entfernen.
        
        Durch die Nutzung dieser App erklären Sie sich damit einverstanden, dass Sie alle Risiken im Zusammenhang mit der Nutzung dieser App tragen und uns von jeglicher Haftung freistellen.
        
        Bitte konsultieren Sie bei spezifischen Fragen oder Bedenken einen Rechts- oder Fachexperten, um eine sachkundige Beratung zu erhalten.
    """)
