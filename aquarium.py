import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date
import io

# Dateinamen für die "Datenbanken"
DATA_FILE = "aquarium_daten.csv"
NAMES_FILE = "aquarien_liste.txt"

# EXAKT DEINE WUNSCH-FARBEN ALS HEX-CODES
FARB_MAP = {
    "pH (3-10)": "#00B1FF",      # Hellblau
    "KH": "#FF9000",             # Orange
    "Nitrit (NO2)": "#AB004B",    # Dunkelrot/Magenta
    "Nitrat (NO3)": "#FFAA00",    # Gelb/Orange
    "CO2": "#6AFF40",            # Hellgrün
    "Ammonium (NH4)": "#00594D",  # Dunkelgrün
    "GH": "#6B6B6B"              # Grau
}

LINIEN_STILE = ["solid", "dash", "dot", "dashdot", "longdash", "longdashdot"]

def berechne_co2(ph, kh):
    if ph > 0 and kh > 0:
        try: return round(3.0 * kh * (10 ** (7.0 - ph)), 1)
        except: return 0.0
    return 0.0

def lade_aquarien():
    if os.path.exists(NAMES_FILE):
        with open(NAMES_FILE, "r", encoding="utf-8") as f:
            namen = [line.strip() for line in f.readlines() if line.strip()]
        if namen: return namen
    return ["Aquarium 1", "Aquarium 2"]

def speichere_aquarien(namen_liste):
    with open(NAMES_FILE, "w", encoding="utf-8") as f:
        for name in namen_liste: f.write(f"{name}\n")

aquarien_optionen = lade_aquarien()

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df['Datum'] = pd.to_datetime(df['Datum'])
    rename_db = {"pH": "pH (3-10)", "Nitrit": "Nitrit (NO2)", "Nitrat": "Nitrat (NO3)", "Ammonium": "Ammonium (NH4)"}
    df.rename(columns=rename_db, inplace=True)
    if "Nitrit (NO2)" in df.columns: df["Nitrit (NO2)"] = df["Nitrit (NO2)"].round(2)
else:
    df = pd.DataFrame(columns=["Datum", "Aquarium", "pH (3-10)", "Nitrit (NO2)", "Nitrat (NO3)", "Ammonium (NH4)", "KH", "GH", "CO2"])

st.set_page_config(page_title="Aquarien Wasserwerte Tracker Pro", layout="wide")
st.title("🐟 Aquarien Wasserwerte Tracker Pro")

# --- CSS INJEKTION FÜR THEME-UNABHÄNGIGE FARBIGE CHIPS IM MULTISELECT ---
# Nutzt jetzt einen robusten Selektor, der den Textinhalt der Tags unabhängig vom Dark/Light-Mode ansteuert
st.markdown("""
    <style>
        /* Erzwinge die Farben basierend auf den aria-labels und inneren Divs */
        div[data-baseweb="tag"][aria-label*="pH (3-10)"], div[data-baseweb="tag"] span[title*="pH (3-10)"] { background-color: #00B1FF !important; color: white !important; }
        div[data-baseweb="tag"][aria-label*="KH"], div[data-baseweb="tag"] span[title*="KH"] { background-color: #FF9000 !important; color: white !important; }
        div[data-baseweb="tag"][aria-label*="Nitrit (NO2)"], div[data-baseweb="tag"] span[title*="Nitrit (NO2)"] { background-color: #AB004B !important; color: white !important; }
        div[data-baseweb="tag"][aria-label*="Nitrat (NO3)"], div[data-baseweb="tag"] span[title*="Nitrat (NO3)"] { background-color: #FFAA00 !important; color: white !important; }
        div[data-baseweb="tag"][aria-label*="CO2"], div[data-baseweb="tag"] span[title*="CO2"] { background-color: #6AFF40 !important; color: black !important; }
        div[data-baseweb="tag"][aria-label*="Ammonium (NH4)"], div[data-baseweb="tag"] span[title*="Ammonium (NH4)"] { background-color: #00594D !important; color: white !important; }
        div[data-baseweb="tag"][aria-label*="GH"], div[data-baseweb="tag"] span[title*="GH"] { background-color: #6B6B6B !important; color: white !important; }
        
        /* Allgemeiner Fix für Textfarbe in den Buttons, falls das Theme überschreibt */
        div[data-baseweb="tag"] { color: white !important; border-radius: 4px !important; }
        div[data-baseweb="tag"][aria-label*="CO2"] { color: black !important; }
        
        /* Schließ-Kreuzchen (X) in den Tags lesbar und weiß/schwarz machen */
        div[data-baseweb="tag"] role[button], div[data-baseweb="tag"] svg { fill: currentColor !important; color: inherit !important; }
    </style>
""", unsafe_allow_html=True)

