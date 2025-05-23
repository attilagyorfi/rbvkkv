import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker 
import seaborn as sns
from io import BytesIO # Bár PDF export nincs, a diagramokhoz még kellhet BytesIO, ha pl. képként akarnánk menteni (de most nem használjuk)
from utils import (
    get_status_box_style,
    get_vrio_table_data,
    highlight_vrio_cells,
    get_factor_explanation_box_style
)

# --- Konfigurációk és beállítások ---
st.set_page_config(
    layout="wide",
    page_title="RBV Kkv Indikátor", # Program neve a böngésző fülön
    page_icon="📊"                 # Logó (favicon) a böngésző fülön
)

# Roboto betűtípus és egyéb CSS (beleértve a selectbox hover kurzor kísérletet)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
        html, body, [class*="st-"], [class*="css-"]  {
            font-family: 'Roboto', sans-serif;
        }
        .stDataFrame th { 
            font-weight: bold;
            background-color: #f0f2f6;
            text-align: left;
        }
        /* Selectbox hover kurzor próbálkozás */
        div[data-baseweb="select"] > div:first-child {
            cursor: default !important; 
        }
        div[data-testid="stSelectbox"] > div > div[aria-expanded] {
            cursor: default !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title("A Kkv-k Nemzetköziesedési Szimulátora az RBV Elmélet Alapján")

# --- Tényezők definíciói és magyarázatok ---
factor_definitions = {
    "Innovációs képesség": {
        1: "Nagyon alacsony: Nincs kapacitás új termékek/szolgáltatások fejlesztésére.", 2: "Alacsony: Kisebb, alkalmi fejlesztésekre képes.",
        3: "Közepes: Folyamatosan fejleszti termékeit, de nincs piaci áttörés.", 4: "Magas: Képes innovatív megoldásokat fejleszteni, ami versenyelőnyt ad.",
        5: "Kiemelkedő: Piacvezető innovációk, gyakori áttörések."
    },
    "Humántőke és szakértelem": {
        1: "Nagyon alacsony: Hiányzik a nemzetközi tapasztalat és nyelvtudás.", 2: "Alacsony: Korlátozott számú, nemzetközi tapasztalattal rendelkező munkatárs.",
        3: "Közepes: Képzett munkaerő, alapvető nyelvtudás, de hiányzik a mélyebb szakértelem.", 4: "Magas: Magasan képzett, nyelvtudó csapat, nemzetközi tapasztalattal.",
        5: "Kiemelkedő: Kiemelkedő szakértelemmel és globális hálózattal rendelkező menedzsment."
    },
    "Pénzügyi stabilitás": {
        1: "Nagyon alacsony: Instabil pénzügyi helyzet, forráshiányos.", 2: "Alacsony: Nehezen jut finanszírozáshoz, korlátozott befektetési képesség.",
        3: "Közepes: Stabil pénzügyi háttér, de nagyobb beruházásokhoz külső forrás kell.", 4: "Magas: Kedvező finanszírozási feltételek, képes nagyobb külpiaci beruházásokra.",
        5: "Kiemelkedő: Kiváló pénzügyi helyzet, jelentős saját források, könnyű forrásbevonás."
    },
    "Kapcsolati háló és partneri együttműködések": {
        1: "Nagyon alacsony: Nincs nemzetközi kapcsolati háló.", 2: "Alacsony: Korlátozott, alkalmi külföldi kapcsolatok.",
        3: "Közepes: Alapvető nemzetközi kapcsolatok, de stratégiai partnerek hiánya.", 4: "Magas: Erős nemzetközi kapcsolati háló, stabil partneri együttműködések.",
        5: "Kiemelkedő: Széleskörű globális hálózat, aktív stratégiai szövetségek."
    },
    "Technológiai fejlettség": {
        1: "Nagyon alacsony: Elavult technológia, digitális eszközök hiánya.", 2: "Alacsony: Alapvető digitális eszközök, de nem integrált rendszerek.",
        3: "Közepes: Modern technológia, de nem élenjáró, digitális folyamatok részben automatizáltak.", 4: "Magas: Aktívan alkalmaz digitális megoldásokat, e-kereskedelmi csatornák.",
        5: "Kiemelkedő: Piacvezető technológia, teljes digitális transzformáció, AI/automatizálás."
    },
    "Korlátozott pénzügyi források (Gátló)": {
        1: "Nagyon alacsony akadály: Nincs jelentős korlát, könnyen finanszírozható a terjeszkedés.", 2: "Alacsony akadály: Kisebb finanszírozási kihívások, de megoldhatók.",
        3: "Közepes akadály: Jelentős, de kezelhető pénzügyi korlátok.", 4: "Magas akadály: Nehézkes a finanszírozás, lassítja a terjeszkedést.",
        5: "Kiemelkedő akadály: Krónikus forráshiány, meggátolja a külpiacra lépést."
    },
    "Piaci ismeretek hiánya (Gátló)": {
        1: "Nagyon alacsony akadály: Mélyreható piacismeretek a célországokról.", 2: "Alacsony akadály: Alapvető piacismeret, kisebb hiányosságokkal.",
        3: "Közepes akadály: Hiányos piacismeretek, de piackutatással pótolható.", 4: "Magas akadály: Jelentős piaci ismerethiány, nagy kockázat.",
        5: "Kiemelkedő akadály: Teljes piaci ismerethiány, sikertelen piacra lépés."
    },
    "Hiányos digitális kompetenciák (Gátló)": {
        1: "Nagyon alacsony akadály: Kiváló digitális kompetenciák, online jelenlét.", 2: "Alacsony akadály: Alapvető digitális tudás, de van hova fejlődni.",
        3: "Közepes akadály: Részben fejlett digitális kompetenciák, de elmaradás a versenytársaktól.", 4: "Magas akadály: Hiányos digitális eszközök, marketingstratégiák.",
        5: "Kiemelkedő akadály: Teljes digitális lemaradás, online jelenlét hiánya."
    },
    "Vezetési és stratégiai hiányosságok (Gátló)": {
        1: "Nagyon alacsony akadály: Erős, rugalmas menedzsment, jól meghatározott stratégia.", 2: "Alacsony akadály: Kompetens vezetés, kisebb stratégiai finomításra szorul.",
        3: "Közepes akadály: Alapvető stratégiai tervezés, de hiányzik a nemzetközi fókusz.", 4: "Magas akadály: Rossz vezetési döntések, rugalmatlan stratégia a külpiacokon.",
        5: "Kiemelkedő akadály: Nincs nemzetközi stratégia, rossz kockázatkezelés."
    }
}

# Session state inicializálása
if 'selected_factors' not in st.session_state:
    st.session_state.selected_factors = {factor_name: 3 for factor_name in factor_definitions.keys()}
if 'current_page' not in st.session_state: 
    st.session_state.current_page = "Kkv Jellemzők Beállítása"

# Oldalsáv navigáció
st.sidebar.header("Navigáció")
page_options = ["Kkv Jellemzők Beállítása", "Főoldal (Kkv Profil)", "Nemzetköziesedési Potenciál", "VRIO Elemzés", "Beszámoló", "Gyakorlati Javaslatok"]

try:
    current_page_index = page_options.index(st.session_state.current_page)
except ValueError:
    current_page_index = 0 
    st.session_state.current_page = page_options[0] 

selected_page_from_radio = st.sidebar.radio(
    "Válasszon aloldalt:",
    page_options,
    index=current_page_index, 
    key="navigation_radio"
)

if selected_page_from_radio != st.session_state.current_page:
    st.session_state.current_page = selected_page_from_radio
    st.rerun() 

st.sidebar.markdown("---") 
st.sidebar.caption("Készítette: Győrfi Attila")

page = st.session_state.current_page

# --- Kkv jellemzők értékeinek kiolvasása ---
innovacio = st.session_state.selected_factors.get("Innovációs képesség", 3)
humantoke = st.session_state.selected_factors.get("Humántőke és szakértelem", 3)
penzugyi_stabilitas = st.session_state.selected_factors.get("Pénzügyi stabilitás", 3)
kapcsolati_halo = st.session_state.selected_factors.get("Kapcsolati háló és partneri együttműködések", 3)
technologiai_fejlettseg = st.session_state.selected_factors.get("Technológiai fejlettség", 3)
korlatozott_penzugyi_forrasok = st.session_state.selected_factors.get("Korlátozott pénzügyi források (Gátló)", 3)
piaci_ismeretek_hianya = st.session_state.selected_factors.get("Piaci ismeretek hiánya (Gátló)", 3)
hianyos_digitalis_kompetenciak = st.session_state.selected_factors.get("Hiányos digitális kompetenciák (Gátló)", 3)
vezetesi_strategiai_hianyossagok = st.session_state.selected_factors.get("Vezetési és stratégiai hiányosságok (Gátló)", 3)

# --- Számítási logika ---
s_innovacio = (innovacio - 1) / 4; s_humantoke = (humantoke - 1) / 4; s_penzugyi_stabilitas = (penzugyi_stabilitas - 1) / 4
s_kapcsolati_halo = (kapcsolati_halo - 1) / 4; s_technologiai_fejlettseg = (technologiai_fejlettseg - 1) / 4
s_korlatozott_penzugyi_forrasok = 1 - (korlatozott_penzugyi_forrasok - 1) / 4
s_piaci_ismeretek_hianya = 1 - (piaci_ismeretek_hianya - 1) / 4
s_hianyos_digitalis_kompetenciak = 1 - (hianyos_digitalis_kompetenciak - 1) / 4
s_vezetesi_strategiai_hianyossagok = 1 - (vezetesi_strategiai_hianyossagok - 1) / 4
avg_support = (s_innovacio + s_humantoke + s_penzugyi_stabilitas + s_kapcsolati_halo + s_technologiai_fejlettseg) / 5
avg_barrier_negated = (s_korlatozott_penzugyi_forrasok + s_piaci_ismeretek_hianya + s_hianyos_digitalis_kompetenciak + s_vezetesi_strategiai_hianyossagok) / 4
nemzetkoziesedesi_potencial_num = (avg_support * 0.6 + avg_barrier_negated * 0.4) * 100
nemzetkoziesedesi_potencial_num = max(0, min(100, nemzetkoziesedesi_potencial_num))

# --- Stílusfüggvények a profil táblázathoz (Főoldal) ---
def get_rating_style_main_profile(value):
    color = "black"; background_color = 'transparent'
    if value == 1: background_color = '#f8d7da'; color = '#721c24'
    elif value == 2: background_color = '#f5c6cb'; color = '#721c24'
    elif value == 3: background_color = '#fff3cd'; color = '#856404'
    elif value == 4: background_color = '#d4edda'; color = '#155724'
    elif value == 5: background_color = '#c3e6cb'; color = '#155724'
    return f'background-color: {background_color}; color: {color}; font-weight: bold;'
def get_description_style_main_profile(rating_value):
    if rating_value == 1: color = '#721c24'
    elif rating_value == 2: color = '#721c24'
    elif rating_value == 3: color = '#856404'
    elif rating_value == 4: color = '#155724'
    elif rating_value == 5: color = '#155724'
    else: color = 'black'
    return f'color: {color};'
def style_main_profile_row_cells(row):
    factor_style = 'text-align: left; font-weight: bold; border: 1px solid #ddd; padding: 8px; vertical-align: top;'
    rating_value = row['Értékelés (1-5)']
    rating_cell_color_props = get_rating_style_main_profile(rating_value)
    rating_cell_style = f'{rating_cell_color_props} text-align: center; border: 1px solid #ddd; padding: 8px; vertical-align: top;'
    desc_cell_color_props = get_description_style_main_profile(rating_value)
    desc_cell_style = f'{desc_cell_color_props} text-align: left; border: 1px solid #ddd; padding: 8px; vertical-align: top; word-break: break-word; white-space: normal;'
    return [factor_style, rating_cell_style, desc_cell_style]

# --- Oldalak megjelenítése ---
if page == "Kkv Jellemzők Beállítása":
    st.header("Kkv Jellemzők Beállítása")
    st.write("Minden tényezőt értékeljen 1-től 5-ig terjedő skálán. Az értékeléséhez tartozó részletes magyarázat a kiválasztás után jelenik meg.")
    st.markdown("---")
    cols = st.columns(2); factor_keys = list(factor_definitions.keys()); num_factors = len(factor_keys); mid_point = (num_factors + 1) // 2
    for i, factor_name in enumerate(factor_keys):
        current_col = cols[0] if i < mid_point else cols[1]
        with current_col:
            st.markdown(f"##### {factor_name}")
            current_value_from_session = st.session_state.selected_factors.get(factor_name, 3)
            selected_value = st.selectbox(label=f"Értékelés_{factor_name}", options=[1, 2, 3, 4, 5], index=current_value_from_session - 1, 
                                          key=f"sb_factor_{factor_name.replace(' ', '_').replace('(', '').replace(')', '')}", label_visibility="collapsed")
            st.session_state.selected_factors[factor_name] = selected_value 
            full_description = factor_definitions[factor_name][selected_value]; level_desc, detail_desc = full_description.split(': ', 1)
            is_barrier_factor = "(Gátló)" in factor_name
            box_style_css = get_factor_explanation_box_style(selected_value, is_barrier_factor) 
            explanation_html = f"<div style='{box_style_css}'><strong>{level_desc} ({selected_value}):</strong> {detail_desc}</div>"
            st.markdown(explanation_html, unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("A beállítások összefoglaló diagramja:")
    try:
        df_summary_display = pd.DataFrame(st.session_state.selected_factors.items(), columns=['Tényező', 'Értékelés'])
        fig_summary_display, ax_summary_display = plt.subplots(figsize=(10, 6)) 
        colors_summary_display = []
        for index, row_disp in df_summary_display.iterrows():
            score_disp = row_disp['Értékelés']; is_barrier_disp = "(Gátló)" in row_disp['Tényező']
            color_to_append_disp = '#ffc107'
            if is_barrier_disp:
                if score_disp <= 2: color_to_append_disp = '#28a745' 
                elif score_disp >= 4: color_to_append_disp = '#dc3545'
            else:
                if score_disp <= 2: color_to_append_disp = '#dc3545'
                elif score_disp >= 4: color_to_append_disp = '#28a745'
            colors_summary_display.append(color_to_append_disp)
        sns.barplot(x='Értékelés', y='Tényező', data=df_summary_display, palette=colors_summary_display, ax=ax_summary_display, orient='h')
        ax_summary_display.set_xlabel("Értékelés (1-5)"); ax_summary_display.set_ylabel("Tényező"); ax_summary_display.set_title("Kkv Jellemzők Jelenlegi Értékelései")
        ax_summary_display.set_xlim(0, 5.5); ax_summary_display.xaxis.set_major_locator(mticker.MultipleLocator(1))
        for i_disp, v_disp in enumerate(df_summary_display['Értékelés']): ax_summary_display.text(v_disp + 0.1, i_disp, str(v_disp), color='black', va='center', fontweight='bold')
        plt.tight_layout(); st.pyplot(fig_summary_display); plt.close(fig_summary_display)
    except Exception as e_diag: st.error(f"Hiba az összefoglaló diagram megjelenítése közben: {e_diag}")
    st.markdown("---")

elif page == "Főoldal (Kkv Profil)":
    st.header("Kkv Profil Összefoglaló")
    st.write("Az alábbiakban táblázatos formában láthatja a jelenleg beállított kkv jellemzőket.")
    profile_data = []
    for factor_name_key in factor_definitions.keys():
        value = st.session_state.selected_factors[factor_name_key]; description = factor_definitions[factor_name_key][value]
        profile_data.append({"Tényező": factor_name_key, "Értékelés (1-5)": value, "Rövid Leírás": description.split(': ', 1)[1]})
    df_profile = pd.DataFrame(profile_data)
    styled_profile_styler = df_profile.style.apply(style_main_profile_row_cells, axis=1).hide(axis="index")
    st.dataframe(styled_profile_styler, use_container_width=True, column_config={
        "Tényező": st.column_config.TextColumn("Tényező", width="medium"), "Értékelés (1-5)": st.column_config.TextColumn("Értékelés", width="small"),
        "Rövid Leírás": st.column_config.TextColumn("Leírás", width="large")})
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Részletes Beszámoló Megtekintése", key="show_report_btn"):
        st.session_state.current_page = "Beszámoló" 
        st.rerun() 

elif page == "Nemzetköziesedési Potenciál":
    st.header("Nemzetköziesedési Potenciál")
    col1, col2 = st.columns([0.6, 0.4]) 
    with col1: st.metric(label="Aktuális Nemzetköziesedési Potenciál", value=f"{nemzetkoziesedesi_potencial_num:.1f} %")
    with col2:
        labels_pie = 'Elért', 'Hátralévő'; sizes_pie = [nemzetkoziesedesi_potencial_num, 100 - nemzetkoziesedesi_potencial_num]
        explode_pie = (0.05, 0) if 0 < nemzetkoziesedesi_potencial_num < 100 else (0,0)
        color_reached = '#D3D3D3'; 
        if nemzetkoziesedesi_potencial_num < 40: color_reached = '#dc3545' 
        elif nemzetkoziesedesi_potencial_num < 70: color_reached = '#ffc107' 
        else: color_reached = '#28a745' 
        fig_pie, ax_pie = plt.subplots(figsize=(2.5, 2.5)); ax_pie.pie(sizes_pie, explode=explode_pie, labels=None, autopct=None, startangle=90, colors=[color_reached, '#E9E9E9'], wedgeprops = {"edgecolor":"white", 'linewidth': 0.5, 'antialiased': True}); ax_pie.axis('equal')
        centre_circle = plt.Circle((0,0),0.75,fc='white'); fig_pie.gca().add_artist(centre_circle)
        ax_pie.text(0, 0, f"{nemzetkoziesedesi_potencial_num:.0f}%", ha='center', va='center', fontsize=16, fontweight='bold', color=color_reached)
        st.pyplot(fig_pie, use_container_width=False); plt.close(fig_pie)
    st.write("---"); st.subheader("Tényezők Hozzájárulása (Súlyozott Elemzés)")
    factors_for_viz = pd.DataFrame({'Tényező': ['Innováció', 'Humántőke', 'Pénzügyi stab.', 'Kapcs. háló', 'Tech. fejlettség', 'Pénzügyi korl.', 'Piaci ism. hiánya', 'Digit. komp. hiánya', 'Strat. hiány.'],
        'Hatás Pont': [s_innovacio * 10, s_humantoke * 10, s_penzugyi_stabilitas * 10, s_kapcsolati_halo * 10, s_technologiai_fejlettseg * 10, (1 - s_korlatozott_penzugyi_forrasok) * -10, (1 - s_piaci_ismeretek_hianya) * -10, (1 - s_hianyos_digitalis_kompetenciak) * -10, (1 - s_vezetesi_strategiai_hianyossagok) * -10]})
    colors_potential = ['#28a745' if x >= 0 else '#dc3545' for x in factors_for_viz['Hatás Pont']] 
    fig_pot, ax_pot = plt.subplots(figsize=(10, 4)) 
    sns.barplot(x='Hatás Pont', y='Tényező', data=factors_for_viz, palette=colors_potential, ax=ax_pot)
    ax_pot.set_title('Az egyes tényezők hatása a nemzetköziesedési potenciálra', fontsize=14); ax_pot.set_xlabel('Hatás Pontszám', fontsize=10); ax_pot.set_ylabel('Tényező', fontsize=10)
    ax_pot.set_xlim(-10.5, 10.5); ax_pot.tick_params(axis='x', labelsize=8); ax_pot.tick_params(axis='y', labelsize=8); plt.tight_layout(); st.pyplot(fig_pot); plt.close(fig_pot)

elif page == "VRIO Elemzés":
    st.header("VRIO-modell elemzés"); st.info("A VRIO-modell (Valuable, Rare, Inimitable, Organized) alapján értékeljük az erőforrásait. A '✓' jelöli, ha az erőforrás megfelel a kritériumnak, '✗' pedig ha nem.")
    vrio_data_bool = get_vrio_table_data(innovacio, humantoke, penzugyi_stabilitas, kapcsolati_halo, technologiai_fejlettseg)
    df_vrio = pd.DataFrame(vrio_data_bool, columns=['Erőforrás', 'Értékes', 'Ritka', 'Utánozhatatlan', 'Szervezett'])
    styled_df_vrio_styler = df_vrio.style.applymap(highlight_vrio_cells, subset=['Értékes', 'Ritka', 'Utánozhatatlan', 'Szervezett']).set_properties(**{'text-align': 'center', 'font-weight': 'bold'}, subset=['Értékes', 'Ritka', 'Utánozhatatlan', 'Szervezett']).set_properties(**{'text-align': 'left', 'font-weight': 'bold'}, subset=['Erőforrás']).hide(axis="index")
    formatter_vrio = {col: (lambda x: "✓" if x else "✗") for col in ['Értékes', 'Ritka', 'Utánozhatatlan', 'Szervezett']}
    st.dataframe(styled_df_vrio_styler.format(formatter_vrio), use_container_width=True, column_config={"Erőforrás": st.column_config.TextColumn(width="large"), "Értékes": st.column_config.TextColumn(width="small"), "Ritka": st.column_config.TextColumn(width="small"), "Utánozhatatlan": st.column_config.TextColumn(width="small"), "Szervezett": st.column_config.TextColumn(width="small")})
    st.markdown("<br>", unsafe_allow_html=True)

elif page == "Beszámoló":
    st.header("Részletes Eredmény Beszámoló"); st.markdown("---")
    st.write("Ez az oldal összefoglalja és értelmezi a nemzetköziesedési szimulátorban beállított értékek és a számított potenciál alapján levonható főbb következtetéseket.")
    
    st.subheader("1. Nemzetköziesedési Potenciál Értékelése")
    col_report1, col_report2 = st.columns([0.7, 0.3])
    with col_report1:
        st.metric(label="Kiszámított Nemzetköziesedési Potenciál", value=f"{nemzetkoziesedesi_potencial_num:.1f} %")
        potencial_text = ""
        if nemzetkoziesedesi_potencial_num < 40: potencial_text = "Ez **alacsony** nemzetköziesedési potenciált jelez. Vállalkozásának jelenleg jelentős belső fejlesztésekre és a gátló tényezők csökkentésére van szüksége a sikeres nemzetközi piacra lépéshez. Az alacsony pontszám arra utal, hogy több kulcsfontosságú területen is elmaradás tapasztalható, ami kockázatossá teszi a külpiaci nyitást megfelelő felkészülés nélkül."
        elif nemzetkoziesedesi_potencial_num < 70: potencial_text = "Ez **közepes** nemzetköziesedési potenciált mutat. Vállalkozása rendelkezik bizonyos erősségekkel, amelyekre építhet, de vannak még leküzdendő akadályok és fejleszthető területek. A nemzetközi sikeresség érdekében érdemes a gyengeségekre koncentrálni és a meglévő előnyöket tudatosan kiaknázni, mielőtt nagyobb léptékű nemzetközi terjeszkedésbe kezdene."
        else: potencial_text = "Ez **magas** nemzetköziesedési potenciált jelez. Vállalkozása erős alapokkal rendelkezik a nemzetközi terjeszkedéshez, és jó esélyekkel indulhat a külpiacokon. A magas pontszám azt sugallja, hogy a belső erőforrások és a külső környezet kevésbé gátló tényezői együttesen kedvező helyzetet teremtenek a sikeres nemzetközi jelenléthez."
        st.markdown(potencial_text)
    with col_report2: 
        labels_pie_rep = 'Elért', 'Hátralévő'; sizes_pie_rep = [nemzetkoziesedesi_potencial_num, 100 - nemzetkoziesedesi_potencial_num]
        explode_pie_rep = (0.05, 0) if 0 < nemzetkoziesedesi_potencial_num < 100 else (0,0)
        color_reached_rep = '#D3D3D3'; 
        if nemzetkoziesedesi_potencial_num < 40: color_reached_rep = '#dc3545'
        elif nemzetkoziesedesi_potencial_num < 70: color_reached_rep = '#ffc107'
        else: color_reached_rep = '#28a745'
        fig_pie_rep, ax_pie_rep = plt.subplots(figsize=(2.5, 2.5)); ax_pie_rep.pie(sizes_pie_rep, explode=explode_pie_rep, labels=None, autopct=None, startangle=90, colors=[color_reached_rep, '#E9E9E9'], wedgeprops = {"edgecolor":"white", 'linewidth': 0.5, 'antialiased': True}); ax_pie_rep.axis('equal')
        centre_circle_rep = plt.Circle((0,0),0.75,fc='white'); fig_pie_rep.gca().add_artist(centre_circle_rep)
        ax_pie_rep.text(0, 0, f"{nemzetkoziesedesi_potencial_num:.0f}%", ha='center', va='center', fontsize=16, fontweight='bold', color=color_reached_rep)
        st.pyplot(fig_pie_rep, use_container_width=False); plt.close(fig_pie_rep)
    st.markdown("---")

    st.subheader("2. Főbb Tényezők Részletes Elemzése")
    támogató_factors = {k:v for k,v in st.session_state.selected_factors.items() if "(Gátló)" not in k}
    gátló_factors = {k:v for k,v in st.session_state.selected_factors.items() if "(Gátló)" in k}
    
    erős_támogatók = sorted([ (k,v) for k,v in támogató_factors.items() if v >= 4], key=lambda item: item[1], reverse=True)
    if erős_támogatók:
        st.markdown("**Erősségek – Kiemelkedő erőforrások, amelyekre építhet a nemzetközi piacokon:**")
        text_block_strong = "Az elemzés alapján vállalkozása több területen is erős pozíciókkal rendelkezik, amelyek megalapozhatják a nemzetközi sikert. "
        for factor, value in erős_támogatók[:2]: 
            factor_desc_detail = factor_definitions[factor][value].split(': ',1)[1]
            text_block_strong += f"Különösen figyelemre méltó a(z) **{factor.lower()}** ({value}/5), amely azt jelenti, hogy vállalata {factor_desc_detail.lower()} Ez komoly versenyelőnyt biztosíthat a külpiacokon, és érdemes erre a képességre tudatosan építeni a nemzetközi stratégiát. "
        st.markdown(text_block_strong)
    else:
        st.markdown("**Erősségek – Kiemelkedő erőforrások:** Jelenleg nincsenek 4-es vagy 5-ös értékelésű támogató erőforrásai. Ez azt jelzi, hogy bár lehetnek stabilan működő területek, a kiemelkedő, nehezen másolható versenyelőnyök még fejlesztésre szorulnak. Érdemes lenne azonosítani és fejleszteni azokat a belső képességeket, amelyekre a nemzetközi terjeszkedés épülhet, vagy a meglévő közepes erőforrásokat magasabb szintre emelni.")
    st.markdown("<br>", unsafe_allow_html=True)

    gyenge_támogatók = sorted([ (k,v) for k,v in támogató_factors.items() if v <= 2], key=lambda item: item[1])
    if gyenge_támogatók:
        st.markdown("**Fejlesztendő területek – Erőforrások, amelyekre érdemes fókuszálni:**")
        text_block_weak = "Az értékelés rávilágított néhány olyan belső erőforrásra, amelyek további fejlesztést igényelnek a sikeres nemzetköziesedés érdekében, mivel jelenlegi szintjük korlátozhatja a külpiaci érvényesülést. "
        for factor, value in gyenge_támogatók[:2]:
            factor_desc_detail = factor_definitions[factor][value].split(': ',1)[1]
            text_block_weak += f"A(z) **{factor.lower()}** ({value}/5) területén jelentős előrelépésre van szükség, mivel jelenleg vállalata {factor_desc_detail.lower()} Ennek megerősítése kulcsfontosságú lehet a külpiaci versenyképesség javításához és a kockázatok csökkentéséhez. "
        st.markdown(text_block_weak)
    else:
        st.markdown("**Fejlesztendő területek – Erőforrások:** Úgy tűnik, nincsenek kifejezetten alacsony (1-es vagy 2-es) pontszámú támogató erőforrásai, ami pozitív. Azonban a közepes erőforrások további erősítése és a potenciális gyengeségek proaktív kezelése továbbra is fontos lehet a hosszú távú siker érdekében.")
    st.markdown("<br>", unsafe_allow_html=True)

    alacsony_gátlók = sorted([ (k,v) for k,v in gátló_factors.items() if v <= 2], key=lambda item: item[1])
    if alacsony_gátlók:
        st.markdown("**Kedvező külső tényezők – Alacsony szintű akadályok:**")
        text_block_low_barrier = "Bizonyos gátló tényezők esetében vállalkozása kedvező helyzetben van, ami megkönnyítheti a nemzetközi piacra lépést és csökkentheti a kapcsolódó kockázatokat. "
        for factor, value in alacsony_gátlók[:2]:
            factor_desc_detail = factor_definitions[factor][value].split(': ',1)[1]
            clean_factor_name = factor.replace(' (Gátló)','').lower()
            text_block_low_barrier += f"Például a(z) **{clean_factor_name}** ({value}/5) területén alacsony akadályokkal kell szembenéznie, hiszen {factor_desc_detail.lower()} Ezt érdemes kihasználni a stratégiaalkotás során, és fókuszálni azokra a piacokra, ahol ezek a kedvező feltételek érvényesülnek. "
        st.markdown(text_block_low_barrier)
    else:
        st.markdown("**Kedvező külső tényezők – Alacsony szintű akadályok:** Az elemzés nem tárt fel kiemelkedően alacsony (1-es vagy 2-es) pontszámú gátló tényezőket. Ez azt jelenti, hogy több területen is lehetnek kezelendő kihívások, amelyekre fel kell készülni, és proaktívan kell kezelni a potenciális nehézségeket.")
    st.markdown("<br>", unsafe_allow_html=True)

    magas_gátlók = sorted([ (k,v) for k,v in gátló_factors.items() if v >= 4], key=lambda item: item[1], reverse=True)
    if magas_gátlók:
        st.markdown("**Kritikus kihívások – Jelentős akadályok, amelyekre kiemelt figyelmet kell fordítani:**")
        text_block_high_barrier = "Vannak olyan tényezők, amelyek jelenleg komoly akadályt gördíthetnek a nemzetközi terjeszkedés útjába, és amelyek kezelése elengedhetetlen a sikerhez. Ezek figyelmen kívül hagyása jelentős kockázatokat hordozhat. "
        for factor, value in magas_gátlók[:2]:
            factor_desc_detail = factor_definitions[factor][value].split(': ',1)[1]
            clean_factor_name = factor.replace(' (Gátló)','').lower()
            text_block_high_barrier += f"Különösen nagy kihívást jelenthet a(z) **{clean_factor_name}** ({value}/5), mivel {factor_desc_detail.lower()} Ezen akadályok csökkentése vagy kiküszöbölése, illetve a rájuk adott stratégiai válasz prioritást kell, hogy élvezzen a nemzetköziesedési tervek kidolgozása során. "
        st.markdown(text_block_high_barrier)
    else:
        st.markdown("**Kritikus kihívások – Jelentős akadályok:** Az értékelés alapján úgy tűnik, nincsenek kiemelkedően magas (4-es vagy 5-ös) pontszámú gátló tényezői, ami biztató. Ez csökkenti a közvetlen, súlyos kockázatokat, de a közepes szintű akadályokra is figyelmet kell fordítani és stratégiát kell kidolgozni azok hatékony kezelésére.")
    st.markdown("---")

    st.subheader("3. VRIO Elemzés Kulcsfontosságú Megállapításai")
    vrio_data = get_vrio_table_data(innovacio, humantoke, penzugyi_stabilitas, kapcsolati_halo, technologiai_fejlettseg)
    vrio_paragraphs = []
    for row in vrio_data:
        eroforras, v, r, i, o = row
        sentence_parts = []
        if v: sentence_parts.append("értékesnek minősül, mivel hozzájárul a vevői értékteremtéshez vagy a költséghatékonysághoz")
        else: sentence_parts.append("jelenlegi formájában nem feltétlenül tekinthető közvetlenül értékesnek a nemzetközi versenyben, vagy fejlesztésre szorul ezen a téren")
        if r: sentence_parts.append("ritka a piacon, azaz kevés versenytárs rendelkezik hasonlóval")
        else: sentence_parts.append("nem tekinthető ritkának, így mások is hozzáférhetnek vagy rendelkezhetnek vele")
        if i: sentence_parts.append("nehezen másolható vagy helyettesíthető a versenytársak által, ami védelmet nyújthat")
        else: sentence_parts.append("viszonylag könnyen utánozható vagy helyettesíthető lehet, ami csökkenti a belőle származó előnyt")
        if o: sentence_parts.append("és vállalata szervezeti felépítése, folyamatai és kultúrája támogatják annak hatékony kihasználását és a benne rejlő érték maximalizálását")
        else: sentence_parts.append("azonban a szervezeti felkészültség, a belső folyamatok vagy a vállalati kultúra hiányosságai korlátozhatják a benne rejlő potenciál teljes körű kiaknázását, még ha az erőforrás önmagában értékes is lenne")

        vrio_desc = f"A(z) **{eroforras.lower()}** az elemzés alapján {', '.join(sentence_parts)}."

        if v and r and i and o: vrio_desc += " Mindezek alapján ez az erőforrás **tartós versenyelőnyt** biztosíthat Önnek a nemzetközi piacokon, amelyre hosszú távon is építhet stratégiát, mivel nehezen támadható és fenntartható."
        elif v and r and o: vrio_desc += " Ezáltal **ideiglenes versenyelőnyt** jelenthet, amíg a versenytársak nem képesek hasonló erőforrást vagy képességet kiépíteni. Fontos a folyamatos fejlesztés és az előny megőrzésére irányuló törekvés."
        elif v and o: vrio_desc += " Így **versenyparitást** érhet el a piacon, de önmagában ez nem garantál kiemelkedő, megkülönböztetett pozíciót. Más tényezőkkel kombinálva lehet erősebb."
        else: vrio_desc += " Ez a jelenlegi formájában és kiaknázottságában **versenyhátrányt** is jelenthet, vagy kevésbé bír relevanciával a nemzetközi siker szempontjából. Érdemes megfontolni ezen erőforrás fejlesztését vagy alternatívák keresését."
        vrio_paragraphs.append(vrio_desc)
    for par in vrio_paragraphs:
        st.markdown(par)
        st.markdown(" ") 
    st.markdown("---")
    
    st.subheader("4. Összegzés és Javasolt Következő Lépések")
    st.markdown("Ez a szimuláció egy pillanatképet adott vállalkozása nemzetköziesedési felkészültségéről. A kapott eredmények alapján azonosíthatta erősségeit és a fejlesztendő területeket, valamint a potenciális akadályokat.")
    st.markdown("A konkrét, személyre szabott teendőkért és stratégiai javaslatokért kérjük, **tekintse meg a 'Gyakorlati Javaslatok' oldalt**, amely a potenciál pontszáma alapján ad iránymutatást a következő lépésekhez.")
    st.markdown("Ne feledje, a nemzetköziesedés egy folyamatos tanulási és alkalmazkodási folyamat. A piaci környezet és a belső képességek változhatnak, ezért rendszeres önértékelés és stratégiai finomhangolás javasolt. Sok sikert kívánunk!")

elif page == "Gyakorlati Javaslatok":
    st.header("Gyakorlati Javaslatok a Nemzetköziesedéshez")
    box_style = get_status_box_style(nemzetkoziesedesi_potencial_num) 
    message_javaslat = ""; javaslat_reszlet = ""
    javaslat_alacsony_text = "* **Pénzügyi alapok megerősítése:** Vizsgálja meg a kedvezményes hitelkonstrukciókat, pályázati lehetőségeket és kockázati tőkebefektetési opciókat a nemzetköziesedés finanszírozásához. Készítsen részletes pénzügyi tervet a várható költségekről és megtérülésről.\n* **Piaci ismeretek bővítése:** Kezdjen részletes piackutatást a célpiacokról, beleértve a versenytársak, a fogyasztói igények és a jogi-szabályozási környezet elemzését. Fontolja meg helyi tanácsadók vagy piackutató cégek bevonását.\n* **Digitális felkészültség:** Fektessen be modern e-kereskedelmi platformokba, fejlessze online marketing stratégiáját (SEO, közösségi média, tartalommarketing), és biztosítsa a megfelelő digitális infrastruktúrát a nemzetközi vevők kiszolgálásához."
    javaslat_kozepes_text = "* **Innováció ösztönzése:** Folyamatosan fejlessze termékeit és szolgáltatásait a nemzetközi piaci igényeknek megfelelően. Keresse a K+F együttműködéseket, vegyen részt iparági innovációs programokban, és figyelje a globális trendeket.\n* **Humántőke fejlesztése:** Biztosítson képzéseket és nyelvi kurzusokat munkatársainak a nemzetközi üzleti kommunikáció és kulturális érzékenység javítása érdekében. Fontolja meg nemzetközi tapasztalattal rendelkező szakemberek alkalmazását vagy menedzsmenti tudásimportot.\n* **Kapcsolati háló bővítése:** Vegyen részt aktívan nemzetközi üzleti fórumokon, szakmai kiállításokon és vásárokon. Csatlakozzon nemzetközi szakmai szervezetekhez és kereskedelmi kamarákhoz a potenciális partnerek és ügyfelek felkutatása érdekében."
    javaslat_magas_text = "* **Stratégiai partnerségek:** Keressen hosszú távú, kölcsönösen előnyös stratégiai szövetségeket és partnerségeket a célpiacokon (pl. disztribútorok, helyi gyártók, közös vállalatok). Ezek segíthetnek a piaci behatolásban és a kockázatok megosztásában.\n* **Folyamatos innováció és adaptáció:** Maradjon a trendek élén, alkalmazza a legújabb technológiákat, és gyűjtsön aktívan vevői visszajelzéseket a termékek és szolgáltatások folyamatos tökéletesítése érdekében. Legyen rugalmas és képes gyorsan alkalmazkodni a változó piaci igényekhez.\n* **Kockázatkezelés és fenntarthatóság:** Fejlessze ki és alkalmazza a nemzetközi kereskedelemmel járó kockázatok (pl. devizaárfolyam-ingadozás, politikai instabilitás, kintlévőségek) kezelésére vonatkozó stratégiákat. Fontolja meg exportbiztosítások és egyéb kockázatcsökkentő eszközök használatát. Ügyeljen a fenntartható üzleti gyakorlatokra is."
    
    if nemzetkoziesedesi_potencial_num < 40:
        message_javaslat = "Alacsony nemzetköziesedési potenciál. Erős fókuszra van szükség a belső erőforrások fejlesztésére!"
        st.markdown(f'<div style="{box_style}">{message_javaslat}</div>', unsafe_allow_html=True); st.markdown(javaslat_alacsony_text)
    elif 40 <= nemzetkoziesedesi_potencial_num < 70:
        message_javaslat = "Közepes nemzetköziesedési potenciál. Vannak erősségei, de a gátló tényezők leküzdése kritikus!"
        st.markdown(f'<div style="{box_style}">{message_javaslat}</div>', unsafe_allow_html=True); st.markdown(javaslat_kozepes_text)
    else: 
        message_javaslat = "Magas nemzetköziesedési potenciál! Fókuszáljon a fenntartható növekedésre és a piacvezető pozíció megszerzésére."
        st.markdown(f'<div style="{box_style}">{message_javaslat}</div>', unsafe_allow_html=True); st.markdown(javaslat_magas_text)

