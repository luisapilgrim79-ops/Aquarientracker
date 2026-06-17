import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date
import io

# Dateinamen für die "Datenbanken"
DATA_FILE = "aquarium_daten.csv"
NAMES_FILE = "aquarien_liste.txt"

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

# --- AQUARIEN-LISTE LADEN ODER INITIALISIEREN ---
def lade_aquarien():
    if os.path.exists(NAMES_FILE):
        with open(NAMES_FILE, "r", encoding="utf-8") as f:
            namen = [line.strip() for line in f.readlines() if line.strip()]
        if namen:
            return namen
    # Standardwerte, falls die Datei leer ist oder nicht existiert
    return ["Aquarium 1", "Aquarium 2"]

def speichere_aquarien(namen_liste):
    with open(NAMES_FILE, "w", encoding="utf-8") as f:
        for name in namen_liste:
            f.write(f"{name}\n")

aquarien_optionen = lade_aquarien()

# --- WASSERWERTE-DATEN LADEN ---
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df['Datum'] = pd.to_datetime(df['Datum'])
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
# Hier nutzen wir nun die dynamische Liste
eingabe_aquarium = st.sidebar.selectbox("Aquarium auswählen", aquarien_optionen)

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
    modus = st.radio("Ansichtsmodus:", ["Einzelansicht", "Direkter Vergleich (Alle Aquarien)"], horizontal=True)

    parameter_liste = ["pH", "Nitrit", "Nitrat", "Ammonium", "KH", "GH", "CO2"]
    ausgewaehlte_parameter = st.multiselect("Welche Werte möchtest du im Graphen sehen? (Mehrfachauswahl möglich)", options=parameter_liste, default=["pH"])

    if not ausgewaehlte_parameter:
        st.warning("Bitte wähle mindestens einen Wert aus, um den Graphen anzuzeigen.")
    else:
        if modus == "Einzelansicht":
            # Nutzt jetzt ebenfalls die dynamische Auswahlliste
            aquarium_auswahl = st.selectbox("Wähle das Aquarium für die Detailansicht:", aquarien_optionen)
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
            # Das Dropdown im Tabellen-Editor passt sich jetzt ebenfalls automatisch an deine Aquarien an
            "Aquarium": st.column_config.SelectboxColumn("Aquarium", options=aquarien_optionen, required=True),
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
        # Generiert dynamisch für jedes existierende Aquarium ein eigenes Tabellenblatt
        for aq in aquarien_optionen:
            df_aq = df_excel[df_excel["Aquarium"] == aq]
            if not df_aq.empty:
                df_aq.to_excel(writer, sheet_name=aq[:31], index=False) # Excel erlaubt max. 31 Zeichen pro Tab-Name
        df_excel.to_excel(writer, sheet_name="Alle Daten", index=False)
    
    st.download_button(
        label="📥 Als Excel-Datei (.xlsx) herunterladen",
        data=buffer.getvalue(),
        file_name=f"Aquarium_Wasserwerte_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- NEU: VERWALTUNGSBEREICH GANZ UNTEN ---
st.markdown("---")
st.subheader("🛠️ Aquarien verwalten")

col_neu, col_edit = st.columns(2)

with col_neu:
    st.markdown("**Neues Aquarium hinzufügen**")
    neues_aq_name = st.text_input("Name des neuen Aquariums", placeholder="z.B. Nano Cube 30L")
    if st.button("➕ Hinzufügen"):
        if neues_aq_name.strip():
            if neues_aq_name.strip() not in aquarien_optionen:
                aquarien_optionen.append(neues_aq_name.strip())
                speichere_aquarien(aquarien_optionen)
                st.success(f"'{neues_aq_name.strip()}' wurde erfolgreich hinzugefügt!")
                st.rerun()
            else:
                st.warning("Ein Aquarium mit diesem Namen existiert bereits.")
        else:
            st.error("Bitte gib einen gültigen Namen ein.")

with col_edit:
    st.markdown("**Bestehendes Aquarium umbenennen**")
    zu_aendern = st.selectbox("Welches Becken möchtest du umbenennen?", aquarien_optionen)
    neuer_name = st.text_input("Neuer Name", value=zu_aendern)
    
    if st.button("📝 Umbenennen bestätigen"):
        if neuer_name.strip() and neuer_name.strip() != zu_aendern:
            # 1. In der Namensliste aktualisieren
            neue_liste = [neuer_name.strip() if name == zu_aendern else name for name in aquarien_optionen]
            speichere_aquarien(neue_liste)
            
            # 2. In der bestehenden CSV-Datenbank alle alten Einträge umschreiben, damit keine Daten verloren gehen!
            if not df.empty:
                df["Aquarium"] = df["Aquarium"].replace(zu_aendern, neuer_name.strip())
                df.to_csv(DATA_FILE, index=False)
                
            st.success(f"Erfolgreich von '{zu_aendern}' in '{neuer_name.strip()}' geändert!")
            st.rerun()