# --- REUSABLE IMPORT FUNCTION ---
def verarbeite_excel_import(uploaded_file):
    try:
        xl = pd.ExcelFile(uploaded_file)
        import_dfs = []
        
        for sheet in xl.sheet_names:
            sheet_df = xl.parse(sheet)
            if not sheet_df.empty:
                sheet_df.columns = [str(c).strip() for c in sheet_df.columns]
                rename_dict = {
                    "date": "Datum", "date_input": "Datum", "aquarium": "Aquarium", "becken": "Aquarium",
                    "ph": "pH (3-10)", "ph-wert": "pH (3-10)", "ph (3-10)": "pH (3-10)",
                    "kh": "KH", "karbonathärte": "KH", "gh": "GH", "gesamthärte": "GH",
                    "nitrit": "Nitrit (NO2)", "no2": "Nitrit (NO2)", "nitrit (no2)": "Nitrit (NO2)",
                    "nitrat": "Nitrat (NO3)", "no3": "Nitrat (NO3)", "nitrat (no3)": "Nitrat (NO3)",
                    "ammonium": "Ammonium (NH4)", "nh4": "Ammonium (NH4)", "ammonium (nh4)": "Ammonium (NH4)"
                }
                sheet_df.rename(columns=lambda x: rename_dict.get(x.lower(), x), inplace=True)
                import_dfs.append(sheet_df)
        
        if import_dfs:
            all_imported = pd.concat(import_dfs, ignore_index=True)
            for col in ["Datum", "Aquarium", "pH (3-10)", "KH", "GH", "Nitrit (NO2)", "Nitrat (NO3)", "Ammonium (NH4)"]:
                if col not in all_imported.columns: all_imported[col] = None
            
            all_imported["Datum"] = pd.to_datetime(all_imported["Datum"])
            all_imported = all_imported.dropna(subset=["Datum"])
            all_imported["Nitrit (NO2)"] = pd.to_numeric(all_imported["Nitrit (NO2)"]).round(2)
            all_imported["pH (3-10)"] = pd.to_numeric(all_imported["pH (3-10)"])
            all_imported["KH"] = pd.to_numeric(all_imported["KH"])
            all_imported["CO2"] = all_imported.apply(lambda r: berechne_co2(r["pH (3-10)"], r["KH"]), axis=1)
            
            return all_imported
    except Exception as e:
        st.error(f"Fehler beim Import: {e}")
    return None

# --- INTERAKTIVES POP-UP FÜR UNBEKANNTE AQUARIEN ---
@st.dialog("⚠️ Unbekannte Aquarien gefunden!")
def zeige_import_dialog(neue_aquarien, import_df):
    st.warning("In deiner Excel-Datei wurden Aquarien gefunden, die in der App noch nicht existieren:")
    for aq in neue_aquarien:
        st.markdown(f"* **{aq}**")
    st.markdown("Möchtest du diese Aquarien automatisch anlegen und alle Messwerte importieren?")
    
    col_ja, col_nein = st.columns(2)
    with col_ja:
        if st.button("👍 Ja, alles importieren"):
            aktuelle_liste = lade_aquarien()
            for aq in neue_aquarien:
                if aq not in aktuelle_liste: aktuelle_liste.append(aq)
            speichere_aquarien(aktuelle_liste)
            
            global df
            final_df = pd.concat([df, import_df], ignore_index=True)
            final_df = final_df.drop_duplicates(subset=["Datum", "Aquarium"], keep="last").sort_values(by="Datum")
            
            save_df = final_df.copy()
            save_df.rename(columns={"pH (3-10)": "pH", "Nitrit (NO2)": "Nitrit", "Nitrat (NO3)": "Nitrat", "Ammonium (NH4)": "Ammonium"}, inplace=True)
            save_df.to_csv(DATA_FILE, index=False)
            
            st.success("Erfolgreich importiert!")
            st.rerun()
            
    with col_nein:
        if st.button("❌ Abbrechen"): st.rerun()

