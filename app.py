import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from io import BytesIO
from utils import (
    get_status_box_style,
    get_vrio_table_data,
    highlight_vrio_cells,
    # get_factor_explanation_box_style # Ezt már nem használjuk
)

# --- Konfigurációk és beállítások ---
st.set_page_config(
    layout="wide",
    page_title="RBV Kkv Indikátor",
    page_icon="📊"
)

# Roboto betűtípus és egyéb CSS
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
    st.session_state.selected_factors = {factor_name: None for factor_name in factor_definitions.keys()}
if 'current_page' not in st.session_state: 
    st.session_state.current_page = "Bevezető" 

# Oldalsáv navigáció
st.sidebar.header("Navigáció")
page_options = ["Bevezető", "Főoldal (Kkv Profil)", "Kkv Jellemzők Beállítása", "Nemzetköziesedési Potenciál", "VRIO Elemzés", "Beszámoló", "Gyakorlati Javaslatok"]

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

# --- Globális ellenőrzés és számítások ---
all_factors_selected = all(value is not None for value in st.session_state.selected_factors.values())
nemzetkoziesedesi_potencial_num = 0.0
s_innovacio, s_humantoke, s_penzugyi_stabilitas, s_kapcsolati_halo, s_technologiai_fejlettseg = 0,0,0,0,0
s_korlatozott_penzugyi_forrasok, s_piaci_ismeretek_hianya, s_hianyos_digitalis_kompetenciak, s_vezetesi_strategiai_hianyossagok = 0,0,0,0
innovacio, humantoke, penzugyi_stabilitas, kapcsolati_halo, technologiai_fejlettseg = (None,) * 5
korlatozott_penzugyi_forrasok, piaci_ismeretek_hianya, hianyos_digitalis_kompetenciak, vezetesi_strategiai_hianyossagok = (None,) * 4


if all_factors_selected:
    innovacio = st.session_state.selected_factors["Innovációs képesség"]
    humantoke = st.session_state.selected_factors["Humántőke és szakértelem"]
    penzugyi_stabilitas = st.session_state.selected_factors["Pénzügyi stabilitás"]
    kapcsolati_halo = st.session_state.selected_factors["Kapcsolati háló és partneri együttműködések"]
    technologiai_fejlettseg = st.session_state.selected_factors["Technológiai fejlettség"]
    korlatozott_penzugyi_forrasok = st.session_state.selected_factors["Korlátozott pénzügyi források (Gátló)"]
    piaci_ismeretek_hianya = st.session_state.selected_factors["Piaci ismeretek hiánya (Gátló)"]
    hianyos_digitalis_kompetenciak = st.session_state.selected_factors["Hiányos digitális kompetenciák (Gátló)"]
    vezetesi_strategiai_hianyossagok = st.session_state.selected_factors["Vezetési és stratégiai hiányosságok (Gátló)"]

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

# --- Stílusfüggvények ---
def get_rating_style_main_profile(value):
    color = "black"; background_color = 'transparent'; font_weight = "normal"
    if pd.notnull(value) and isinstance(value, (int, float)):
        font_weight = "bold"
        if value == 1: background_color = '#f8d7da'; color = '#721c24'
        elif value == 2: background_color = '#f5c6cb'; color = '#721c24'
        elif value == 3: background_color = '#fff3cd'; color = '#856404'
        elif value == 4: background_color = '#d4edda'; color = '#155724'
        elif value == 5: background_color = '#c3e6cb'; color = '#155724'
    return f'background-color: {background_color}; color: {color}; font-weight: {font_weight};'

def get_description_style_main_profile(rating_value):
    color = 'black'
    if pd.notnull(rating_value) and isinstance(rating_value, (int, float)):
        if rating_value == 1: color = '#721c24'
        elif rating_value == 2: color = '#721c24'
        elif rating_value == 3: color = '#856404'
        elif rating_value == 4: color = '#155724'
        elif rating_value == 5: color = '#155724'
    return f'color: {color};'

