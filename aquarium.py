import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date
import io

# Dateiname für die "Datenbank"
DATA_FILE = "aquarium_daten.csv"

# Farbschema für die Parameter festlegen
FARB_MAP = {
    "pH": "#0000FF",         # Blau
    "KH": "#FFA500",         # Orange
    "Nitrit": "#FF00FF",     # Magenta
    "Nitrat": "#FFFF00",     # Gelb
    "CO2": "#90EE90",        # Hellgrün
    "Ammonium": "#00CED1",   # Türkis
    "GH": "#808080"          # Grau
}

def berechne_co2(ph, kh):
    if ph > 0 and kh > 0:
        try:
            co2 = 3.0 * kh * (10 ** (7.0 - ph))
            return round(co2, 1)
        except:
            return 0.0
    return 0.0

# 1. Daten laden oder neu erstellen
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df['Datum'] = pd.to_datetime(df['Datum'])
    # Falls die Temperatur noch in einer alten CSV existiert, werfen wir sie hier für die Anzeige raus
    if "Temperatur" in df.columns:
        df = df.drop(columns=["Temperatur"])
else:
    df = pd.DataFrame(columns=[
        "Datum", "Aquarium", "pH", "Nitrit", "Nitrat", "Ammonium", "KH", "GH", "CO2"
    ])

# Streamlit App Layout
st.set_page_config(page_title="Aquarien Wasserwerte Tracker Pro", layout="wide")
st.title("🐟 Aquarien Wasserwerte Tracker Pro")

# --- SEITENLEISTE: NEUE DATEN EINGEBEN ---
st.sidebar.header("📝 Neue Werte eintragen")

eingabe_datum = st.sidebar.date_input("Datum", date.today())
eingabe_aquarium = st.sidebar.selectbox("Aquarium auswählen", ["Aquarium 1", "Aquarium 2"])

# Letzte Werte als Voreinstellung suchen
df_aquarium_aktuell = df[df["Aquarium"] == eingabe_aquarium]

if not df_aquarium_aktuell.empty:
    letzter_eintrag = df_aquarium_aktuell.sort_values(by="Datum").iloc[-1]
    start_ph = float(letzter_eintrag["pH"])
    start_no2 = float(letzter_eintrag["Nitrit"])
    start_no3 = float(letzter_eintrag["Nitrat"])
    start_nh4 = float(letzter_eintrag["Ammonium"])
    start_kh = float(letzter_eintrag["KH"])
    start_gh = float(letzter_eintrag["GH"])
else:
    start_ph = 7.0
    start_no2 = 0.000
    start_no3 = 0.0
    start_nh4 = 0.0
    start_kh = 0.0
    start_gh = 0.0

st.sidebar.subheader("Messwerte")
eingabe_ph = st.sidebar.number_input("pH-Wert (3.0 - 10.0)", min_value=3.0, max_value=10.0, value=start_ph, step=0.1)
eingabe_no2 = st.sidebar.number_input("Nitrit (NO2 in mg/l)", min_value=0.000, value=start_no2, step=0.025, format="%.3f")
eingabe_no3 = st.sidebar.number_input("Nitrat (NO3 in mg/l)", min_value=0.0, value=start_no3, step=1.0)
eingabe_nh4 = st.sidebar.number_input("Ammonium (NH4 in mg/l)", min_value=0.0, value=start_nh4, step=0.1)
eingabe_kh = st.sidebar.number_input("Karbonathärte (KH)", min_value=0.0, value=start_kh, step=0.5)
eingabe_gh = st.sidebar.number_input("Gesamthärte (GH)", min_value=0.0, value=start_gh, step=0.5)

berechneter_co2 = berechne_co2(eingabe_ph, eingabe_kh)
st.sidebar.info(f"💡 Automatisch berechneter CO2-Wert: **{berechneter_co2} mg/l**")

if st.sidebar.button("Werte speichern"):
    neue_daten = pd.DataFrame([{
        "Datum": pd.to_datetime(eingabe_datum),
        "Aquarium": eingabe_aquarium,
        "pH": eingabe_ph,
        "Nitrit": eingabe_no2,
        "Nitrat": eingabe_no3,
        "Ammonium": eingabe_nh4,
        "KH": eingabe_kh,
        "GH": eingabe_gh,
        "CO2": berechneter_co2
    }])
    df = pd.concat([df, neue_daten], ignore_index=True)
    df = df.sort_values(by="Datum")
    df.to_csv(DATA_FILE, index=False)
    st.sidebar.success("Werte erfolgreich gespeichert!")
    st.rerun()