# --- SEITENLEISTE: MANUELLE EINGABE ---
st.sidebar.header("📝 Neue Werte eintragen")
eingabe_datum = st.sidebar.date_input("Datum", date.today())
eingabe_aquarium = st.sidebar.selectbox("Aquarium auswählen", aquarien_optionen)

df_aquarium_aktuell = df[df["Aquarium"] == eingabe_aquarium]
if not df_aquarium_aktuell.empty:
    letzter = df_aquarium_aktuell.sort_values(by="Datum").iloc[-1]
    start_ph = float(letzter["pH (3-10)"]) if "pH (3-10)" in letzter and pd.notna(letzter["pH (3-10)"]) else 7.0
    start_no2 = float(letzter["Nitrit (NO2)"]) if "Nitrit (NO2)" in letzter and pd.notna(letzter["Nitrit (NO2)"]) else 0.00
    start_no3 = float(letzter["Nitrat (NO3)"]) if "Nitrat (NO3)" in letzter and pd.notna(letzter["Nitrat (NO3)"]) else 0.0
    start_nh4 = float(letzter["Ammonium (NH4)"]) if "Ammonium (NH4)" in letzter and pd.notna(letzter["Ammonium (NH4)"]) else 0.0
    start_kh = float(letzter["KH"]) if "KH" in letzter and pd.notna(letzter["KH"]) else 0.0
    start_gh = float(letzter["GH"]) if "GH" in letzter and pd.notna(letzter["GH"]) else 0.0
else:
    start_ph, start_no2, start_no3, start_nh4, start_kh, start_gh = 7.0, 0.00, 0.0, 0.0, 0.0, 0.0

eingabe_no2 = st.sidebar.number_input("Nitrit (NO2 in mg/l)", min_value=0.00, value=start_no2, step=0.05, format="%.2f")
eingabe_no3 = st.sidebar.number_input("Nitrat (NO3 in mg/l)", min_value=0.0, value=start_no3, step=1.0)
eingabe_nh4 = st.sidebar.number_input("Ammonium (NH4 in mg/l)", min_value=0.0, value=start_nh4, step=0.1)
eingabe_ph = st.sidebar.number_input("pH-Wert (3.0 - 10.0)", min_value=3.0, max_value=10.0, value=start_ph, step=0.1)
eingabe_kh = st.sidebar.number_input("Karbonathärte (KH)", min_value=0.0, value=start_kh, step=0.5)
eingabe_gh = st.sidebar.number_input("Gesamthärte (GH)", min_value=0.0, value=start_gh, step=0.5)

berechneter_co2 = berechne_co2(eingabe_ph, eingabe_kh)
st.sidebar.info(f"💡 Automatisch berechneter CO2-Wert: **{berechneter_co2} mg/l**")

if st.sidebar.button("Werte speichern"):
    neue_daten = pd.DataFrame([{"Datum": pd.to_datetime(eingabe_datum), "Aquarium": eingabe_aquarium, "pH (3-10)": eingabe_ph, "Nitrit (NO2)": round(eingabe_no2, 2), "Nitrat (NO3)": eingabe_no3, "Ammonium (NH4)": eingabe_nh4, "KH": eingabe_kh, "GH": eingabe_gh, "CO2": berechneter_co2}])
    df = pd.concat([df, neue_daten], ignore_index=True).sort_values(by="Datum")
    
    save_df = df.copy()
    save_df.rename(columns={"pH (3-10)": "pH", "Nitrit (NO2)": "Nitrit", "Nitrat (NO3)": "Nitrat", "Ammonium (NH4)": "Ammonium"}, inplace=True)
    save_df.to_csv(DATA_FILE, index=False)
    
    st.sidebar.success("Werte erfolgreich gespeichert!")
    st.rerun()

