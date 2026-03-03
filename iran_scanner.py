#!/usr/bin/env python3
"""
S.I.E.G. Iran — Scanner V1.0
8 vectores: Conflicto_Directo, Proxies_Regionales, Nuclear,
            Energia_Hormuz, Teatro_Regional, Posicion_Global,
            Sanciones_Economia, Diplomatico
Autolearning 3 capas. Ciclo recomendado: cada 60min offset :45
"""

import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path

import requests
import xml.etree.ElementTree as ET

# ─── CONFIG ──────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).resolve().parent
DATA_DIR      = BASE_DIR / "data" / "live"
MAPA_FUENTES  = BASE_DIR / "mapa_iran.txt"
HISTORY_CSV   = DATA_DIR / "history_iran.csv"
LEARNED_FILE  = DATA_DIR / "iran_learned_sources.json"
FLASHES_FILE  = DATA_DIR / "iran_flashes.json"

RSS_ITEMS     = 25
TIMEOUT       = 10
VERSION       = "V1.1"
MIN_NOTICIAS  = 50
FLASH_TTL_H   = 48          # horas que permanece un flash visible
FLASH_SCORE   = 75          # score mínimo de oracion para generar flash
FLASH_MAX     = 20          # máximo flashes almacenados

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("SIEG-Iran")

# ─── VECTORES Y SUELOS ───────────────────────────────────────────
VECTORES = [
    "Conflicto_Directo", "Proxies_Regionales", "Nuclear",
    "Energia_Hormuz", "Teatro_Regional", "Posicion_Global",
    "Sanciones_Economia", "Diplomatico",
]

SUELOS_BASE = {
    "Conflicto_Directo":  72,
    "Proxies_Regionales": 65,
    "Nuclear":            58,
    "Energia_Hormuz":     55,
    "Teatro_Regional":    62,
    "Posicion_Global":    45,
    "Sanciones_Economia": 50,
    "Diplomatico":        35,
}

# Pesos para calcular el nivel de crisis global (0-100)
PESOS_CRISIS = {
    "Conflicto_Directo":  0.25,
    "Proxies_Regionales": 0.18,
    "Nuclear":            0.20,
    "Energia_Hormuz":     0.12,
    "Teatro_Regional":    0.10,
    "Posicion_Global":    0.05,
    "Sanciones_Economia": 0.05,
    "Diplomatico":        0.05,
}

# ─── VOCABULARIO ─────────────────────────────────────────────────
KINETIC_ALTO = [
    "airstrike", "airstrikes", "missile strike", "missile attack",
    "bombing", "bombed", "ballistic missile", "drone strike",
    "drone attack", "struck", "targeted strike", "air raid",
    "killed", "destroyed", "intercepted", "launched missiles",
    "rocket attack", "artillery", "shelling", "ground offensive",
    "naval strike", "warship",
]
KINETIC_MEDIO = [
    "attack", "attacked", "military operation", "escalation",
    "retaliation", "retaliatory", "under fire", "explosion",
    "blast", "troops deployed", "military buildup", "skirmish",
    "border clash", "armed forces", "combat",
]
KINETIC_BAJO = [
    "tension", "warning", "threatens", "sanctions", "provocation",
    "military exercise", "drills", "mobilize", "alert",
    "confrontation", "standoff",
]
NUCLEAR_TERMS = [
    "nuclear", "uranium enrichment", "centrifuge", "natanz", "fordow",
    "iaea", "nuclear weapon", "bomb", "warhead", "enriched",
    "nuclear deal", "jcpoa", "breakout", "proliferation",
]
DEESCALATION = [
    "ceasefire", "peace talks", "negotiations", "truce",
    "diplomatic solution", "agreement", "summit", "mediation",
]
CRITICAL = [
    "nuclear warhead", "tactical nuke", "dirty bomb", "radiological",
    "chemical weapon", "mass casualty", "full scale war",
    "declaration of war",
]

