"""
S.I.E.G. Iran — Crisis Room Dashboard V1.0
8 tabs: Crisis Overview · Teatro Operaciones · Red Alianzas ·
        Nuclear & Armamento · Energia & Hormuz ·
        Economia & Sanciones · Impacto Global · Docs
"""

import glob
import json
import logging
import os
import time
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ─── CONFIG ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="S.I.E.G. Iran — Crisis Room",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DATA_DIR     = os.path.join(BASE_DIR, "data", "live")
HISTORY_FILE = os.path.join(DATA_DIR, "history_iran.csv")
SUMMARY_FILE = os.path.join(DATA_DIR, "iran_crisis_summary.json")
IRAN_PATTERN = os.path.join(DATA_DIR, "iran_*.json")

APP_VERSION     = "V1.0"
SCANNER_VERSION = "V1.0"
BUILD_DATE      = "2026"

VECTORES = [
    "Conflicto_Directo", "Proxies_Regionales", "Nuclear",
    "Energia_Hormuz", "Teatro_Regional", "Posicion_Global",
    "Sanciones_Economia", "Diplomatico",
]

VECTOR_DISPLAY = {
    "Conflicto_Directo":  "⚔️ Conflicto Directo",
    "Proxies_Regionales": "🕸 Proxies Regionales",
    "Nuclear":            "⚛️ Nuclear",
    "Energia_Hormuz":     "🛢 Energía & Hormuz",
    "Teatro_Regional":    "🗺 Teatro Regional",
    "Posicion_Global":    "🌍 Posición Global",
    "Sanciones_Economia": "💰 Sanciones & Economía",
    "Diplomatico":        "🕊 Diplomático",
}

VECTOR_ICON = {
    "Conflicto_Directo":  "⚔️",
    "Proxies_Regionales": "🕸",
    "Nuclear":            "⚛️",
    "Energia_Hormuz":     "🛢",
    "Teatro_Regional":    "🗺",
    "Posicion_Global":    "🌍",
    "Sanciones_Economia": "💰",
    "Diplomatico":        "🕊",
}

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ─── CSS ─────────────────────────────────────────────────────────
CRISIS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Share+Tech+Mono&display=swap');

:root {
    --bg:      #08050a;
    --bg2:     #0f0a12;
    --bg3:     #160f1a;
    --red:     #ff3300;
    --orange:  #ff6600;
    --yellow:  #ffaa00;
    --amber:   #ffcc00;
    --text:    #e8d8c8;
    --muted:   #775544;
    --border:  #2a1518;
    --green:   #44ff88;
    --blue:    #44aaff;
}

* { box-sizing: border-box; }
.stApp { background-color: var(--bg); color: var(--text); }
.block-container { max-width: 98% !important; padding-top: 3.5rem; }

h1, h2, h3 {
    font-family: 'Rajdhani', sans-serif !important;
    color: var(--orange) !important;
    letter-spacing: 0.06em;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: var(--bg2);
    border-bottom: 2px solid var(--red);
}
.stTabs [data-baseweb="tab"] {
    color: var(--muted);
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.82em;
}
.stTabs [aria-selected="true"] {
    color: var(--orange) !important;
    border-bottom: 2px solid var(--orange) !important;
}

/* Hero */
.crisis-hero {
    background: linear-gradient(135deg, #0f0005 0%, #1a0008 50%, #0f0a00 100%);
    border: 1px solid var(--red);
    border-left: 5px solid var(--red);
    border-radius: 6px;
    padding: 1.4rem 2rem;
    margin-bottom: 1.2rem;
    font-family: 'Share Tech Mono', monospace;
    position: relative;
    overflow: hidden;
}
.crisis-hero::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg, transparent, transparent 2px,
        rgba(255,51,0,0.015) 2px, rgba(255,51,0,0.015) 4px
    );
    pointer-events: none;
}
.crisis-title {
    color: var(--red);
    font-size: 1.6em;
    font-weight: bold;
    letter-spacing: 0.15em;
    font-family: 'Rajdhani', sans-serif;
}
.crisis-sub {
    color: var(--muted);
    font-size: 0.78em;
    margin-top: 4px;
}