# --- HAUPTBEREICH ---
if df.empty:
    # OPTION ZUM DIRECT-UPLOAD WENN DIE APP NOCH LEER IST
    st.info("👋 Willkommen! Noch keine Daten vorhanden. Trage links manuell Werte ein oder lade direkt hier deine Excel-Datensicherung hoch, um zu starten:")
    
    st.markdown("### 📤 Excel-Sicherung direkt importieren")
    leerer_upload = st.file_uploader("Wähle deine Excel-Datei (.xlsx)", type=["xlsx"], key="empty_uploader")
    if leerer_upload is not None:
        if st.button("📤 Excel-Datei jetzt einlesen und App starten"):
            all_imported = verarbeite_excel_import(leerer_upload)
            if all_imported is not None and not all_imported.empty:
                erfasste_aquarien = [str(aq).strip() for aq in all_imported["Aquarium"].dropna().unique() if str(aq).strip()]
                neue_aquarien = [aq for aq in erfasste_aquarien if aq not in aquarien_optionen]
                
                if neue_aquarien:
                    zeige_import_dialog(neue_aquarien, all_imported)
                else:
                    df = all_imported.sort_values(by="Datum")
                    save_df = df.copy()
                    save_df.rename(columns={"pH (3-10)": "pH", "Nitrit (NO2)": "Nitrit", "Nitrat (NO3)": "Nitrat", "Ammonium (NH4)": "Ammonium"}, inplace=True)
                    save_df.to_csv(DATA_FILE, index=False)
                    st.success("Daten erfolgreich importiert! Die App lädt neu...")
                    st.rerun()
            else:
                st.error("Die Excel-Datei enthielt keine lesbaren Daten oder Spaltennamen.")