# Aliases por vector para detección contextual
VECTOR_ALIASES = {
    "Conflicto_Directo":  [
        "iran", "israel", "idf", "irgc", "mossad", "tehran", "tel aviv",
        "netanyahu", "khamenei", "iron dome", "persian", "israeli",
    ],
    "Proxies_Regionales": [
        "hezbollah", "houthi", "hamas", "pij", "plo", "pmf", "kataib",
        "fatemiyoun", "zeinabiyoun", "ansar allah", "islamic jihad",
        "popular mobilization", "proxy", "militia", "backed",
    ],
    "Nuclear": [
        "nuclear", "uranium", "enrichment", "natanz", "fordow", "iaea",
        "centrifuge", "jcpoa", "breakout", "proliferation", "atomic",
    ],
    "Energia_Hormuz": [
        "hormuz", "strait", "oil", "tanker", "brent", "crude", "opec",
        "pipeline", "gas", "lng", "energy", "petroleum", "barrel",
    ],
    "Teatro_Regional": [
        "lebanon", "syria", "iraq", "yemen", "gaza", "west bank",
        "beirut", "damascus", "baghdad", "sanaa", "ramallah",
    ],
    "Posicion_Global": [
        "united states", "russia", "china", "nato", "pentagon",
        "centcom", "india", "eu", "european union", "un security",
    ],
    "Sanciones_Economia": [
        "sanctions", "embargo", "rial", "swift", "freeze", "assets",
        "lloyd", "insurance", "export", "import", "trade", "economy",
    ],
    "Diplomatico": [
        "talks", "negotiations", "mediator", "qatar", "oman", "un",
        "diplomat", "envoy", "agreement", "ceasefire", "deal",
    ],
}

# ─── FALLBACK SOURCES (Capa 2) ───────────────────────────────────
FALLBACK_SOURCES = {
    "Conflicto_Directo": [
        {"url": "https://www.haaretz.com/cmlink/1.4482668",        "cf": 0.8},
        {"url": "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml", "cf": 0.9},
        {"url": "https://www.washingtonpost.com/world/rss/",       "cf": 0.9},
        {"url": "https://www.reuters.com/rssFeed/worldNews",       "cf": 0.9},
    ],
    "Proxies_Regionales": [
        {"url": "https://www.middleeasteye.net/rss",               "cf": 0.7},
        {"url": "https://www.aljazeera.com/xml/rss/all.xml",       "cf": 0.7},
        {"url": "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml", "cf": 0.9},
        {"url": "https://www.reuters.com/rssFeed/worldNews",       "cf": 0.9},
    ],
    "Nuclear": [
        {"url": "https://www.iaea.org/feeds/topnews.xml",          "cf": 1.0},
        {"url": "https://thebulletin.org/feed/",                   "cf": 0.9},
        {"url": "https://www.armscontrol.org/rss.xml",             "cf": 1.0},
        {"url": "https://feeds.bbci.co.uk/news/world/rss.xml",     "cf": 0.9},
    ],
    "Energia_Hormuz": [
        {"url": "https://www.eia.gov/rss/latest_articles.xml",     "cf": 1.0},
        {"url": "https://www.gcaptain.com/feed/",                  "cf": 0.8},
        {"url": "https://feeds.bbci.co.uk/news/business/rss.xml",  "cf": 0.9},
        {"url": "https://www.reuters.com/rssFeed/businessNews",    "cf": 0.9},
    ],
    "Teatro_Regional": [
        {"url": "https://www.middleeasteye.net/rss",               "cf": 0.7},
        {"url": "https://www.aljazeera.com/xml/rss/all.xml",       "cf": 0.7},
        {"url": "https://rss.nytimes.com/services/xml/rss/nyt/MiddleEast.xml", "cf": 0.9},
        {"url": "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml", "cf": 0.9},
    ],
    "Posicion_Global": [
        {"url": "https://foreignpolicy.com/feed/",                 "cf": 0.9},
        {"url": "https://www.reuters.com/rssFeed/worldNews",       "cf": 0.9},
        {"url": "https://feeds.bbci.co.uk/news/world/rss.xml",     "cf": 0.9},
        {"url": "https://thediplomat.com/feed/",                   "cf": 0.8},
    ],
    "Sanciones_Economia": [
        {"url": "https://www.ft.com/rss/home",                     "cf": 0.9},
        {"url": "https://feeds.bbci.co.uk/news/business/rss.xml",  "cf": 0.9},
        {"url": "https://www.reuters.com/rssFeed/businessNews",    "cf": 0.9},
        {"url": "https://foreignpolicy.com/feed/",                 "cf": 0.9},
    ],
    "Diplomatico": [
        {"url": "https://foreignpolicy.com/feed/",                 "cf": 0.9},
        {"url": "https://thediplomat.com/feed/",                   "cf": 0.8},
        {"url": "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml", "cf": 0.9},
        {"url": "https://www.middleeasteye.net/rss",               "cf": 0.7},
    ],
}