# --- HAUPTBEREICH: AUSWERTUNG ---
if df.empty:
    st.info("Noch keine Daten vorhanden. Trage links in der Seitenleiste deine ersten Werte ein!")
else:
    modus = st.radio("Ansichtsmodus:", ["Einzelansicht", "Direkter Vergleich (Beide Aquarien)"], horizontal=True)

    parameter_liste = ["pH", "Nitrit", "Nitrat", "Ammonium", "KH", "GH", "CO2"]
    ausgewaehlte_parameter = st.multiselect("Welche Werte möchtest du im Graphen sehen? (Mehrfachauswahl möglich)", options=parameter_liste, default=["pH"])

    if not ausgewaehlte_parameter:
        st.warning("Bitte wähle mindestens einen Wert aus, um den Graphen anzuzeigen.")
    else:
        if modus == "Einzelansicht":
            aquarium_auswahl = st.selectbox("Wähle das Aquarium für die Detailansicht:", ["Aquarium 1", "Aquarium 2"])
            df_gefiltert = df[df["Aquarium"] == aquarium_auswahl]

            if df_gefiltert.empty:
                st.warning(f"Noch keine Daten für {aquarium_auswahl} eingetragen.")
            else:
                df_melted_single = df_gefiltert.melt(id_vars=["Datum"], value_vars=ausgewaehlte_parameter, var_name="Parameter", value_name="Wert")
                fig = px.line(df_melted_single, x="Datum", y="Wert", color="Parameter", title=f"Verlauf für {aquarium_auswahl}", markers=True, color_discrete_map=FARB_MAP)
                st.plotly_chart(fig, use_container_width=True)
        else:
            df_melted = df.melt(id_vars=["Datum", "Aquarium"], value_vars=ausgewaehlte_parameter, var_name="Parameter", value_name="Wert")
            df_melted["Linie"] = df_melted["Aquarium"] + " (" + df_melted["Parameter"] + ")"
            fig = px.line(df_melted, x="Datum", y="Wert", color="Linie", title="Direkter Vergleich aller ausgewählten Werte", markers=True)
            st.plotly_chart(fig, use_container_width=True)

    # --- DATEN-EDITOR ---
    st.markdown("---")
    st.subheader("📊 Datentabelle (Direkt bearbeitbar)")
    st.caption("💡 Anleitung: Doppelklick in eine Zelle zum Ändern. Zeile markieren + 'Entf'-Taste zum Löschen.")

    df_anzeige = df.copy()
    df_anzeige['Datum'] = df_anzeige['Datum'].dt.date

    edited_df = st.data_editor(
        df_anzeige, 
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Datum": st.column_config.DateColumn("Datum", required=True),
            "Aquarium": st.column_config.SelectboxColumn("Aquarium", options=["Aquarium 1", "Aquarium 2"], required=True),
            "pH": st.column_config.NumberColumn("pH", min_value=3.0, max_value=10.0, format="%.2f"),
            "Nitrit": st.column_config.NumberColumn("Nitrit", format="%.3f"),
            "CO2": st.column_config.NumberColumn("CO2 (Berechnet)", disabled=True)
        }
    )

    if st.button("💾 Änderungen in Tabelle speichern"):
        edited_df['Datum'] = pd.to_datetime(edited_df['Datum'])
        
        for idx, row in edited_df.iterrows():
            edited_df.at[idx, "CO2"] = berechne_co2(row["pH"], row["KH"])
            
        edited_df = edited_df.sort_values(by="Datum")
        edited_df.to_csv(DATA_FILE, index=False)
        st.success("Änderungen erfolgreich in der CSV-Datei gespeichert!")
        st.rerun()

    # --- EXCEL EXPORT ---
    st.markdown("---")
    st.subheader("📂 Daten exportieren")
    
    df_excel = df.copy()
    df_excel['Datum'] = df_excel['Datum'].dt.strftime('%Y-%m-%d')
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_excel[df_excel["Aquarium"] == "Aquarium 1"].to_excel(writer, sheet_name="Aquarium 1", index=False)
        df_excel[df_excel["Aquarium"] == "Aquarium 2"].to_excel(writer, sheet_name="Aquarium 2", index=False)
        df_excel.to_excel(writer, sheet_name="Alle Daten", index=False)
    
    st.download_button(
        label="📥 Als Excel-Datei (.xlsx) herunterladen",
        data=buffer.getvalue(),
        file_name=f"Aquarium_Wasserwerte_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )