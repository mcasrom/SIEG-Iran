import streamlit as st
import json, os
from pathlib import Path

st.set_page_config(page_title="SIEG-IRAN Crisis Room", layout="wide", page_icon="🚨")
LIVE_DIR = Path("../data/live")
VECTORS = [
    "Conflicto_Directo", "Proxies_Regionales", "Nuclear",
    "Energia_Hormuz", "Teatro_Regional", "Posicion_Global",
    "Sanciones_Economia", "Diplomatico"
]

# Sidebar info
st.sidebar.title("SIEG-IRAN Dashboard")
st.sidebar.markdown("Crisis room Iran-Israel")

# Tabs
tabs = st.tabs(["🔴 Crisis Overview","🗺 Teatro de Operaciones","🕸 Red de Alianzas",
                "⚛ Nuclear & Armamento","🛢 Energía & Hormuz","💰 Economía & Sanciones",
                "🌍 Impacto Global","📖 Docs"])

# Dummy data loader
def load_vector(vector):
    f = LIVE_DIR / f"iran_{vector}.json"
    if f.exists():
        with open(f, "r") as fh: return json.load(fh)
    return {"vector": vector, "score": 0, "events":[]}

# Tab 1: Crisis Overview
with tabs[0]:
    st.header("Crisis Overview")
    scores = [load_vector(v)["score"] for v in VECTORS]
    for v, s in zip(VECTORS, scores):
        st.metric(label=v, value=s)

# Tab 2: Teatro de Operaciones
with tabs[1]:
    st.header("Teatro de Operaciones")
    st.write("Mapa dummy: frentes activos y proxies por país")

# Tab 3: Red de Alianzas
with tabs[2]:
    st.header("Red de Alianzas")
    st.write("Grafo de red dummy (Plotly Network Graph)")

# Tab 4: Nuclear & Armamento
with tabs[3]:
    st.header("Nuclear & Armamento")
    st.write("Timeline de instalaciones y enriquecimiento de Uranio")

# Tab 5: Energía & Hormuz
with tabs[4]:
    st.header("Energía & Hormuz")
    st.write("Mapa de gasoductos y precio Brent (dummy)")

# Tab 6: Economía & Sanciones
with tabs[5]:
    st.header("Economía & Sanciones")
    st.write("Rial iraní y sanciones timeline (dummy)")

# Tab 7: Impacto Global
with tabs[6]:
    st.header("Impacto Global")
    st.write("Radar chart potencias y exposición OTAN (dummy)")

# Tab 8: Docs
with tabs[7]:
    st.header("Docs")
    st.write("Documentación integrada y referencias (dummy)")
