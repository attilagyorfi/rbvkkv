import streamlit as st
import pandas as pd

# --- VRIO modell elemzéshez segédfüggvény ---
def get_vrio_table_data(innovacio, humantoke, penzugyi_stabilitas, kapcsolati_halo, technologiai_fejlettseg):
    # A szakdolgozat 3. táblázata alapján a VRIO kritériumok
    # Jelenlegi egyszerűsített logika:
    # Valuable: Általában 3-tól jó
    # Rare: Általában 4-től jó
    # Inimitable: Csak bizonyos tényezők lehetnek 5-ös értéknél
    # Organized: Általában 4-től jó

    data = []

    # Innováció
    is_valuable = innovacio >= 3
    is_rare = innovacio >= 4
    is_inimitable = innovacio == 5 # Csak a legmagasabb szinten utánozhatatlan
    is_organized = innovacio >= 4
    data.append(["Innováció", is_valuable, is_rare, is_inimitable, is_organized])

    # Humántőke
    is_valuable = humantoke >= 3
    is_rare = humantoke >= 4
    is_inimitable = humantoke == 5 # Csak a legmagasabb szinten utánozhatatlan
    is_organized = humantoke >= 4
    data.append(["Humántőke", is_valuable, is_rare, is_inimitable, is_organized])

    # Pénzügyi stabilitás
    is_valuable = penzugyi_stabilitas >= 3
    is_rare = False # A szakdolgozat szerint a pénzügyi források nem ritka
    is_inimitable = False # A szakdolgozat szerint a pénzügyi források nem utánozhatatlan
    is_organized = penzugyi_stabilitas >= 3
    data.append(["Pénzügyi források", is_valuable, is_rare, is_inimitable, is_organized])

    # Kapcsolati háló
    is_valuable = kapcsolati_halo >= 3
    is_rare = kapcsolati_halo >= 4
    is_inimitable = kapcsolati_halo >= 4 # Erős háló nehezen utánozható
    is_organized = kapcsolati_halo >= 3
    data.append(["Kapcsolati háló", is_valuable, is_rare, is_inimitable, is_organized])

    # Technológiai fejlettség
    is_valuable = technologiai_fejlettseg >= 3
    is_rare = technologiai_fejlettseg >= 4
    is_inimitable = False # A szakdolgozat szerint a technológia elérhető, de beépítése versenyelőny
    is_organized = technologiai_fejlettseg >= 3
    data.append(["Technológiai fejlettség", is_valuable, is_rare, is_inimitable, is_organized])

    return data

# --- Stílus a "Gyakorlati Javaslatok" oldal fő állapotjelző dobozához ---
def get_status_box_style(potencial_score):
    # Színátmenet a pontszám alapján (piros-narancs-zöld)
    red_intensity, green_intensity, blue_intensity = 240, 240, 240 # Alap szürke

    if potencial_score < 40: # Pirosas
        # Minél alacsonyabb, annál erősebb piros, kevésbé zöld/kék
        normalized_score = potencial_score / 39.0
        red_intensity = 255
        green_intensity = int(150 + 70 * normalized_score) # Halványabb piros (rózsaszínesebb)
        blue_intensity = int(150 + 70 * normalized_score)
    elif 40 <= potencial_score < 70: # Narancsos/Sárgás
        # Átmenet a sárgás felé
        normalized_score_in_range = (potencial_score - 40) / 29.0
        red_intensity = 255
        green_intensity = int(210 + 45 * normalized_score_in_range) # Narancstól sárgáig
        blue_intensity = int(100 - 100 * normalized_score_in_range) # Kevés kék
    else: # Zöldes (>= 70)
        # Minél magasabb, annál erősebb zöld
        normalized_score_in_range = (potencial_score - 70) / 30.0
        red_intensity = int(200 - 150 * normalized_score_in_range)
        green_intensity = 255
        blue_intensity = int(200 - 150 * normalized_score_in_range)


    red_intensity = max(0, min(255, red_intensity))
    green_intensity = max(0, min(255, green_intensity))
    blue_intensity = max(0, min(255, blue_intensity))

    hex_color = f"#{red_intensity:02x}{green_intensity:02x}{blue_intensity:02x}"

    # Szövegszín meghatározása a kontraszt érdekében
    luminance = (0.299 * red_intensity + 0.587 * green_intensity + 0.114 * blue_intensity) / 255
    text_color = "#FFFFFF" if luminance < 0.45 else "#000000" # Küszöbérték finomítva

    return f"background-color: {hex_color}; color: {text_color}; padding: 1rem; border-radius: 0.25rem; margin-bottom: 1rem; border: 1px solid {text_color if luminance < 0.45 else '#dddddd'};"


# --- Függvény a VRIO táblázat stílusozásához (Streamlit Stylerrel) ---
def highlight_vrio_cells(val):
    color_true = 'rgba(212, 237, 218, 0.7)'  # Világoszöld (enyhén áttetsző)
    color_false = 'rgba(248, 215, 218, 0.7)' # Világospiros (enyhén áttetsző)
    if isinstance(val, bool):
        if val:
            return f'background-color: {color_true}'
        else:
            return f'background-color: {color_false}'
    return ''

# --- Stílus a "Kkv Jellemzők Beállítása" oldal tényezőnkénti magyarázó dobozaihoz ---
def get_factor_explanation_box_style(score, is_barrier=False):
    """
    Meghatározza a magyarázó doboz CSS stílusát a faktor pontszáma alapján.
    """
    base_color_profile = "neutral" 

    if is_barrier:
        if score <= 2: 
            base_color_profile = "good" # Jó (alacsony gát)
        elif score == 3: 
            base_color_profile = "neutral" # Semleges
        else: 
            base_color_profile = "bad" # Rossz (magas gát)
    else: # Támogató tényező
        if score <= 2: 
            base_color_profile = "bad" # Rossz (alacsony erőforrás)
        elif score == 3: 
            base_color_profile = "neutral" # Semleges
        else: 
            base_color_profile = "good" # Jó (magas erőforrás)

    hex_color = "rgba(240, 242, 246, 0.7)" # Alapértelmezett semleges Streamlit-szerű háttér (enyhén áttetsző)
    text_color = "#000000" 
    border_color = "rgba(206, 212, 218, 0.7)" 

    if base_color_profile == "bad":
        hex_color = "rgba(248, 215, 218, 0.7)" 
        text_color = "#721c24" 
        border_color = "rgba(245, 198, 203, 0.9)"
    elif base_color_profile == "neutral":
        hex_color = "rgba(255, 243, 205, 0.7)" 
        text_color = "#856404" 
        border_color = "rgba(255, 238, 186, 0.9)"
    elif base_color_profile == "good":
        hex_color = "rgba(212, 237, 218, 0.7)" 
        text_color = "#155724" 
        border_color = "rgba(195, 230, 203, 0.9)"
            
    return f"background-color: {hex_color}; color: {text_color}; padding: 0.75rem; border-radius: 0.25rem; margin-bottom: 0.5rem; border: 1px solid {border_color};"