GOOGLE_NEWS_QUERIES = {
    "Conflicto_Directo":  "iran+israel+attack+military+airstrike",
    "Proxies_Regionales": "hezbollah+houthi+hamas+iran+proxy+militia",
    "Nuclear":            "iran+nuclear+uranium+enrichment+iaea+natanz",
    "Energia_Hormuz":     "hormuz+strait+iran+oil+tanker+energy",
    "Teatro_Regional":    "iran+lebanon+syria+iraq+yemen+gaza+conflict",
    "Posicion_Global":    "iran+usa+russia+china+nato+geopolitics",
    "Sanciones_Economia": "iran+sanctions+embargo+economy+rial",
    "Diplomatico":        "iran+negotiations+diplomacy+deal+ceasefire",
}

# ─── CALIDAD ─────────────────────────────────────────────────────
def calcular_calidad(n: int, uso_fb: bool, uso_web: bool) -> dict:
    if n >= 80:   nivel, emoji, css = "VERDE",    "🟢", "green"
    elif n >= 60: nivel, emoji, css = "AZUL",     "🔵", "blue"
    elif n >= 40: nivel, emoji, css = "AMARILLO", "🟡", "yellow"
    elif n >= 20: nivel, emoji, css = "NARANJA",  "🟠", "orange"
    else:         nivel, emoji, css = "ROJO",     "🔴", "red"
    return {"nivel": nivel, "emoji": emoji, "css": css,
            "uso_fallback": uso_fb, "uso_web": uso_web}

# ─── FUENTES APRENDIDAS ──────────────────────────────────────────
def cargar_aprendidas() -> dict:
    try:
        return json.load(open(LEARNED_FILE)) if LEARNED_FILE.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}

def guardar_aprendidas(d: dict) -> None:
    try:
        json.dump(d, open(LEARNED_FILE, "w"), indent=2)
    except OSError as e:
        log.warning("No se pudo guardar fuentes aprendidas: %s", e)

# ─── SISTEMA DE FLASHES ──────────────────────────────────────────
# Palabras clave que elevan una noticia a FLASH URGENTE
FLASH_TRIGGERS = [
    # Cierre Hormuz / energía crítica
    "hormuz closed", "hormuz blocked", "hormuz closure",
    "strait closed", "oil embargo", "oil blockade",
    "pipeline attack", "pipeline explosion", "gas cut",
    # Ataques directos Iran-Israel
    "iran launches", "iran fires", "iran attacks",
    "israel strikes iran", "israel bombs iran",
    "idf strikes", "ballistic missile iran",
    "iran missile barrage", "mass missile attack",
    # Nuclear crítico
    "nuclear device", "nuclear test", "enriched to 90",
    "bomb-grade", "weaponize", "nuclear breakout",
    "iaea emergency", "iaea inspectors expelled",
    # Proxies crítico
    "hezbollah declares war", "full scale attack",
    "houthi closes", "red sea closed",
    "israel ground invasion", "iran declares war",
    # Ataques activos
    "shot down", "fighter jet downed", "warship sunk",
    "aircraft carrier", "drone swarm", "mass casualty",
    "hundreds killed", "city under fire",
]

FLASH_ICONOS = {
    "Conflicto_Directo":  "⚔️",
    "Proxies_Regionales": "🕸",
    "Nuclear":            "⚛️",
    "Energia_Hormuz":     "🛢",
    "Teatro_Regional":    "🗺",
    "Posicion_Global":    "🌍",
    "Sanciones_Economia": "💰",
    "Diplomatico":        "🕊",
}

def cargar_flashes() -> list:
    try:
        if FLASHES_FILE.exists():
            return json.load(open(FLASHES_FILE))
    except (OSError, json.JSONDecodeError):
        pass
    return []