def style_main_profile_row_cells(row):
    factor_style = 'text-align: left; font-weight: bold; border: 1px solid #ddd; padding: 8px; vertical-align: top;'
    rating_value = row['Értékelés (1-5)'] # Ez lehet None vagy szám
    rating_cell_color_props = get_rating_style_main_profile(rating_value)
    rating_cell_style = f'{rating_cell_color_props} text-align: center; border: 1px solid #ddd; padding: 8px; vertical-align: top;'
    desc_cell_color_props = get_description_style_main_profile(rating_value)
    desc_cell_style = f'{desc_cell_color_props} text-align: left; border: 1px solid #ddd; padding: 8px; vertical-align: top; word-break: break-word; white-space: normal;'
    return [factor_style, rating_cell_style, desc_cell_style]

def get_score_text_style(score_value, is_barrier=False, is_selected=False):
    color = "black" 
    font_weight = "normal"
    if is_selected: # Csak a kiválasztottat színezzük és vastagítjuk
        font_weight = "bold"
        if is_barrier:
            if score_value <= 2: color = "green"
            elif score_value == 3: color = "darkorange" 
            else: color = "red"
        else:
            if score_value <= 2: color = "red"
            elif score_value == 3: color = "darkorange"
            else: color = "green"
    return f"color: {color}; font-weight: {font_weight};"

# --- Oldalak megjelenítése ---
if page == "Bevezető":
    st.header("Bevezető és Módszertan")
    st.markdown("---")
    st.markdown("""
    Kedves Felhasználó!

    Győrfi Attila vagyok és a szakdolgozatom részeként készítettem ezt az interaktív alkalmazást. 
    Célom egy olyan eszköz létrehozása volt, amely segítséget nyújthat a kkv-knak saját nemzetköziesedési felkészültségük felmérésében és a fejlesztendő területek azonosításában.

    ### Tudományos Megalapozottság
    A szimulátor az **Erőforrás-Alapú Elméletre (Resource-Based View - RBV)** épül, amely szerint a vállalati siker és versenyelőny kulcsa a vállalat egyedi, nehezen másolható erőforrásaiban és képességeiben rejlik. A nemzetköziesedés kontextusában ez azt jelenti, hogy azok a kkv-k lehetnek sikeresebbek a külpiacokon, amelyek rendelkeznek a megfelelő belső potenciállal.

    További felhasznált elméleti keretek és koncepciók:
    * **VRIO-modell (Barney, 1991):** Az erőforrások értékelésére (Értékes, Ritka, Utánozhatatlan, Szervezett).
    * A nemzetköziesedés szakaszos modelljei és a "born global" vállalkozások koncepciója.
    * A kkv-k nemzetköziesedését támogató és gátló tényezőkre vonatkozó szakirodalmi kutatások.

    ### Alkalmazott Módszerek
    A szimulátorban a következő módszereket alkalmaztam:
    * **Szakirodalom-kutatás:** A releváns elméletek és modellek, valamint a kkv-k nemzetköziesedési gyakorlatának feltárása.
    * **Kvantitatív értékelési modell:** A szakirodalom alapján azonosított kulcsfontosságú erőforrások és gátló tényezők súlyozott értékelése egy normalizált pontrendszer alapján, amely egy összesített nemzetköziesedési potenciál indexet eredményez.
    * **Kategorizálás:** A potenciál index alapján a kkv-k alacsony, közepes vagy magas potenciállal rendelkező csoportokba sorolása, és ennek megfelelő általános javaslatok megfogalmazása.
    * **Interaktív Adatvizualizáció:** Streamlit keretrendszer használata az eredmények felhasználóbarát megjelenítésére.

    ### A Szimulátor Limitációi
    Fontos kiemelni, hogy ez az eszköz egy **szimulációs és önértékelési segédlet**, és nem helyettesíti a részletes, személyre szabott üzleti tanácsadást vagy a mélyreható piacelemzést.
    * **Szubjektivitás:** Az önértékelésen alapuló bemeneti adatok pontossága befolyásolja az eredményt.
    * **Általánosítás:** A modell és a javaslatok általánosítottak, és nem vesznek figyelembe minden iparág-specifikus vagy egyedi vállalati körülményt.
    * **Dinamizmus hiánya:** A modell egy adott időpontban értékeli a helyzetet, nem követi dinamikusan a vállalati és piaci változásokat.
    * **Nem teljes körű:** Bár igyekeztem a legfontosabb tényezőket bevonni, a valóságban számos egyéb, itt nem modellezett faktor is befolyásolhatja a nemzetköziesedési sikert.

    Kérem, használja kritikusan az eredményeket, és tekintse azokat egy kiindulási pontnak a további stratégiai gondolkodáshoz!
    
    Sikeres elemzést kívánok!
    
    *Győrfi Attila*
    """)