/* Crisis score badge */
.crisis-score {
    display: inline-block;
    font-family: 'Rajdhani', sans-serif;
    font-size: 2.8em;
    font-weight: 700;
    letter-spacing: 0.05em;
    padding: 0.2em 0.5em;
    border-radius: 6px;
    border: 2px solid;
    line-height: 1.1;
}
.crisis-critico { color: #ff2200; border-color: #ff2200; background: #1a0000; }
.crisis-alto    { color: #ff6600; border-color: #ff6600; background: #1a0800; }
.crisis-medio   { color: #ffaa00; border-color: #ffaa00; background: #1a1200; }
.crisis-bajo    { color: #44ff88; border-color: #44ff88; background: #001a08; }

/* Alert box */
.alert-critico {
    background: #1a0000; border-left: 4px solid #ff2200;
    color: #ff8888; padding: 10px 16px; border-radius: 4px;
    font-family: 'Share Tech Mono', monospace; font-size: 0.82em;
    margin: 4px 0;
}
.alert-warn {
    background: #1a0800; border-left: 4px solid #ff6600;
    color: #ffaa88; padding: 10px 16px; border-radius: 4px;
    font-family: 'Share Tech Mono', monospace; font-size: 0.82em;
    margin: 4px 0;
}

/* Quality badge */
.qbadge {
    display: inline-block; font-family: 'Share Tech Mono', monospace;
    font-size: 0.68em; padding: 2px 8px; border-radius: 10px;
    margin-top: 2px; font-weight: bold;
}
.q-green  { background:#0a2a0a; color:#44ff88; border:1px solid #44ff88; }
.q-blue   { background:#0a1a2a; color:#44aaff; border:1px solid #44aaff; }
.q-yellow { background:#2a2200; color:#ffaa00; border:1px solid #ffaa00; }
.q-orange { background:#2a1200; color:#ff6600; border:1px solid #ff6600; }
.q-red    { background:#2a0000; color:#ff3300; border:1px solid #ff3300; }

/* Actor card */
.actor-card {
    background: var(--bg2); border: 1px solid var(--border);
    border-radius: 6px; padding: 12px 14px; margin-bottom: 8px;
    font-family: 'Share Tech Mono', monospace; font-size: 0.82em;
}
.actor-card:hover { border-color: var(--orange); }
.actor-name { color: var(--orange); font-weight: bold; font-size: 1.05em; }
.actor-role { color: var(--muted); font-size: 0.88em; margin-top: 2px; }
.actor-side-iran   { border-left: 3px solid #ff3300; }
.actor-side-israel { border-left: 3px solid #4488ff; }
.actor-side-proxy  { border-left: 3px solid #ff8800; }
.actor-side-global { border-left: 3px solid #888888; }

/* Footer */
.iran-footer {
    border-top: 1px solid var(--border); margin-top: 30px;
    padding: 16px 0 8px 0; text-align: center;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75em; color: var(--muted); line-height: 2.2;
}
.iran-footer a { color: var(--orange); text-decoration: none; }
.iran-footer a:hover { text-decoration: underline; }
</style>
"""
st.markdown(CRISIS_CSS, unsafe_allow_html=True)

# ─── CARGA DE DATOS ──────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_vectores() -> list:
    result = []
    for v in VECTORES:
        path = os.path.join(DATA_DIR, f"iran_{v.lower()}.json")
        try:
            with open(path) as f:
                d = json.load(f)
            result.append({
                "key":           v,
                "display":       VECTOR_DISPLAY.get(v, v),
                "icon":          VECTOR_ICON.get(v, "·"),
                "score":         float(d.get("score", 20)),
                "disonancia":    bool(d.get("disonancia", False)),
                "noticias":      int(d.get("noticias", 0)),
                "timestamp":     float(d.get("timestamp", 0)),
                "calidad_nivel": d.get("calidad_nivel", "ROJO"),
                "calidad_emoji": d.get("calidad_emoji", "🔴"),
                "calidad_css":   d.get("calidad_css", "red"),
                "uso_fallback":  bool(d.get("uso_fallback", False)),
                "uso_web":       bool(d.get("uso_web", False)),
            })
        except (OSError, json.JSONDecodeError):
            result.append({
                "key": v, "display": VECTOR_DISPLAY.get(v, v),
                "icon": VECTOR_ICON.get(v, "·"),
                "score": float(20),
                "disonancia": False, "noticias": 0, "timestamp": 0,
                "calidad_nivel": "ROJO", "calidad_emoji": "🔴",
                "calidad_css": "red", "uso_fallback": False, "uso_web": False,
            })
    return sorted(result, key=lambda x: x["score"], reverse=True)


@st.cache_data(ttl=120)
def load_crisis_summary() -> dict:
    try:
        return json.load(open(SUMMARY_FILE))
    except (OSError, json.JSONDecodeError):
        return {"crisis_score": 65, "timestamp": time.time(), "vectores": {}}


@st.cache_data(ttl=180)
def load_history() -> pd.DataFrame:
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame(columns=["timestamp", "vector", "score", "dt"])
    try:
        df = pd.read_csv(HISTORY_FILE, header=None,
                         names=["timestamp", "vector", "score"])
        df["score"]     = pd.to_numeric(df["score"], errors="coerce").fillna(0)
        df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")
        df["dt"]        = pd.to_datetime(df["timestamp"], unit="s")
        return df.sort_values("dt")
    except Exception:
        return pd.DataFrame(columns=["timestamp", "vector", "score", "dt"])


@st.cache_data(ttl=300)
def fetch_oil_price() -> dict:
    try:
        import requests as _req
        r = _req.get(
            "https://query1.finance.yahoo.com/v8/finance/chart/BZ=F",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=6,
        )
        data   = r.json()
        meta   = data["chart"]["result"][0]["meta"]
        price  = meta.get("regularMarketPrice", 0)
        prev   = meta.get("chartPreviousClose", price)
        return {"brent": round(price, 2), "delta": round(price - prev, 2), "ok": True}
    except Exception:
        return {"brent": 0.0, "delta": 0.0, "ok": False}

# ─── HELPERS ─────────────────────────────────────────────────────
def score_css(s):
    if s >= 80: return "crisis-critico"
    if s >= 60: return "crisis-alto"
    if s >= 40: return "crisis-medio"
    return "crisis-bajo"

def score_label(s):
    if s >= 80: return "🔴 CRÍTICO"
    if s >= 60: return "🟠 ALTO"
    if s >= 40: return "🟡 MEDIO"
    return "🟢 BAJO"

def gauge_color(s):
    if s >= 80: return "#ff2200"
    if s >= 60: return "#ff6600"
    if s >= 40: return "#ffaa00"
    return "#44ff88"

def make_gauge(valor, titulo, height=180):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#ff6600",
                     "tickfont": {"color": "#775544", "size": 7}},
            "bar":  {"color": gauge_color(valor)},
            "bgcolor": "#0f0a12",
            "bordercolor": "#2a1518",
            "steps": [
                {"range": [0,  40], "color": "#0a0a0a"},
                {"range": [40, 60], "color": "#120800"},
                {"range": [60, 80], "color": "#180500"},
                {"range": [80,100], "color": "#1a0000"},
            ],
        },
        number={"font": {"color": gauge_color(valor), "size": 26,
                         "family": "Rajdhani"}, "suffix": "%"},
        title={"text": titulo, "font": {"color": "#cc8844", "size": 10,
                                        "family": "Share Tech Mono"}},
    ))
    fig.update_layout(
        height=height,
        margin=dict(t=40, b=10, l=10, r=10),
        paper_bgcolor="#08050a",
        font_color="#ff6600",
    )
    return fig

# ─── SIDEBAR ─────────────────────────────────────────────────────
def render_sidebar(vectores, summary):
    with st.sidebar:
        st.markdown(
            "<div style='font-family:Rajdhani,sans-serif;color:#ff3300;"
            "font-size:1.2em;font-weight:700;letter-spacing:0.1em;'>"
            "🔴 IRAN CRISIS ROOM</div>",
            unsafe_allow_html=True,
        )
        crisis = summary.get("crisis_score", 65)
        st.markdown(
            f"<div style='text-align:center;margin:12px 0'>"
            f"<span class='crisis-score {score_css(crisis)}'>{crisis}%</span><br>"
            f"<span style='font-family:Share Tech Mono;font-size:0.75em;"
            f"color:#775544;'>{score_label(crisis)}</span></div>",
            unsafe_allow_html=True,
        )
        st.divider()

        st.markdown(
            "<span style='font-family:Share Tech Mono;color:#775544;"
            "font-size:0.75em;'>VECTORES ACTIVOS</span>",
            unsafe_allow_html=True,
        )
        for v in sorted(vectores, key=lambda x: x["score"], reverse=True):
            bar = int(v["score"] / 10)
            bar_filled = "█" * bar + "░" * (10 - bar)
            color = gauge_color(v["score"])
            st.markdown(
                f"<div style='font-family:Share Tech Mono;font-size:0.7em;"
                f"margin:3px 0;'>"
                f"<span style='color:#cc6633;'>{v['icon']}</span> "
                f"<span style='color:#cc8844;'>{v['key'].replace('_',' ')[:16]}</span><br>"
                f"<span style='color:{color};font-size:0.95em;'>{bar_filled}</span> "
                f"<span style='color:{color};'>{v['score']}%</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.divider()
        st.markdown(
            "<span style='font-family:Share Tech Mono;color:#775544;"
            "font-size:0.75em;'>PROYECTOS RELACIONADOS</span>",
            unsafe_allow_html=True,
        )
        st.markdown("[🛡 SIEG Core →](https://sieg-intelligence-radar.streamlit.app)")
        st.markdown("[🌐 SIEG Atlas →](https://sieg-atlas-intelligence.streamlit.app)")
        st.divider()
        st.markdown(
            "<span style='font-family:Share Tech Mono;color:#775544;"
            "font-size:0.72em;'>✉ mybloggingnotes@gmail.com</span>",
            unsafe_allow_html=True,
        )


# ─── TAB 1: CRISIS OVERVIEW ──────────────────────────────────────
def render_overview(vectores, summary, df_history):
    crisis = summary.get("crisis_score", 65)

    # Hero
    ts = summary.get("timestamp", time.time())
    dt_str = datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M") if ts else "—"
    st.markdown(f"""
    <div class='crisis-hero'>
        <div class='crisis-title'>🔴 S.I.E.G. IRAN — SALA DE CRISIS</div>
        <div class='crisis-sub'>
            Iran-Israel Conflict Monitor · {dt_str} UTC ·
            Scanner {SCANNER_VERSION} · {len(vectores)} vectores activos
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Crisis score + nivel
    col_score, col_nivel, col_oil = st.columns([2, 2, 2])
    with col_score:
        st.markdown(
            f"<div style='text-align:center;padding:1rem;'>"
            f"<div style='font-family:Share Tech Mono;color:#775544;"
            f"font-size:0.75em;letter-spacing:0.1em;margin-bottom:8px;'>"
            f"NIVEL DE CRISIS GLOBAL</div>"
            f"<span class='crisis-score {score_css(crisis)}'>{crisis}%</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_nivel:
        n_crit = sum(1 for v in vectores if v["score"] >= 80)
        n_alto = sum(1 for v in vectores if 60 <= v["score"] < 80)
        n_med  = sum(1 for v in vectores if 40 <= v["score"] < 60)
        st.markdown(
            f"<div style='font-family:Share Tech Mono;font-size:0.82em;"
            f"padding:1rem;background:#0f0a12;border:1px solid #2a1518;"
            f"border-radius:6px;'>"
            f"<div style='color:#775544;font-size:0.8em;margin-bottom:8px;'>"
            f"DISTRIBUCIÓN VECTORES</div>"
            f"<span style='color:#ff2200;'>● CRÍTICO: {n_crit}</span><br>"
            f"<span style='color:#ff6600;'>● ALTO: {n_alto}</span><br>"
            f"<span style='color:#ffaa00;'>● MEDIO: {n_med}</span><br>"
            f"<span style='color:#44ff88;'>● BAJO: {len(vectores)-n_crit-n_alto-n_med}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_oil:
        oil = fetch_oil_price()
        if oil["ok"]:
            delta_color = "#ff3300" if oil["delta"] > 0 else "#44ff88"
            delta_sign  = "▲" if oil["delta"] > 0 else "▼"
            st.markdown(
                f"<div style='font-family:Share Tech Mono;font-size:0.82em;"
                f"padding:1rem;background:#0f0a12;border:1px solid #2a1518;"
                f"border-radius:6px;'>"
                f"<div style='color:#775544;font-size:0.8em;margin-bottom:8px;'>"
                f"BRENT CRUDE (RT)</div>"
                f"<span style='color:#ffaa00;font-size:1.8em;font-family:Rajdhani;"
                f"font-weight:700;'>${oil['brent']}</span><br>"
                f"<span style='color:{delta_color};'>{delta_sign} {abs(oil['delta'])}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.divider()

    # Gauges 4x2
    cols = st.columns(4)
    for i, v in enumerate(vectores):
        with cols[i % 4]:
            fig = make_gauge(v["score"], v["key"].replace("_", " "))
            st.plotly_chart(fig, use_container_width=True,
                           config={"displayModeBar": False})
            fb  = " FB"  if v["uso_fallback"] else ""
            web = " WEB" if v["uso_web"]      else ""
            st.markdown(
                f"<div style='text-align:center;margin-top:-8px;'>"
                f"<span class='qbadge q-{v['calidad_css']}'>"
                f"{v['calidad_emoji']} {v['calidad_nivel']}{fb}{web}"
                f"</span></div>",
                unsafe_allow_html=True,
            )

    # Histórico comparativo si hay datos
    if not df_history.empty and len(df_history) > 10:
        st.divider()
        st.subheader("📈 Evolución de Tensión")
        df_90 = df_history[df_history["dt"] >= pd.Timestamp.now() - pd.Timedelta(days=90)]
        fig = go.Figure()
        for v in VECTORES:
            df_v = df_90[df_90["vector"] == v]
            if df_v.empty: continue
            fig.add_trace(go.Scatter(
                x=df_v["dt"], y=df_v["score"],
                mode="lines", name=v.replace("_", " "),
                line=dict(width=1.5),
                opacity=0.85,
            ))
        for y, label, color in [(80, "CRÍTICO", "#ff2200"),
                                 (60, "ALTO",    "#ff6600"),
                                 (40, "MEDIO",   "#ffaa00")]:
            fig.add_hline(y=y, line_dash="dot", line_color=color,
                         annotation_text=label,
                         annotation_font_color=color, opacity=0.4)
        fig.update_layout(
            height=280, paper_bgcolor="#08050a", plot_bgcolor="#0a0508",
            font_color="#cc8844", legend=dict(font=dict(size=9, color="#cc8844")),
            xaxis=dict(gridcolor="#1a0f1a"), yaxis=dict(gridcolor="#1a0f1a", range=[0,105]),
            margin=dict(t=20, b=20, l=30, r=10),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Exportar
    st.divider()
    st.subheader("📥 Exportar")
    c1, c2, c3 = st.columns(3)
    with c1:
        days = st.selectbox("Periodo", [7, 30, 90, 0],
            format_func=lambda x: f"Últimos {x}d" if x else "Todo",
            key="iran_exp")
    with c2:
        if not df_history.empty:
            df_e = df_history if days == 0 else df_history[
                df_history["dt"] >= pd.Timestamp.now() - pd.Timedelta(days=days)
            ]
            csv = df_e[["dt","vector","score"]].rename(
                columns={"dt":"datetime","vector":"vector","score":"score_pct"}
            ).to_csv(index=False).encode()
            st.download_button(
                f"⬇ CSV ({len(df_e)} filas)",
                csv,
                f"sieg_iran_{datetime.now().strftime('%Y-%m-%d')}.csv",
                "text/csv",
            )
    with c3:
        if not df_history.empty:
            st.caption(
                f"Total: {len(df_history):,} registros · "
                f"Desde {df_history['dt'].min().strftime('%d/%m/%Y')}"
            )


# ─── TAB 2: TEATRO DE OPERACIONES ────────────────────────────────
def render_teatro():
    st.subheader("🗺 Teatro de Operaciones — Oriente Medio")
    st.caption("Frentes activos · Proxies por país · Bases EEUU · Rutas de energía")

    # Mapa de puntos calientes
    hotspots = [
        # Iran
        dict(lat=35.7, lon=51.4,   label="Teherán",         tipo="Iran",   intensidad=90, desc="Capital. IRGC HQ, programa nuclear"),
        dict(lat=33.7, lon=51.7,   label="Natanz",           tipo="Nuclear",intensidad=95, desc="Principal instalación de enriquecimiento"),
        dict(lat=34.6, lon=49.9,   label="Fordow",           tipo="Nuclear",intensidad=90, desc="Instalación nuclear subterránea"),
        dict(lat=32.4, lon=53.7,   label="Isfahan",          tipo="Nuclear",intensidad=80, desc="Centro investigación nuclear"),
        dict(lat=30.3, lon=48.3,   label="Abadán",           tipo="Energia",intensidad=70, desc="Refinería petroleo clave"),
        dict(lat=27.2, lon=56.3,   label="Hormuz",           tipo="Energia",intensidad=88, desc="Estrecho. 20% petróleo mundial"),
        # Israel
        dict(lat=31.8, lon=35.2,   label="Jerusalén",        tipo="Israel", intensidad=85, desc="Capital. Sede gobierno"),
        dict(lat=32.1, lon=34.9,   label="Tel Aviv",         tipo="Israel", intensidad=85, desc="Centro militar. IDF HQ"),
        dict(lat=31.9, lon=34.8,   label="Palmachim",        tipo="Israel", intensidad=75, desc="Base aérea. Lanzamientos balísticos"),
        # Proxies
        dict(lat=33.9, lon=35.5,   label="Beirut",           tipo="Proxy",  intensidad=78, desc="Hezbollah. Líbano"),
        dict(lat=31.5, lon=34.5,   label="Gaza",             tipo="Proxy",  intensidad=92, desc="Hamas. Conflicto activo"),
        dict(lat=15.4, lon=44.2,   label="Saná",             tipo="Proxy",  intensidad=80, desc="Houthi / Ansar Allah. Yemen"),
        dict(lat=33.3, lon=44.4,   label="Bagdad",           tipo="Proxy",  intensidad=65, desc="PMF / Kataib Hezbollah. Iraq"),
        dict(lat=33.5, lon=36.3,   label="Damasco",          tipo="Proxy",  intensidad=70, desc="Fuerzas pro-Iran. Siria"),
        # USA / OTAN
        dict(lat=26.2, lon=50.6,   label="Bahréin (US 5th)", tipo="EEUU",   intensidad=60, desc="5th Fleet. Comando naval EEUU"),
        dict(lat=25.2, lon=55.4,   label="Dubai (Al Dhafra)",tipo="EEUU",   intensidad=55, desc="Base aérea USAF"),
        dict(lat=29.5, lon=48.1,   label="Kuwait (Ali Al S.)",tipo="EEUU",  intensidad=55, desc="Base EEUU. 35.000 efectivos región"),
        dict(lat=36.8, lon=36.9,   label="Incirlik (OTAN)",  tipo="EEUU",   intensidad=50, desc="Base OTAN. Turquía"),
        # Rutas energía
        dict(lat=26.0, lon=56.0,   label="Estrecho Ormuz",   tipo="Energia",intensidad=88, desc="21M barriles/día. Chokepoint crítico"),
        dict(lat=29.9, lon=32.6,   label="Canal Suez",       tipo="Energia",intensidad=72, desc="Ruta alternativa. Houthi amenaza"),
        dict(lat=12.6, lon=43.5,   label="Bab el-Mandeb",    tipo="Energia",intensidad=82, desc="Atacado por Houthi. Mar Rojo"),
    ]

    df_map = pd.DataFrame(hotspots)
    color_map = {
        "Iran":    "#ff3300",
        "Nuclear": "#ff00ff",
        "Israel":  "#4488ff",
        "Proxy":   "#ff8800",
        "EEUU":    "#aaaaaa",
        "Energia": "#ffcc00",
    }
    df_map["color"] = df_map["tipo"].map(color_map)

    fig = go.Figure()
    for tipo, color in color_map.items():
        df_t = df_map[df_map["tipo"] == tipo]
        if df_t.empty: continue
        fig.add_trace(go.Scattergeo(
            lat=df_t["lat"], lon=df_t["lon"],
            mode="markers+text",
            name=tipo,
            marker=dict(
                size=df_t["intensidad"] / 8,
                color=color,
                opacity=0.85,
                line=dict(color="#000000", width=0.5),
            ),
            text=df_t["label"],
            textposition="top center",
            textfont=dict(size=8, color=color),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Tipo: " + tipo + "<br>"
                "Intensidad: %{customdata[0]}%<br>"
                "%{customdata[1]}<extra></extra>"
            ),
            customdata=df_t[["intensidad", "desc"]].values,
        ))

    fig.update_layout(
        geo=dict(
            scope="world",
            center=dict(lat=30, lon=45),
            projection_scale=4.5,
            showland=True, landcolor="#0a0810",
            showocean=True, oceancolor="#05080f",
            showlakes=False,
            showcountries=True, countrycolor="#1a1520",
            showcoastlines=True, coastlinecolor="#2a2030",
            bgcolor="#08050a",
        ),
        height=550,
        paper_bgcolor="#08050a",
        legend=dict(font=dict(color="#cc8844", size=10), bgcolor="#0f0a12",
                   bordercolor="#2a1518"),
        margin=dict(t=10, b=10, l=0, r=0),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Tabla de puntos calientes
    st.subheader("📍 Puntos Calientes")
    df_show = df_map[["label", "tipo", "intensidad", "desc"]].sort_values(
        "intensidad", ascending=False
    ).rename(columns={
        "label": "Localización", "tipo": "Tipo",
        "intensidad": "Intensidad %", "desc": "Contexto"
    })
    st.dataframe(df_show, use_container_width=True, hide_index=True)


# ─── TAB 3: RED DE ALIANZAS ──────────────────────────────────────
def render_alianzas():
    st.subheader("🕸 Red de Alianzas y Actores Clave")
    st.caption("Grafo de relaciones: alianzas · cadena de mando · influencia")

    # Grafo con Plotly
    nodos = [
        # Iran camp
        ("Iran",         0.0, 0.8, "#ff3300", 30, "Estado"),
        ("IRGC",         -0.3, 0.6, "#ff4400", 20, "Guardia Revolucionaria"),
        ("Khamenei",     0.3, 0.6, "#ff5500", 18, "Líder Supremo"),
        ("Hezbollah",    -0.6, 0.3, "#ff6600", 22, "Proxy Líbano"),
        ("Hamas",        -0.4, 0.1, "#ff7700", 18, "Proxy Gaza"),
        ("Houthi",       -0.7, 0.0, "#ff6600", 20, "Proxy Yemen"),
        ("PMF Iraq",     -0.5, 0.5, "#ff5500", 15, "Proxy Iraq"),
        ("Assad Syria",  -0.2, 0.3, "#cc4400", 14, "Proxy Siria"),
        # Israel camp
        ("Israel",       0.0, -0.8, "#4488ff", 30, "Estado"),
        ("IDF",          -0.3, -0.6, "#5599ff", 22, "Fuerzas Defensa"),
        ("Mossad",       0.3, -0.6, "#6699ff", 18, "Inteligencia"),
        ("Netanyahu",    0.0, -0.5, "#77aaff", 16, "PM"),
        # EEUU / OTAN
        ("EEUU",         0.7, 0.2, "#aaaaaa", 26, "Aliado Israel"),
        ("OTAN",         0.8, 0.0, "#888888", 18, "Alianza colectiva"),
        ("CENTCOM",      0.8, 0.3, "#999999", 14, "Mando militar región"),
        # Otros
        ("Rusia",        0.4, 0.8, "#cc8800", 20, "Apoyo tácito Iran"),
        ("China",        0.6, 0.6, "#cc4400", 18, "Comprador petróleo"),
        ("Qatar",        0.2, 0.0, "#44ccaa", 14, "Mediador"),
        ("Arabia S.",    0.5, -0.3, "#ffcc00", 16, "Normalización Israel"),
        ("Turquía",      0.5, 0.5, "#888844", 14, "Posición ambigua"),
    ]

    edges = [
        # Iran → proxies
        ("Iran", "IRGC"),       ("Iran", "Khamenei"),
        ("IRGC", "Hezbollah"),  ("IRGC", "Hamas"),
        ("IRGC", "Houthi"),     ("IRGC", "PMF Iraq"),
        ("Iran", "Assad Syria"),
        # Israel
        ("Israel", "IDF"),      ("Israel", "Mossad"),
        ("Israel", "Netanyahu"),
        # EEUU
        ("EEUU", "Israel"),     ("EEUU", "OTAN"),
        ("EEUU", "CENTCOM"),    ("CENTCOM", "Israel"),
        # Otros
        ("Rusia", "Iran"),      ("Rusia", "Assad Syria"),
        ("China", "Iran"),      ("Qatar", "Hamas"),
        ("Qatar", "Iran"),      ("Arabia S.", "Israel"),
        ("OTAN", "Israel"),
    ]

    # Construir traces
    edge_x, edge_y = [], []
    for e in edges:
        n1 = next((n for n in nodos if n[0] == e[0]), None)
        n2 = next((n for n in nodos if n[0] == e[1]), None)
        if n1 and n2:
            edge_x += [n1[1], n2[1], None]
            edge_y += [n1[2], n2[2], None]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(color="#2a1518", width=1.2),
        hoverinfo="none", showlegend=False,
    ))

    for camp, color in [
        ("Iran",    "#ff3300"), ("Israel", "#4488ff"),
        ("EEUU",    "#aaaaaa"), ("Otros",  "#888844"),
    ]:
        camp_nodos = [n for n in nodos if (
            (camp == "Iran"   and n[3] in ["#ff3300","#ff4400","#ff5500","#ff6600","#ff7700","#cc4400"]) or
            (camp == "Israel" and n[3] in ["#4488ff","#5599ff","#6699ff","#77aaff"]) or
            (camp == "EEUU"   and n[3] in ["#aaaaaa","#888888","#999999"]) or
            (camp == "Otros"  and n[3] in ["#cc8800","#cc4400","#44ccaa","#ffcc00","#888844"])
        )]
        if not camp_nodos: continue
        fig.add_trace(go.Scatter(
            x=[n[1] for n in camp_nodos],
            y=[n[2] for n in camp_nodos],
            mode="markers+text",
            name=camp,
            marker=dict(
                size=[n[4] for n in camp_nodos],
                color=[n[3] for n in camp_nodos],
                line=dict(color="#08050a", width=1.5),
            ),
            text=[n[0] for n in camp_nodos],
            textposition="top center",
            textfont=dict(size=9, color=color),
            hovertemplate="<b>%{text}</b><br>%{customdata}<extra></extra>",
            customdata=[n[5] for n in camp_nodos],
        ))

    fig.update_layout(
        height=520,
        paper_bgcolor="#08050a", plot_bgcolor="#08050a",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        legend=dict(font=dict(color="#cc8844", size=10), bgcolor="#0f0a12",
                   bordercolor="#2a1518"),
        margin=dict(t=10, b=10, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Fichas de actores clave
    st.subheader("👤 Actores Clave")
    actores = [
        ("Iran",          "actor-side-iran",   "Khamenei / Pezeshkian",  "Líder Supremo · Presidente",     "Estado patrocinador proxies. Programa nuclear avanzado."),
        ("IRGC",          "actor-side-iran",   "Gen. Salami",            "Comandante en Jefe IRGC",         "Operaciones extraterritoriales · Fuerza Quds · Proxies"),
        ("Hezbollah",     "actor-side-proxy",  "Hassan Nasrallah †",     "Secretario Gral. (fallecido)",    "~150.000 cohetes · Sur Líbano · Financiado por Iran"),
        ("Hamas",         "actor-side-proxy",  "Yahya Sinwar †",         "Líder político (fallecido)",      "Gaza. Detonante 7-Oct-2023. Apoyo Iran/Qatar"),
        ("Houthi",        "actor-side-proxy",  "Abdul-Malik al-Houthi",  "Líder Houthi / Ansar Allah",      "Ataques Mar Rojo · Drones/misiles · Yemen"),
        ("Israel",        "actor-side-israel", "Benjamin Netanyahu",     "Primer Ministro",                 "Operaciones preventivas · IDF · Mossad"),
        ("IDF",           "actor-side-israel", "Herzi Halevi",           "Jefe Estado Mayor",               "Operaciones multidominio · Iron Dome · Arrow-3"),
        ("EEUU",          "actor-side-global", "Biden / Trump",          "Administración",                  "CENTCOM · USS Gerald Ford · Patriot en región"),
        ("Rusia",         "actor-side-global", "Putin",                  "Presidente",                      "S-400 a Iran · Apoyo Assad · Relación pragmática"),
        ("China",         "actor-side-global", "Xi Jinping",             "Presidente",                      "Mayor comprador petróleo iraní · Mediador Saudi-Iran"),
    ]
    cols = st.columns(2)
    for i, (nombre, side, lider, rol, desc) in enumerate(actores):
        with cols[i % 2]:
            st.markdown(
                f"<div class='actor-card {side}'>"
                f"<div class='actor-name'>{nombre}</div>"
                f"<div class='actor-role'>{lider} · <i>{rol}</i></div>"
                f"<div style='color:#998877;font-size:0.88em;margin-top:4px;'>{desc}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )


# ─── TAB 4: NUCLEAR ──────────────────────────────────────────────
def render_nuclear(vectores):
    st.subheader("⚛️ Nuclear & Armamento")
    v_nuc = next((v for v in vectores if v["key"] == "Nuclear"), None)
    if v_nuc:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.plotly_chart(make_gauge(v_nuc["score"], "Nuclear", 160),
                           use_container_width=True, config={"displayModeBar": False})
        with col2:
            st.markdown("""
            **Estado del programa nuclear iraní (estimación AIEA/FAS 2025-2026)**

            - Enriquecimiento al **60%** (umbral arma: 90%)
            - Tiempo de ruptura estimado: **~2-4 semanas** (desde 60% a 90%)
            - Natanz: ~20.000 centrifugadoras IR-1 + IR-6
            - Fordow: instalación subterránea — resistente a bombardeo convencional
            - Stock 60%: ~200 kg (suficiente para ~3-4 dispositivos si se enriquece a 90%)
            """)

    st.divider()

    # Timeline nuclear
    st.subheader("📅 Timeline Nuclear Iran")
    eventos_nuc = [
        (2002, "Revelación instalaciones Natanz y Arak por oposición iraní"),
        (2006, "Inicio enriquecimiento 3.5%. Primeras sanciones CSONU"),
        (2015, "JCPOA firmado. Límite enriquecimiento 3.67%. Levantamiento sanciones"),
        (2018, "Trump retira EEUU del JCPOA. Iran reinicia enriquecimiento"),
        (2020, "Asesinato Fakhrizadeh (científico nuclear). Natanz saboteado"),
        (2021, "Iran alcanza 60% enriquecimiento. Ruptura JCPOA"),
        (2023, "Stock 60% supera 200 kg. Breakout <1 mes estimado"),
        (2024, "Intercambio misiles Iran-Israel directo. Natanz posible objetivo"),
        (2025, "AIEA reporta obstrucción inspecciones. Stock 60% ~200-250 kg"),
        (2026, "Negociaciones JCPOA2 estancadas. Presión militar creciente"),
    ]
    df_nuc = pd.DataFrame(eventos_nuc, columns=["Año", "Evento"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_nuc["Año"], y=[1]*len(df_nuc),
        mode="markers+text",
        marker=dict(size=14, color="#ff4400",
                   line=dict(color="#ff8800", width=2)),
        text=df_nuc["Año"].astype(str),
        textposition="top center",
        textfont=dict(color="#ff8800", size=9),
        hovertemplate="<b>%{x}</b><br>%{customdata}<extra></extra>",
        customdata=df_nuc["Evento"],
        showlegend=False,
    ))
    fig.add_hline(y=1, line_color="#2a1518", line_width=1)
    fig.update_layout(
        height=150, paper_bgcolor="#08050a", plot_bgcolor="#08050a",
        xaxis=dict(showgrid=False, color="#775544"),
        yaxis=dict(showgrid=False, showticklabels=False, range=[0.5, 2]),
        margin=dict(t=20, b=20, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    for año, evento in reversed(eventos_nuc[-5:]):
        st.markdown(
            f"<div class='alert-warn'>📅 <b>{año}</b> — {evento}</div>",
            unsafe_allow_html=True,
        )

    # Capacidades militares comparadas
    st.divider()
    st.subheader("⚔️ Capacidades Militares Comparadas")
    categorias = ["Misiles balísticos", "Drones", "Defensa antiaérea",
                  "Ciberguerra", "Proxies/asimetría", "Fuerza naval"]
    iran_vals   = [80, 85, 55, 70, 95, 45]
    israel_vals = [75, 70, 95, 88, 30, 65]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=iran_vals, theta=categorias, fill="toself",
        name="Iran", line_color="#ff3300", fillcolor="rgba(255,51,0,0.15)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=israel_vals, theta=categorias, fill="toself",
        name="Israel", line_color="#4488ff", fillcolor="rgba(68,136,255,0.15)",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#0f0a12",
            radialaxis=dict(visible=True, range=[0,100], color="#775544",
                          gridcolor="#2a1518"),
            angularaxis=dict(color="#cc8844", gridcolor="#2a1518"),
        ),
        height=380, paper_bgcolor="#08050a",
        legend=dict(font=dict(color="#cc8844"), bgcolor="#0f0a12"),
        margin=dict(t=20, b=20, l=40, r=40),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ─── TAB 5: ENERGIA & HORMUZ ─────────────────────────────────────
def render_energia(vectores, df_history):
    st.subheader("🛢 Energía & Estrecho de Hormuz")
    v_en = next((v for v in vectores if v["key"] == "Energia_Hormuz"), None)

    col1, col2, col3 = st.columns(3)
    with col1:
        if v_en:
            st.plotly_chart(make_gauge(v_en["score"], "Energia/Hormuz", 160),
                           use_container_width=True, config={"displayModeBar": False})
    with col2:
        oil = fetch_oil_price()
        if oil["ok"]:
            delta_color = "#ff3300" if oil["delta"] > 0 else "#44ff88"
            st.metric("Brent Crude (RT)", f"${oil['brent']}", f"{oil['delta']:+.2f}")
        st.caption("Datos Yahoo Finance (~15min diferido)")
    with col3:
        st.markdown("""
        **Estado Estrecho Hormuz**

        🔴 **Tráfico:** 21M bbl/día (~20% global)
        🟠 **Riesgo cierre:** ALTO
        🟡 **Alternativa:** Oleoducto IPSA (Arabia S.)
        """)

    st.divider()
    st.subheader("🗺 Infraestructura Energética Regional")

    infra = [
        dict(lat=27.2, lon=56.3, label="Estrecho Hormuz", tipo="Chokepoint", val=95),
        dict(lat=12.6, lon=43.5, label="Bab el-Mandeb",   tipo="Chokepoint", val=82),
        dict(lat=30.0, lon=32.5, label="Canal Suez",       tipo="Chokepoint", val=72),
        dict(lat=30.4, lon=48.3, label="Campo Abadán",     tipo="Campo",      val=75),
        dict(lat=32.5, lon=49.7, label="Campo Ahwaz",      tipo="Campo",      val=70),
        dict(lat=27.8, lon=53.0, label="Campo Pars Sur",   tipo="GasField",   val=88),
        dict(lat=26.4, lon=50.1, label="Ras Tanura (AS)",  tipo="Terminal",   val=80),
        dict(lat=24.4, lon=54.4, label="Fujairah Terminal",tipo="Terminal",   val=70),
        dict(lat=29.4, lon=47.9, label="Mina Ahmadi (KW)", tipo="Terminal",   val=65),
        dict(lat=23.6, lon=58.5, label="Muscat",           tipo="Terminal",   val=55),
    ]
    df_inf = pd.DataFrame(infra)
    color_inf = {"Chokepoint": "#ff3300", "Campo": "#ffcc00",
                 "GasField": "#44ccff", "Terminal": "#ff8800"}
    fig = go.Figure()
    for tipo, color in color_inf.items():
        df_t = df_inf[df_inf["tipo"] == tipo]
        if df_t.empty: continue
        fig.add_trace(go.Scattergeo(
            lat=df_t["lat"], lon=df_t["lon"],
            mode="markers+text", name=tipo,
            marker=dict(size=df_t["val"]/5 + 8, color=color, opacity=0.8,
                       line=dict(color="#000", width=0.5)),
            text=df_t["label"],
            textposition="top center",
            textfont=dict(size=8, color=color),
            hovertemplate="<b>%{text}</b><br>Riesgo: %{customdata}%<extra></extra>",
            customdata=df_t["val"],
        ))
    fig.update_layout(
        geo=dict(
            scope="world", center=dict(lat=27, lon=52), projection_scale=5,
            showland=True, landcolor="#0a0810",
            showocean=True, oceancolor="#05080f",
            showcountries=True, countrycolor="#1a1520",
            bgcolor="#08050a",
        ),
        height=420, paper_bgcolor="#08050a",
        legend=dict(font=dict(color="#cc8844", size=9), bgcolor="#0f0a12"),
        margin=dict(t=10, b=10, l=0, r=0),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Correlación tensión-petróleo si hay histórico
    if not df_history.empty:
        st.subheader("📈 Tensión Energía vs Histórico")
        df_e = df_history[df_history["vector"] == "Energia_Hormuz"].copy()
        if not df_e.empty:
            df_e_90 = df_e[df_e["dt"] >= pd.Timestamp.now() - pd.Timedelta(days=90)]
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=df_e_90["dt"], y=df_e_90["score"],
                mode="lines", fill="tozeroy",
                line=dict(color="#ffcc00", width=2),
                fillcolor="rgba(255,204,0,0.08)",
                name="Score Energía/Hormuz",
            ))
            fig2.add_hline(y=70, line_dash="dot", line_color="#ff3300",
                          annotation_text="RIESGO CIERRE", opacity=0.5)
            fig2.update_layout(
                height=220, paper_bgcolor="#08050a", plot_bgcolor="#0a0508",
                font_color="#cc8844",
                xaxis=dict(gridcolor="#1a0f1a"),
                yaxis=dict(gridcolor="#1a0f1a", range=[0, 105]),
                margin=dict(t=20, b=20, l=30, r=10),
            )
            st.plotly_chart(fig2, use_container_width=True,
                           config={"displayModeBar": False})


# ─── TAB 6: ECONOMIA & SANCIONES ────────────────────────────────
def render_economia(vectores, df_history):
    st.subheader("💰 Economía & Sanciones")
    v_ec = next((v for v in vectores if v["key"] == "Sanciones_Economia"), None)

    col1, col2 = st.columns([1, 2])
    with col1:
        if v_ec:
            st.plotly_chart(make_gauge(v_ec["score"], "Sanciones", 160),
                           use_container_width=True, config={"displayModeBar": False})
    with col2:
        st.markdown("""
        **Estado sanciones sobre Iran (2026)**

        | Régimen | Estado | Impacto |
        |---------|--------|---------|
        | Sanciones petróleo EEUU | 🔴 Activo | -50% exportaciones |
        | Exclusión SWIFT | 🔴 Activo | Bloqueo pagos internacionales |
        | Sanciones nucleares UE | 🔴 Activo | Comercio restringido |
        | Congelación activos | 🔴 Activo | ~$100B bloqueados |
        | Sanciones IRGC | 🔴 Activo | Entidades y personas |
        | Acuerdo gas Qatar | 🟡 Parcial | Canal alternativo |
        """)

    st.divider()

    # Timeline sanciones
    st.subheader("📅 Timeline Sanciones y Acuerdos")
    eventos_san = [
        (1979, "Primera ronda sanciones EEUU tras revolución islámica"),
        (1996, "ILSA — Sanciones inversión energía Iran/Libia"),
        (2006, "CSONU Res.1737 — Sanciones nucleares multilaterales"),
        (2012, "Exclusión Iran del sistema SWIFT. Colapso rial"),
        (2015, "JCPOA — Levantamiento parcial sanciones a cambio de límites nucleares"),
        (2018, "Trump retira EEUU del JCPOA. 'Máxima presión' — rial -70%"),
        (2020, "Reimposición sanciones ONU. Embargo armas"),
        (2023, "Biden desbloquea $6B congelados (Qatar). Liberación rehenes"),
        (2024, "Nuevas sanciones post-ataque misiles directo Iran-Israel"),
        (2025, "Sanciones envío drones a Rusia. Presión máxima renovada"),
    ]
    for año, evento in reversed(eventos_san[-6:]):
        color = "#ff4400" if año >= 2023 else "#885533"
        st.markdown(
            f"<div style='border-left:3px solid {color};padding:6px 12px;"
            f"margin:3px 0;font-family:Share Tech Mono;font-size:0.8em;'>"
            f"<span style='color:{color};'>{año}</span> "
            f"<span style='color:#cc9977;'>—</span> "
            f"<span style='color:#aa8866;'>{evento}</span></div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # Radar impacto económico
    st.subheader("📊 Impacto Económico de Sanciones")
    cats = ["Exportaciones petróleo", "Acceso mercados financieros",
            "Comercio exterior", "Inversión extranjera",
            "Tecnología importada", "Tipo de cambio (rial)"]
    antes_jcpoa = [40, 30, 45, 35, 40, 50]  # bajo JCPOA (mejor)
    actual       = [20, 10, 25, 15, 20, 15]  # actual bajo sanciones máximas
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=antes_jcpoa, theta=cats, fill="toself", name="Bajo JCPOA (2016)",
        line_color="#44ff88", fillcolor="rgba(68,255,136,0.1)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=actual, theta=cats, fill="toself", name="Actual (2026)",
        line_color="#ff3300", fillcolor="rgba(255,51,0,0.15)",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#0f0a12",
            radialaxis=dict(visible=True, range=[0,100], color="#775544",
                          gridcolor="#2a1518"),
            angularaxis=dict(color="#cc8844", gridcolor="#2a1518"),
        ),
        height=350, paper_bgcolor="#08050a",
        legend=dict(font=dict(color="#cc8844"), bgcolor="#0f0a12"),
        margin=dict(t=20, b=20, l=40, r=40),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ─── TAB 7: IMPACTO GLOBAL ───────────────────────────────────────
def render_global(vectores, df_history):
    st.subheader("🌍 Impacto Global — Posición de Potencias")
    v_gl = next((v for v in vectores if v["key"] == "Posicion_Global"), None)
    if v_gl:
        c1, _ = st.columns([1, 3])
        with c1:
            st.plotly_chart(make_gauge(v_gl["score"], "Posición Global", 160),
                           use_container_width=True, config={"displayModeBar": False})

    st.divider()

    # Radar posición potencias
    st.subheader("📡 Posición de Potencias en el Conflicto")
    dims = ["Apoyo Iran", "Apoyo Israel", "Interés energético",
            "Exposición militar", "Mediación", "Sanciones apoyo"]
    potencias = {
        "EEUU":    [10, 90, 70, 85, 30, 90],
        "Rusia":   [70, 5,  80, 20, 10, 5],
        "China":   [60, 10, 95, 10, 40, 5],
        "UE":      [20, 65, 60, 40, 60, 75],
        "India":   [40, 30, 85, 10, 45, 15],
        "Arabia S":[20, 55, 90, 30, 50, 30],
    }
    colores = {"EEUU":"#aaaaaa","Rusia":"#cc8800","China":"#cc4400",
               "UE":"#4488ff","India":"#ffcc00","Arabia S":"#ffaa44"}
    fig = go.Figure()
    for pais, vals in potencias.items():
        fig.add_trace(go.Scatterpolar(
            r=vals, theta=dims, fill="toself", name=pais,
            line_color=colores[pais],
            fillcolor=f"rgba{tuple(int(colores[pais][i:i+2],16) for i in (1,3,5))+(0.08,)}",
        ))
    fig.update_layout(
        polar=dict(
            bgcolor="#0f0a12",
            radialaxis=dict(visible=True, range=[0,100], color="#775544",
                          gridcolor="#2a1518"),
            angularaxis=dict(color="#cc8844", gridcolor="#2a1518"),
        ),
        height=420, paper_bgcolor="#08050a",
        legend=dict(font=dict(color="#cc8844", size=10), bgcolor="#0f0a12"),
        margin=dict(t=20, b=20, l=40, r=40),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Tabla de posiciones
    st.subheader("📋 Posición Declarada y Acciones")
    posiciones = [
        ("EEUU",       "Pro-Israel",        "Portaaviones región · Patriot · Veto ONU",      "🔴 Alta"),
        ("Rusia",      "Neutral / Pro-Iran", "S-400 · Veto sanciones CSONU · Drones compartidos","🟠 Media"),
        ("China",      "Neutral / Pro-Iran", "Mayor comprador petróleo · Mediación Saudi-Iran", "🟡 Media"),
        ("UE",         "Pro-Israel (matiz)", "Sanciones Iran · Apoyo humanitario Gaza",        "🟡 Media"),
        ("India",      "Neutral",            "Comprador petróleo Iran con descuento",          "🟢 Baja"),
        ("Arabia S.",  "Normalización IS.",  "Acuerdo Abraham · Mediación potencial",          "🟡 Media"),
        ("Turquía",    "Ambigua",            "OTAN pero crítica con Israel · Canal diplomático","🟡 Media"),
        ("Qatar",      "Mediador",           "Canal Hamas · Relaciones Iran · Gas a Europa",   "🟢 Baja"),
    ]
    df_pos = pd.DataFrame(posiciones, columns=["País", "Posición", "Acciones", "Riesgo implicación"])
    st.dataframe(df_pos, use_container_width=True, hide_index=True)

    # Escenarios de escalada
    st.divider()
    st.subheader("🔮 Escenarios de Escalada")
    escenarios = [
        ("🟢 Desescalada",    25, "Acuerdo JCPOA2 · Cese hostilidades Gaza · Hormuz estable"),
        ("🟡 Tensión crónica",40, "Status quo · Ataques proxies ocasionales · Sanciones activas"),
        ("🟠 Escalada regional",25,"Houthi bloquea Hormuz · Iran-Israel intercambio misiles amplio"),
        ("🔴 Guerra regional", 10, "EEUU intervención · Iran cierra Hormuz · Crisis energética global"),
    ]
    for emoji_label, prob, desc in escenarios:
        color = "#44ff88" if "Des" in emoji_label else "#ffaa00" if "crónica" in emoji_label else "#ff6600" if "regional" in emoji_label else "#ff2200"
        st.markdown(
            f"<div style='background:#0f0a12;border-left:4px solid {color};"
            f"padding:10px 16px;border-radius:4px;margin:5px 0;"
            f"font-family:Share Tech Mono;font-size:0.82em;'>"
            f"<span style='color:{color};font-weight:bold;'>{emoji_label}</span> "
            f"<span style='color:#775544;'>— Prob. estimada: {prob}%</span><br>"
            f"<span style='color:#998877;'>{desc}</span></div>",
            unsafe_allow_html=True,
        )


# ─── TAB 8: DOCS ─────────────────────────────────────────────────
def render_docs():
    st.markdown("""
    <div style='background:#100508;border:1px solid #2a0f0a;border-left:5px solid #ff3300;
                border-radius:6px;padding:1.2rem 1.5rem;margin-bottom:1.2rem;
                font-family:Share Tech Mono;'>
        <span style='color:#ff3300;font-size:1.1em;font-weight:bold;'>
            📖 SIEG Iran — Documentation Center
        </span><br>
        <span style='color:#775544;font-size:0.82em;'>
            Documentacion integrada · Sincronizada con GitHub
        </span>
    </div>
    """, unsafe_allow_html=True)

    d1, d2, d3 = st.tabs(["📘 Guia de Usuario", "🔧 Referencia Tecnica", "🌐 Web & Descarga"])

    GITHUB_RAW  = "https://raw.githubusercontent.com/mcasrom/SIEG-Core/main"
    GITHUB_IRAN = "https://github.com/mcasrom/SIEG-Iran"
    PAGES_URL   = "https://mcasrom.github.io/SIEG-Core"
    PDF_URL     = f"{GITHUB_RAW}/docs/user_guide.pdf"
    MD_URL      = f"{GITHUB_RAW}/docs/technical_reference.md"

    with d1:
        st.markdown("### 📘 Guia de Usuario / User Guide")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(
                f"""<iframe src="{PDF_URL}" width="100%" height="700"
                style="border:1px solid #2a1518;border-radius:6px;background:#0a0a0a;">
                </iframe>""",
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown("**Acceso directo:**")
            st.markdown(f"[⬇ Descargar PDF]({PDF_URL})")
            st.markdown(f"[🌐 Ver en GitHub](https://github.com/mcasrom/SIEG-Core/blob/main/docs/user_guide.pdf)")

    with d2:
        st.markdown("### 🔧 Referencia Tecnica")
        try:
            import requests as _req
            r = _req.get(MD_URL, timeout=8)
            if r.status_code == 200:
                st.markdown(r.text)
            else:
                st.markdown(f"[Ver en GitHub](https://github.com/mcasrom/SIEG-Core/blob/main/docs/technical_reference.md)")
        except Exception:
            st.markdown(f"[Ver en GitHub](https://github.com/mcasrom/SIEG-Core/blob/main/docs/technical_reference.md)")

    with d3:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"[🌐 Web documentacion]({PAGES_URL})")
            st.markdown(f"[📁 Repo SIEG Iran]({GITHUB_IRAN})")
        with col_b:
            st.markdown(f"[📘 user_guide.pdf]({PDF_URL})")
            st.markdown(f"[🔧 technical_reference.md]({MD_URL})")
            st.markdown("**Proyectos SIEG:**")
            st.markdown("[🛡 SIEG Core](https://sieg-intelligence-radar.streamlit.app)")
            st.markdown("[🌐 SIEG Atlas](https://sieg-atlas-intelligence.streamlit.app)")


# ─── MAIN ────────────────────────────────────────────────────────
def main():
    vectores = load_vectores()
    summary  = load_crisis_summary()
    df_hist  = load_history()

    render_sidebar(vectores, summary)

    (tab_overview, tab_teatro, tab_alianzas, tab_nuclear,
     tab_energia, tab_economia, tab_global, tab_docs) = st.tabs([
        "🔴 Crisis Overview", "🗺 Teatro Operaciones", "🕸 Red Alianzas",
        "⚛️ Nuclear & Armamento", "🛢 Energía & Hormuz",
        "💰 Economía & Sanciones", "🌍 Impacto Global", "📖 Docs"
    ])

    with tab_overview:  render_overview(vectores, summary, df_hist)
    with tab_teatro:    render_teatro()
    with tab_alianzas:  render_alianzas()
    with tab_nuclear:   render_nuclear(vectores)
    with tab_energia:   render_energia(vectores, df_hist)
    with tab_economia:  render_economia(vectores, df_hist)
    with tab_global:    render_global(vectores, df_hist)
    with tab_docs:      render_docs()

    st.markdown(f"""
    <div class='iran-footer'>
        🔴 S.I.E.G. Iran Crisis Room {APP_VERSION} &nbsp;&middot;&nbsp;
        Scanner {SCANNER_VERSION} &nbsp;&middot;&nbsp;
        Iran-Israel Conflict Intelligence<br>
        &copy; {BUILD_DATE} <b>M. Castillo</b> &nbsp;&middot;&nbsp;
        <a href='mailto:mybloggingnotes@gmail.com'>mybloggingnotes@gmail.com</a>
        &nbsp;&middot;&nbsp; Nodo: Odroid-C2 / DietPi
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