def guardar_flashes(flashes: list) -> None:
    try:
        json.dump(flashes, open(FLASHES_FILE, "w"), indent=2, ensure_ascii=False)
    except OSError as e:
        log.warning("Error guardando flashes: %s", e)

def purgar_flashes_expirados(flashes: list, ahora: float) -> list:
    ttl_s = FLASH_TTL_H * 3600
    return [f for f in flashes if (ahora - f.get("ts", 0)) < ttl_s]

def extraer_flashes(noticias: list, vector: str, score_vector: int,
                    ahora: float) -> list:
    """
    Extrae titulares flash de las noticias del ciclo actual.
    Criterios:
      1. El score del vector es >= FLASH_SCORE, Y
      2. El titular contiene al menos uno de los FLASH_TRIGGERS
    Devuelve lista de dicts flash nuevos (sin duplicar existentes).
    """
    if score_vector < FLASH_SCORE:
        return []

    nuevos = []
    vistos = set()

    for n in noticias:
        texto = n.get("text", "").lower()
        # Extraer solo el titular (antes del primer espacio extra largo)
        titulo_raw = n.get("text", "").split("  ")[0].strip()
        titulo = titulo_raw[:140]  # truncar a 140 chars

        if not titulo or titulo in vistos:
            continue

        # Verificar si contiene trigger de flash
        trigger_hit = next((t for t in FLASH_TRIGGERS if t in texto), None)
        if not trigger_hit:
            continue

        vistos.add(titulo)
        nuevos.append({
            "ts":      ahora,
            "vector":  vector,
            "icono":   FLASH_ICONOS.get(vector, "🔴"),
            "titulo":  titulo,
            "trigger": trigger_hit,
            "score":   score_vector,
            "cf":      n.get("cf", 0.7),
        })

        if len(nuevos) >= 3:  # máximo 3 flashes por vector por ciclo
            break

    return nuevos

def actualizar_flashes(nuevos: list, existentes: list,
                       ahora: float) -> list:
    """Purga expirados, evita duplicados por titulo, limita a FLASH_MAX."""
    resultado = purgar_flashes_expirados(existentes, ahora)

    titulos_existentes = {f["titulo"] for f in resultado}
    for f in nuevos:
        if f["titulo"] not in titulos_existentes:
            resultado.append(f)
            titulos_existentes.add(f["titulo"])

    # Más recientes primero, máximo FLASH_MAX
    resultado.sort(key=lambda x: x["ts"], reverse=True)
    return resultado[:FLASH_MAX]

# ─── FETCH RSS ───────────────────────────────────────────────────
def fetch_rss(fuentes: list, vector: str) -> tuple:
    headers  = {"User-Agent": "Mozilla/5.0 (compatible; SIEG-Iran/1.0)"}
    noticias = []
    activas  = 0
    for f in fuentes:
        try:
            r = requests.get(f["url"], headers=headers, timeout=TIMEOUT)
            r.raise_for_status()
            root  = ET.fromstring(r.content)
            items = root.findall(".//item")[:RSS_ITEMS]
            if items:
                activas += 1
            for item in items:
                t = item.find("title")
                d = item.find("description")
                title = (t.text or "") if t is not None else ""
                desc  = (d.text or "") if d is not None else ""
                noticias.append({
                    "text": f"{title} {re.sub(r'<[^>]+>', ' ', desc)}",
                    "cf":   f["cf"],
                })
        except (requests.RequestException, ET.ParseError):
            pass
    return noticias, activas

# ─── AUTOLEARNING 3 CAPAS ────────────────────────────────────────
def fetch_con_autolearning(vector: str, primarias: list,
                           aprendidas: dict) -> tuple:
    uso_fb = uso_web = False

    noticias, activas = fetch_rss(primarias, vector)

    if len(noticias) < MIN_NOTICIAS:
        uso_fb = True
        fb     = FALLBACK_SOURCES.get(vector, [])
        prev   = [{"url": u, "cf": 0.7} for u in aprendidas.get(vector, [])]
        n2, a2 = fetch_rss(fb + prev, vector)
        noticias += n2; activas += a2

    if len(noticias) < MIN_NOTICIAS:
        uso_web = True
        q   = GOOGLE_NEWS_QUERIES.get(vector, vector.lower())
        url = f"https://news.google.com/rss/search?q={q}&hl=en&gl=US&ceid=US:en"
        n3, a3 = fetch_rss([{"url": url, "cf": 0.6}], vector)
        noticias += n3; activas += a3
        if n3:
            aprendidas.setdefault(vector, [])
            if url not in aprendidas[vector]:
                aprendidas[vector].append(url)

    calidad = calcular_calidad(len(noticias), uso_fb, uso_web)
    return noticias, activas, calidad, aprendidas