elif page == "Főoldal (Kkv Profil)":
    st.header("Kkv Profil Összefoglaló")
    st.write("Az alábbiakban táblázatos formában láthatja a jelenleg beállított kkv jellemzőket. Az értékeléshez és a részletes beszámolóhoz navigáljon a megfelelő oldalra.")
    profile_data_for_style = []
    any_factor_not_set_on_main = False
    for factor_name_key in factor_definitions.keys():
        value = st.session_state.selected_factors.get(factor_name_key)
        if value is None: any_factor_not_set_on_main = True
        description_text = factor_definitions[factor_name_key].get(value, "Még nem értékelt").split(': ',1)[1] if value is not None else "Még nem értékelt"
        profile_data_for_style.append({"Tényező": factor_name_key, "Értékelés (1-5)": value, "Rövid Leírás": description_text})
    df_profile_for_style = pd.DataFrame(profile_data_for_style)
    styled_profile_styler = df_profile_for_style.style.apply(style_main_profile_row_cells, axis=1).hide(axis="index")
    def format_rating(val): return "-" if pd.isnull(val) else int(val)
    st.dataframe(styled_profile_styler.format({"Értékelés (1-5)": format_rating}), use_container_width=True, 
                 column_config={"Tényező": st.column_config.TextColumn("Tényező", width="medium"), 
                                "Értékelés (1-5)": st.column_config.TextColumn("Értékelés", width="small"),
                                "Rövid Leírás": st.column_config.TextColumn("Leírás", width="large")})
    if any_factor_not_set_on_main:
        st.info("A részletes beszámoló megtekintéséhez kérjük, először értékelje az összes tényezőt a 'Kkv Jellemzők Beállítása' oldalon.")
    if st.button("Részletes Beszámoló Megtekintése", key="show_report_btn_main", disabled=any_factor_not_set_on_main):
        st.session_state.current_page = "Beszámoló"; st.rerun() 

elif page == "Kkv Jellemzők Beállítása":
    st.header("Kkv Jellemzők Beállítása")
    st.write("Minden tényezőt értékeljen 1-től 5-ig terjedő skálán. Az értékeléséhez tartozó részletes magyarázat alább látható, a kiválasztott szintnek megfelelő színnel és félkövérrel kiemelve.")
    st.markdown("---")
    if any(value is None for value in st.session_state.selected_factors.values()):
        st.info("Még nem minden jellemzőt értékelt. Kérjük, válasszon minden tényezőhöz egy értéket (1-5) a folytatáshoz.")
    cols = st.columns(2); factor_keys = list(factor_definitions.keys()); num_factors = len(factor_keys); mid_point = (num_factors + 1) // 2
    for i, factor_name in enumerate(factor_keys):
        current_col = cols[0] if i < mid_point else cols[1]
        with current_col:
            st.markdown(f"#### **{factor_name}**") # MÓDOSÍTVA: Nagyobb, vastag cím
            current_value_for_factor = st.session_state.selected_factors.get(factor_name)
            selectbox_options_display = ["-"] + list(range(1, 6))
            current_selectbox_index = 0 # Alapértelmezett a "-"
            if current_value_for_factor is not None:
                try: current_selectbox_index = selectbox_options_display.index(current_value_for_factor)
                except ValueError: pass # Marad 0, ha az érték valamiért nem valid
            
            selected_option_from_sb = st.selectbox(label=f"Értékelés - {factor_name}", options=selectbox_options_display, index=current_selectbox_index, 
                                                   key=f"sb_factor_details_{factor_name.replace(' ', '_').replace('(', '').replace(')', '')}", label_visibility="collapsed")
            
            actual_selected_value_for_highlighting = None
            if selected_option_from_sb == "-":
                if st.session_state.selected_factors.get(factor_name) is not None: # Csak akkor frissítünk és futtatunk újra, ha None-ra változott
                    st.session_state.selected_factors[factor_name] = None
                    st.rerun()
            else:
                new_val = int(selected_option_from_sb)
                if st.session_state.selected_factors.get(factor_name) != new_val:
                    st.session_state.selected_factors[factor_name] = new_val
                    st.rerun()
                actual_selected_value_for_highlighting = new_val
            
            st.markdown("<u>Választható szintek és leírásuk:</u>", unsafe_allow_html=True)
            is_barrier_factor = "(Gátló)" in factor_name
            for val_option in range(1, 6):
                full_desc_text = factor_definitions[factor_name][val_option]
                display_text_option = f"{val_option}: {full_desc_text}"
                is_selected_option = (actual_selected_value_for_highlighting == val_option)
                style_str = get_score_text_style(val_option, is_barrier_factor, is_selected=is_selected_option)
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;<span style='{style_str}'>{display_text_option}</span>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True) 
    st.markdown("---")
    if all_factors_selected:
        st.subheader("A beállítások összefoglaló diagramja:")
        try:
            # ... (diagram kódja változatlan) ...
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
    else: st.info("A beállítások összefoglaló diagramja akkor jelenik meg, ha minden tényezőt értékelt.")
    st.markdown("---")