else:
    # GRAPHEN-ANZEIGE WENN DATEN VORHANDEN SIND
    modus = st.radio("Ansichtsmodus:", ["Einzelansicht", "Direkter Vergleich (Alle Aquarien)"], horizontal=True)
    
    parameter_liste = ["pH (3-10)", "KH", "Nitrit (NO2)", "Nitrat (NO3)", "CO2", "Ammonium (NH4)", "GH"]
    ausgewaehlte_parameter = st.multiselect("Welche Werte möchtest du im Graphen sehen?", options=parameter_liste, default=["pH (3-10)"])

    df_aktiv = df[df["Aquarium"].isin(aquarien_optionen)].copy()

    if not ausgewaehlte_parameter:
        st.warning("Bitte wähle mindestens einen Wert aus.")
    else:
        if modus == "Einzelansicht":
            aquarium_auswahl = st.selectbox("Wähle das Aquarium für die Detailansicht:", aquarien_optionen)
            df_gefiltert = df_aktiv[df_aktiv["Aquarium"] == aquarium_auswahl]
            if df_gefiltert.empty:
                st.warning(f"Noch keine Daten für {aquarium_auswahl} eingetragen.")
            else:
                df_melted_single = df_gefiltert.melt(id_vars=["Datum"], value_vars=ausgewaehlte_parameter, var_name="Parameter", value_name="Wert")
                fig = px.line(df_melted_single, x="Datum", y="Wert", color="Parameter", title=f"Verlauf für {aquarium_auswahl}", markers=True, color_discrete_map=FARB_MAP)
                st.plotly_chart(fig, use_container_width=True)
        else:
            if df_aktiv.empty:
                st.warning("Keine Daten vorhanden.")
            else:
                df_melted = df_aktiv.melt(id_vars=["Datum", "Aquarium"], value_vars=ausgewaehlte_parameter, var_name="Parameter", value_name="Wert").sort_values(by="Datum")
                fig = px.line(df_melted, x="Datum", y="Wert", color="Parameter", line_dash="Aquarium", title="Vergleich", markers=True, color_discrete_map=FARB_MAP, line_dash_sequence=LINIEN_STILE)
                st.plotly_chart(fig, use_container_width=True)

    # --- TABELLE ---
    st.markdown("---")
    st.subheader("📊 Datentabelle (Direkt bearbeitbar)")
    t_col1, t_col2 = st.columns(2)
    with t_col1: tabellen_filter = st.selectbox("Tabelle filtern nach:", ["Alle Aquarien"] + aquarien_optionen)
    with t_col2: tabellen_sortierung = st.selectbox("Sortieren nach:", ["Datum (Neueste zuerst)", "Datum (Älteste zuerst)", "Aquarium (A-Z)"])

    df_anzeige = df_aktiv.copy()
    if tabellen_filter != "Alle Aquarien": df_anzeige = df_anzeige[df_anzeige["Aquarium"] == tabellen_filter]

    if tabellen_sortierung == "Datum (Neueste zuerst)": df_anzeige = df_anzeige.sort_values(by="Datum", ascending=False)
    elif tabellen_sortierung == "Datum (Älteste zuerst)": df_anzeige = df_anzeige.sort_values(by="Datum", ascending=True)
    else: df_anzeige = df_anzeige.sort_values(by=["Aquarium", "Datum"])

    df_anzeige['Datum'] = df_anzeige['Datum'].dt.date

    edited_df = st.data_editor(df_anzeige, num_rows="dynamic", use_container_width=True, column_config={
        "Datum": st.column_config.DateColumn("Datum", required=True),
        "Aquarium": st.column_config.SelectboxColumn("Aquarium", options=aquarien_optionen, required=True),
        "pH (3-10)": st.column_config.NumberColumn("pH (3-10)", min_value=3.0, max_value=10.0, format="%.2f"),
        "Nitrit (NO2)": st.column_config.NumberColumn("Nitrit (NO2)", format="%.2f"),
        "CO2": st.column_config.NumberColumn("CO2 (Berechnet)", disabled=True)
    })

    if st.button("💾 Änderungen in Tabelle speichern"):
        edited_df['Datum'] = pd.to_datetime(edited_df['Datum'])
        for idx, row in edited_df.iterrows():
            edited_df.at[idx, "CO2"] = berechne_co2(row["pH (3-10)"], row["KH"])
            if "Nitrit (NO2)" in edited_df.columns: edited_df.at[idx, "Nitrit (NO2)"] = round(row["Nitrit (NO2)"], 2)
        df_final = pd.concat([df[df["Aquarium"] != tabellen_filter], edited_df], ignore_index=True) if tabellen_filter != "Alle Aquarien" else edited_df
        df_final = df_final.sort_values(by="Datum")
        
        save_df = df_final.copy()
        save_df.rename(columns={"pH (3-10)": "pH", "Nitrit (NO2)": "Nitrit", "Nitrat (NO3)": "Nitrat", "Ammonium (NH4)": "Ammonium"}, inplace=True)
        save_df.to_csv(DATA_FILE, index=False)
        
        st.success("Änderungen gespeichert!")
        st.rerun()

    # --- EXPORT & IMPORT ---
    st.markdown("---")
    st.subheader("📂 Datensicherung & Excel-Schnittstelle")
    col_exp, col_imp = st.columns(2)
    
    with col_exp:
        st.markdown(f"**Vorschau-Daten exportieren** ({tabellen_filter})")
        df_excel = df_anzeige.copy()
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            if tabellen_filter == "Alle Aquarien":
                for aq in aquarien_optionen:
                    df_aq = df_excel[df_excel["Aquarium"] == aq]
                    if not df_aq.empty: df_aq.to_excel(writer, sheet_name=aq[:31], index=False)
                df_excel.to_excel(writer, sheet_name="Alle Daten", index=False)
            else:
                df_excel.to_excel(writer, sheet_name=str(tabellen_filter)[:31], index=False)
        st.download_button(label="📥 Als Excel-Datei (.xlsx) herunterladen", data=buffer.getvalue(), file_name=f"Wasserwerte_{tabellen_filter.replace(' ', '_')}_{date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with col_imp:
        st.markdown("**Daten aus Excel importieren**")
        uploaded_file = st.file_uploader("Excel-Datei (.xlsx) wählen", type=["xlsx"], label_visibility="collapsed")
        
        if uploaded_file is not None:
            if st.button("📤 Excel-Datei jetzt einlesen"):
                all_imported = verarbeite_excel_import(uploaded_file)
                if all_imported is not None and not all_imported.empty:
                    erfasste_aquarien = [str(aq).strip() for aq in all_imported["Aquarium"].dropna().unique() if str(aq).strip()]
                    neue_aquarien = [aq for aq in erfasste_aquarien if aq not in aquarien_optionen]
                    
                    if neue_aquarien:
                        zeige_import_dialog(neue_aquarien, all_imported)
                    else:
                        final_df = pd.concat([df, all_imported], ignore_index=True)
                        final_df = final_df.drop_duplicates(subset=["Datum", "Aquarium"], keep="last").sort_values(by="Datum")
                        
                        save_df = final_df.copy()
                        save_df.rename(columns={"pH (3-10)": "pH", "Nitrit (NO2)": "Nitrit", "Nitrat (NO3)": "Nitrat", "Ammonium (NH4)": "Ammonium"}, inplace=True)
                        save_df.to_csv(DATA_FILE, index=False)
                        
                        st.success("Excel-Import erfolgreich durchgeführt!")
                        st.rerun()
                else:
                    st.error("Die Excel-Datei enthielt keine lesbaren Daten.")

# --- VERWALTUNGSBEREICH GANZ UNTEN ---
st.markdown("---")
st.subheader("🛠️ Aquarien verwalten")

col_neu, col_edit, col_del = st.columns(3)

with col_neu:
    st.markdown("**Neues Aquarium hinzufügen**")
    neues_aq_name = st.text_input("Name des neuen Aquariums", placeholder="z.B. Nano Cube 30L")
    if st.button("➕ Hinzufügen"):
        if neues_aq_name.strip() and neues_aq_name.strip() not in aquarien_optionen:
            aquarien_optionen.append(neues_aq_name.strip())
            speichere_aquarien(aquarien_optionen)
            st.success(f"'{neues_aq_name.strip()}' wurde hinzugefügt!")
            st.rerun()

with col_edit:
    st.markdown("**Bestehendes Aquarium umbenennen**")
    zu_aendern = st.selectbox("Welches Becken umbenennen?", aquarien_optionen)
    neuer_name = st.text_input("Neuer Name", value=zu_aendern)
    if st.button("📝 Umbenennen bestätigen"):
        if neuer_name.strip() and neuer_name.strip() != zu_aendern:
            neue_liste = [neuer_name.strip() if name == zu_aendern else name for name in aquarien_optionen]
            speichere_aquarien(neue_liste)
            if not df.empty:
                df["Aquarium"] = df["Aquarium"].replace(zu_aendern, neuer_name.strip())
                
                save_df = df.copy()
                save_df.rename(columns={"pH (3-10)": "pH", "Nitrit (NO2)": "Nitrit", "Nitrat (NO3)": "Nitrat", "Ammonium (NH4)": "Ammonium"}, inplace=True)
                save_df.to_csv(DATA_FILE, index=False)
                
            st.success(f"Geändert in '{neuer_name.strip()}'!")
            st.rerun()

with col_del:
    st.markdown("**Aquarium löschen**")
    zu_loeschen = st.selectbox("Welches Becken entfernen?", aquarien_optionen, key="del_select")
    sicherheit = st.checkbox("Ja, aus der Auswahlliste entfernen.")
    if st.button("❌ Aquarium entfernen"):
        if sicherheit and len(aquarien_optionen) > 1:
            aquarien_optionen.remove(zu_loeschen)
            speichere_aquarien(aquarien_optionen)
            st.success(f"'{zu_loeschen}' entfernt!")
            st.rerun()