# ─── SCORING ─────────────────────────────────────────────────────
def _score_oracion(oracion: str, vector: str) -> float:
    for w in CRITICAL:
        if w in oracion: return 95.0

    for w in NUCLEAR_TERMS:
        if w in oracion and "nuclear" in vector.lower():
            return 80.0

    deesc = sum(1 for w in DEESCALATION if w in oracion)
    if deesc >= 2: return 12.0

    aliases = VECTOR_ALIASES.get(vector, [])
    presente = any(a in oracion for a in aliases)

    ha = sum(1 for w in KINETIC_ALTO  if w in oracion)
    hm = sum(1 for w in KINETIC_MEDIO if w in oracion)
    hb = sum(1 for w in KINETIC_BAJO  if w in oracion)

    if ha + hm + hb == 0: return 18.0

    score = (ha * 24) + (hm * 13) + (hb * 5)
    if presente:  score *= 1.40
    if deesc == 1: score *= 0.75
    return min(92.0, score)

def score_noticia(texto: str, vector: str, cf: float) -> tuple:
    ors = re.split(r"[.!?;|\n]+", texto.lower())
    ss  = [_score_oracion(o, vector) for o in ors if o.strip()]
    if not ss: return 18.0 * cf, cf
    ss.sort(reverse=True)
    return ss[max(0, len(ss) // 4)] * cf, cf

def calcular_triaje(noticias: list, vector: str,
                    old_score: float, historico: list) -> tuple:
    if not noticias:
        return int(old_score), False

    sp, pw, scf = [], [], {}
    for n in noticias:
        s, cf = score_noticia(n["text"], vector, n["cf"])
        sp.append(s); pw.append(cf)
        scf.setdefault(str(round(cf, 1)), []).append(s / cf if cf > 0 else 0)

    tcf    = sum(pw)
    bruto  = sum(sp) / tcf if tcf > 0 else 18.0
    base   = SUELOS_BASE.get(vector, 20)
    if len(historico) >= 5:
        media = sum(historico[-10:]) / len(historico[-10:])
        suelo = max(base, min(media * 0.6, base + 15))
    else:
        suelo = base

    score_s = max(bruto, suelo)
    final   = (old_score * 0.65 + score_s * 0.35) if score_s < old_score else score_s

    # Disonancia
    est = []; alt = []
    for k, v in scf.items():
        (est if float(k) >= 0.8 else alt).extend(v)
    dison = bool(est and alt and abs(sum(est)/len(est) - sum(alt)/len(alt)) > 35)

    return max(10, min(100, int(final))), dison

# ─── HISTORICO ───────────────────────────────────────────────────
def cargar_historico(vector: str) -> list:
    if not HISTORY_CSV.exists(): return []
    scores = []
    try:
        with open(HISTORY_CSV) as f:
            for l in f:
                p = l.strip().split(",")
                if len(p) == 3 and p[1].strip() == vector:
                    try: scores.append(float(p[2]))
                    except ValueError: pass
    except OSError: pass
    return scores[-30:]

def guardar_historico(vector: str, score: int, ts: float) -> None:
    try:
        with open(HISTORY_CSV, "a") as f:
            f.write(f"{ts},{vector},{score}\n")
    except OSError as e:
        log.warning("Error historico: %s", e)

# ─── SCAN PRINCIPAL ──────────────────────────────────────────────
def scan() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    aprendidas = cargar_aprendidas()

    # Carga fuentes primarias
    primarias: dict = {}
    if MAPA_FUENTES.exists():
        with open(MAPA_FUENTES, encoding="utf-8") as f:
            for linea in f:
                if linea.startswith("#") or not linea.strip(): continue
                p = [x.strip() for x in linea.split("|")]
                if len(p) >= 3:
                    try:
                        v, url, cf = p[0], p[1], float(p[2])
                        primarias.setdefault(v, []).append({"url": url, "cf": cf})
                    except ValueError:
                        pass

    ts = time.time()
    print(f"--- S.I.E.G. IRAN SCANNER {VERSION} | {datetime.now().strftime('%H:%M:%S')} ---")
    print(f"    Vectores: {len(VECTORES)} | Umbral: {MIN_NOTICIAS} noticias | Flash TTL: {FLASH_TTL_H}h")
    print()

    scores_globales = []
    flashes_existentes = cargar_flashes()
    flashes_nuevos_ciclo = []

    for vector in VECTORES:
        file_path = DATA_DIR / f"iran_{vector.lower()}.json"
        try:
            old_score = float(json.load(open(file_path)).get("score", 20))
        except (OSError, json.JSONDecodeError, ValueError):
            old_score = float(SUELOS_BASE.get(vector, 20))

        historico = cargar_historico(vector)
        noticias, activas, calidad, aprendidas = fetch_con_autolearning(
            vector, primarias.get(vector, []), aprendidas
        )
        score, dison = calcular_triaje(noticias, vector, old_score, historico)

        # ── Extracción de flashes ──
        nuevos_flash = extraer_flashes(noticias, vector, score, ts)
        flashes_nuevos_ciclo.extend(nuevos_flash)

        try:
            json.dump({
                "score":             score,
                "disonancia":        dison,
                "timestamp":         ts,
                "noticias":          len(noticias),
                "fuentes_activas":   activas,
                "version":           VERSION,
                "calidad_nivel":     calidad["nivel"],
                "calidad_emoji":     calidad["emoji"],
                "calidad_css":       calidad["css"],
                "uso_fallback":      calidad["uso_fallback"],
                "uso_web":           calidad["uso_web"],
            }, open(file_path, "w"), indent=2)
        except OSError as e:
            log.error("%s | No se pudo guardar: %s", vector, e)

        guardar_historico(vector, score, ts)
        scores_globales.append(score)

        delta = score - int(old_score)
        ds    = f"+{delta}" if delta > 0 else str(delta)
        fb    = " [FB]"  if calidad["uso_fallback"] else ""
        web   = " [WEB]" if calidad["uso_web"]      else ""
        flash_tag = f" ⚡{len(nuevos_flash)}" if nuevos_flash else ""
        icono = "☢️ " if score >= 90 else "🔥 " if score >= 75 else "⚠️ " if score >= 60 else "⚖️ "
        print(f"[{icono}] {vector:22} | Score: {score:3}% ({ds:>4}) | "
              f"Noticias: {len(noticias):3} | "
              f"Calidad: {calidad['emoji']} {calidad['nivel']}{fb}{web}{flash_tag}")

    guardar_aprendidas(aprendidas)

    # ── Persistir flashes actualizados ──
    flashes_final = actualizar_flashes(flashes_nuevos_ciclo, flashes_existentes, ts)
    guardar_flashes(flashes_final)
    if flashes_nuevos_ciclo:
        print(f"\n    ⚡ FLASHES NUEVOS: {len(flashes_nuevos_ciclo)} | "
              f"Total activos: {len(flashes_final)}")
        for f in flashes_nuevos_ciclo[:5]:
            print(f"       {f['icono']} [{f['vector']}] {f['titulo'][:80]}")

    # Score global de crisis (media ponderada)
    crisis_score = int(sum(
        s * PESOS_CRISIS.get(v, 0.125)
        for s, v in zip(scores_globales, VECTORES)
    ))

    # Guardar resumen global
    try:
        json.dump({
            "crisis_score":  crisis_score,
            "timestamp":     ts,
            "version":       VERSION,
            "vectores":      dict(zip(VECTORES, scores_globales)),
        }, open(DATA_DIR / "iran_crisis_summary.json", "w"), indent=2)
    except OSError as e:
        log.error("Error summary: %s", e)

    print()
    nivel = ("🔴 CRITICO" if crisis_score >= 80 else
             "🟠 ALTO"    if crisis_score >= 60 else
             "🟡 MEDIO"   if crisis_score >= 40 else "🟢 BAJO")
    print(f"--- CRISIS SCORE GLOBAL: {crisis_score}% | Nivel: {nivel} ---")


if __name__ == "__main__":
    scan()