analysis_pages = ["Nemzetköziesedési Potenciál", "VRIO Elemzés", "Beszámoló", "Gyakorlati Javaslatok"]
if page in analysis_pages:
    if not all_factors_selected:
        st.warning("Kérjük, először értékelje az összes tényezőt a 'Kkv Jellemzők Beállítása' oldalon a folytatáshoz!")
        if st.button("Ugrás a beállításokhoz", key="goto_settings_from_warning"):
            st.session_state.current_page = "Kkv Jellemzők Beállítása"; st.rerun()
    else:
        if page == "Nemzetköziesedési Potenciál":
            st.header("Nemzetköziesedési Potenciál") # ... (tartalom változatlan) ...
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
            st.header("VRIO-modell elemzés"); st.info("A VRIO-modell... '✓' ... '✗' ...") # ... (tartalom változatlan) ...
            vrio_data_bool = get_vrio_table_data(innovacio, humantoke, penzugyi_stabilitas, kapcsolati_halo, technologiai_fejlettseg)
            df_vrio = pd.DataFrame(vrio_data_bool, columns=['Erőforrás', 'Értékes', 'Ritka', 'Utánozhatatlan', 'Szervezett'])
            styled_df_vrio_styler = df_vrio.style.applymap(highlight_vrio_cells, subset=['Értékes', 'Ritka', 'Utánozhatatlan', 'Szervezett']).set_properties(**{'text-align': 'center', 'font-weight': 'bold'}, subset=['Értékes', 'Ritka', 'Utánozhatatlan', 'Szervezett']).set_properties(**{'text-align': 'left', 'font-weight': 'bold'}, subset=['Erőforrás']).hide(axis="index")
            formatter_vrio = {col: (lambda x: "✓" if x else "✗") for col in ['Értékes', 'Ritka', 'Utánozhatatlan', 'Szervezett']}
            st.dataframe(styled_df_vrio_styler.format(formatter_vrio), use_container_width=True, column_config={"Erőforrás": st.column_config.TextColumn(width="large"), "Értékes": st.column_config.TextColumn(width="small"), "Ritka": st.column_config.TextColumn(width="small"), "Utánozhatatlan": st.column_config.TextColumn(width="small"), "Szervezett": st.column_config.TextColumn(width="small")})
            st.markdown("<br>", unsafe_allow_html=True)
        elif page == "Beszámoló":
            st.header("Részletes Eredmény Beszámoló"); st.markdown("---") # ... (tartalom a korábban megadott, bővített szöveggel) ...
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
            támogató_factors = {k:v for k,v in st.session_state.selected_factors.items() if "(Gátló)" not in k and v is not None}
            gátló_factors = {k:v for k,v in st.session_state.selected_factors.items() if "(Gátló)" in k and v is not None}
            erős_támogatók = sorted([ (k,v) for k,v in támogató_factors.items() if v >= 4], key=lambda item: item[1], reverse=True)
            if erős_támogatók:
                st.markdown("**Erősségek – Kiemelkedő erőforrások, amelyekre építhet a nemzetközi piacokon:**")
                text_block_strong = "Az elemzés alapján vállalkozása több területen is erős pozíciókkal rendelkezik, amelyek megalapozhatják a nemzetközi sikert. "
                for factor, value in erős_támogatók[:2]: 
                    factor_desc_detail = factor_definitions[factor][value].split(': ',1)[1]
                    text_block_strong += f"Különösen figyelemre méltó a(z) **{factor.lower()}** ({value}/5), amely azt jelenti, hogy vállalata {factor_desc_detail.lower()} Ez komoly versenyelőnyt biztosíthat a külpiacokon, és érdemes erre a képességre tudatosan építeni a nemzetközi stratégiát. "
                st.markdown(text_block_strong)
            else: st.markdown("**Erősségek – Kiemelkedő erőforrások:** Jelenleg nincsenek 4-es vagy 5-ös értékelésű támogató erőforrásai. Ez azt jelzi, hogy bár lehetnek stabilan működő területek, a kiemelkedő, nehezen másolható versenyelőnyök még fejlesztésre szorulnak. Érdemes lenne azonosítani és fejleszteni azokat a belső képességeket, amelyekre a nemzetközi terjeszkedés épülhet, vagy a meglévő közepes erőforrásokat magasabb szintre emelni.")
            st.markdown("<br>", unsafe_allow_html=True)
            gyenge_támogatók = sorted([ (k,v) for k,v in támogató_factors.items() if v <= 2], key=lambda item: item[1])
            if gyenge_támogatók:
                st.markdown("**Fejlesztendő területek – Erőforrások, amelyekre érdemes fókuszálni:**")
                text_block_weak = "Az értékelés rávilágított néhány olyan belső erőforrásra, amelyek további fejlesztést igényelnek a sikeres nemzetköziesedés érdekében, mivel jelenlegi szintjük korlátozhatja a külpiaci érvényesülést. "
                for factor, value in gyenge_támogatók[:2]:
                    factor_desc_detail = factor_definitions[factor][value].split(': ',1)[1]
                    text_block_weak += f"A(z) **{factor.lower()}** ({value}/5) területén jelentős előrelépésre van szükség, mivel jelenleg vállalata {factor_desc_detail.lower()} Ennek megerősítése kulcsfontosságú lehet a külpiaci versenyképesség javításához és a kockázatok csökkentéséhez. "
                st.markdown(text_block_weak)
            else: st.markdown("**Fejlesztendő területek – Erőforrások:** Úgy tűnik, nincsenek kifejezetten alacsony (1-es vagy 2-es) pontszámú támogató erőforrásai, ami pozitív. Azonban a közepes erőforrások további erősítése és a potenciális gyengeségek proaktív kezelése továbbra is fontos lehet a hosszú távú siker érdekében.")
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
            else: st.markdown("**Kedvező külső tényezők – Alacsony szintű akadályok:** Az elemzés nem tárt fel kiemelkedően alacsony (1-es vagy 2-es) pontszámú gátló tényezőket. Ez azt jelenti, hogy több területen is lehetnek kezelendő kihívások, amelyekre fel kell készülni, és proaktívan kell kezelni a potenciális nehézségeket.")
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
            else: st.markdown("**Kritikus kihívások – Jelentős akadályok:** Az értékelés alapján úgy tűnik, nincsenek kiemelkedően magas (4-es vagy 5-ös) pontszámú gátló tényezői, ami biztató. Ez csökkenti a közvetlen, súlyos kockázatokat, de a közepes szintű akadályokra is figyelmet kell fordítani és stratégiát kell kidolgozni azok hatékony kezelésére.")
            st.markdown("---")
            st.subheader("3. VRIO Elemzés Kulcsfontosságú Megállapításai")
            vrio_data = get_vrio_table_data(innovacio, humantoke, penzugyi_stabilitas, kapcsolati_halo, technologiai_fejlettseg)
            vrio_paragraphs = []
            for row in vrio_data:
                eroforras, v, r, i, o = row; sentence_parts = []
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
            for par in vrio_paragraphs: st.markdown(par); st.markdown(" ") 
            st.markdown("---")
            st.subheader("4. Összegzés és Javasolt Következő Lépések")
            st.markdown("Ez a szimuláció egy pillanatképet adott vállalkozása nemzetköziesedési felkészültségéről...")
            st.markdown("A konkrét, személyre szabott teendőkért... **tekintse meg a 'Gyakorlati Javaslatok' oldalt**...")
            st.markdown("Ne feledje, a nemzetköziesedés egy folyamatos... Sok sikert kívánunk!")

        elif page == "Gyakorlati Javaslatok":
            st.header("Gyakorlati Javaslatok a Nemzetköziesedéshez")
            box_style = get_status_box_style(nemzetkoziesedesi_potencial_num) 
            message_javaslat = ""; javaslat_reszlet = ""
            # MÓDOSÍTVA: Részletesebb javaslatok
            javaslat_alacsony_text = """
            * **Pénzügyi alapok megerősítése:** Alaposan vizsgálja meg a rendelkezésre álló kedvezményes hitelkonstrukciókat, hazai és uniós pályázati lehetőségeket (pl. GINOP Plusz, Horizon Europe keretprogramok, EIC Accelerator), valamint a kockázati tőkebefektetési opciókat, amelyek segíthetnek a nemzetköziesedés kezdeti, tőkeigényes szakaszának finanszírozásában. Készítsen részletes, több forgatókönyvre épülő pénzügyi tervet a várható költségekről, a szükséges befektetésekről és a lehetséges megtérülési időről.
            * **Piaci ismeretek és kompetenciák bővítése:** Kezdjen mélyreható, célzott piackutatást a potenciális célországokról. Ez foglalja magában a versenytársak alapos elemzését, a helyi fogyasztói igények és preferenciák megértését, valamint a jogi, adózási és kereskedelmi szabályozási környezet részletes feltárását. Fontolja meg nemzetközi tapasztalattal rendelkező tanácsadók vagy piackutató cégek bevonását, akik helyismerettel rendelkeznek.
            * **Digitális felkészültség és online jelenlét erősítése:** Fektessen be modern, többnyelvű e-kereskedelmi platformokba, ha termékeit online kívánja értékesíteni. Fejlessze célzott online marketing stratégiáját (keresőoptimalizálás - SEO, nemzetközi közösségi média kampányok, célzott hirdetések, releváns tartalommarketing), és biztosítsa a megfelelő digitális infrastruktúrát (pl. CRM rendszer, ügyfélszolgálati eszközök) a nemzetközi vevők hatékony kiszolgálásához.
            * **Belső erőforrások és képességek fejlesztése:** Azonosítsa azokat a kulcsfontosságú belső erőforrásokat (pl. innovációs kapacitás, humántőke), amelyek jelenleg alacsony szinten állnak, és dolgozzon ki egy tervet ezek fejlesztésére. Ez magában foglalhatja képzéseket, új technológiák bevezetését vagy a belső folyamatok újraszervezését.
            """
            javaslat_kozepes_text = """
            * **Innováció és termékfejlesztés nemzetközi fókusszal:** Folyamatosan fejlessze termékeit és szolgáltatásait úgy, hogy azok megfeleljenek a kiválasztott célpiacok specifikus igényeinek és elvárásainak. Keresse aktívan a K+F együttműködési lehetőségeket hazai és nemzetközi partnerekkel, vegyen részt iparági innovációs programokban, és kövesse figyelemmel a globális technológiai és piaci trendeket. Fontolja meg termékei adaptálását (pl. csomagolás, funkciók, nyelvi lokalizáció).
            * **Humántőke célzott fejlesztése:** Biztosítson célzott képzéseket és nyelvi kurzusokat munkatársainak, különös tekintettel a nemzetközi üzleti kommunikációra, tárgyalástechnikára és a célországok kulturális sajátosságaira. Fontolja meg nemzetközi tapasztalattal rendelkező szakemberek alkalmazását kulcspozíciókba, vagy vegyen igénybe külső tanácsadást a nemzetközi menedzsmenti ismeretek bővítésére.
            * **Kapcsolati háló tudatos építése és partnerkeresés:** Vegyen részt aktívan releváns nemzetközi üzleti fórumokon, szakmai kiállításokon és vásárokon a potenciális partnerek (disztribútorok, ügynökök, vevők) felkutatása érdekében. Csatlakozzon nemzetközi szakmai szervezetekhez és kereskedelmi kamarákhoz, használja ki a diplomáciai képviseletek által nyújtott üzletfejlesztési lehetőségeket.
            * **Gátló tényezők proaktív kezelése:** Azonosítsa azokat a gátló tényezőket, amelyek közepes vagy magas kockázatot jelentenek, és dolgozzon ki stratégiákat ezek csökkentésére vagy kezelésére. Ez lehet például a pénzügyi források diverzifikálása, a piaci ismeretek mélyítése célzott kutatásokkal, vagy a digitális kompetenciák fejlesztése.
            """
            javaslat_magas_text = """
            * **Stratégiai partnerségek és szövetségek kialakítása:** Keressen hosszú távú, kölcsönösen előnyös stratégiai szövetségeket és partnerségeket a célpiacokon, mint például megbízható disztribútorok, helyi gyártási partnerek, vagy hozzon létre közös vállalatokat. Ezek a kapcsolatok jelentősen segíthetik a piaci behatolást, a helyi ismeretek megszerzését és a működési kockázatok megosztását.
            * **Folyamatos innováció és piacvezető pozícióra törekvés:** Maradjon a technológiai és piaci trendek élén, fektessen be a legújabb megoldásokba, és gyűjtsön aktívan, rendszeresen vevői visszajelzéseket a termékek és szolgáltatások folyamatos tökéletesítése, valamint új piaci igények azonosítása érdekében. Törekedjen arra, hogy megkülönböztesse magát a versenytársaktól és erősítse piaci pozícióját.
            * **Kockázatkezelési stratégiák finomítása és diverzifikáció:** Fejlessze tovább és alkalmazza következetesen a nemzetközi kereskedelemmel járó komplex kockázatok (pl. devizaárfolyam-ingadozás, politikai és gazdasági instabilitás a célországokban, kintlévőségek kezelése, logisztikai kihívások) kezelésére vonatkozó stratégiákat. Fontolja meg exportbiztosítások és egyéb pénzügyi kockázatcsökkentő eszközök használatát. Vizsgálja meg a piaci diverzifikáció lehetőségét több ország vagy régió felé a kockázatok porlasztása érdekében.
            * **Márkaépítés és nemzetközi jelenlét erősítése:** Fektessen be a nemzetközi márkaismertség növelésébe és a pozitív vállalati imázs kialakításába a célpiacokon. Használja hatékonyan a digitális marketing eszközöket, és vegyen részt presztízsértékű nemzetközi eseményeken a láthatóság növelése érdekében.
            """
            if nemzetkoziesedesi_potencial_num < 40:
                message_javaslat = "Alacsony nemzetköziesedési potenciál. Erős fókuszra van szükség a belső erőforrások fejlesztésére!"
                st.markdown(f'<div style="{box_style}">{message_javaslat}</div>', unsafe_allow_html=True); st.markdown(javaslat_alacsony_text)
            elif 40 <= nemzetkoziesedesi_potencial_num < 70:
                message_javaslat = "Közepes nemzetköziesedési potenciál. Vannak erősségei, de a gátló tényezők leküzdése kritikus!"
                st.markdown(f'<div style="{box_style}">{message_javaslat}</div>', unsafe_allow_html=True); st.markdown(javaslat_kozepes_text)
            else: 
                message_javaslat = "Magas nemzetköziesedési potenciál! Fókuszáljon a fenntartható növekedésre és a piacvezető pozíció megszerzésére."
                st.markdown(f'<div style="{box_style}">{message_javaslat}</div>', unsafe_allow_html=True); st.markdown(javaslat_magas_text)
