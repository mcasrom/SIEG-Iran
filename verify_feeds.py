#!/usr/bin/env python3
"""
SIEG-Iran — Verificador y expansor de fuentes
Ejecutar en el Odroid desde /home/dietpi/SIEG-Iran
  python3 verify_feeds.py

Comprueba todos los feeds actuales + candidatos nuevos,
e imprime un mapa_iran.txt actualizado listo para usar.
"""

import urllib.request
import xml.etree.ElementTree as ET
import sys
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SIEG-Verifier/1.0)"}
TIMEOUT = 10

# ─── FUENTES ACTUALES ────────────────────────────────────────────
ACTUALES = {
    "Conflicto_Directo": [
        ("https://www.timesofisrael.com/feed/",                              0.8),
        ("https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",         0.9),
        ("https://rss.nytimes.com/services/xml/rss/nyt/MiddleEast.xml",     0.9),
        ("https://www.aljazeera.com/xml/rss/all.xml",                       0.7),
        ("https://foreignpolicy.com/feed/",                                 0.9),
        ("https://www.defensenews.com/rss/",                                0.8),
        ("https://www.jpost.com/rss/rssfeedsfrontpage.aspx",                0.8),
    ],
    "Proxies_Regionales": [
        ("https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",         0.9),
        ("https://www.aljazeera.com/xml/rss/all.xml",                       0.7),
        ("https://foreignpolicy.com/feed/",                                 0.9),
        ("https://www.middleeasteye.net/rss",                               0.7),
        ("https://rss.nytimes.com/services/xml/rss/nyt/MiddleEast.xml",     0.9),
        ("https://www.defensenews.com/rss/",                                0.8),
    ],
    "Nuclear": [
        ("https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",         0.9),
        ("https://www.iaea.org/feeds/topnews.xml",                          1.0),
        ("https://foreignpolicy.com/feed/",                                 0.9),
        ("https://rss.nytimes.com/services/xml/rss/nyt/MiddleEast.xml",     0.9),
        ("https://www.armscontrol.org/rss.xml",                             1.0),
        ("https://thebulletin.org/feed/",                                   0.9),
    ],
    "Energia_Hormuz": [
        ("https://feeds.bbci.co.uk/news/business/rss.xml",                  0.9),
        ("https://www.aljazeera.com/xml/rss/all.xml",                       0.7),
        ("https://feeds.skynews.com/feeds/rss/world.xml",                   0.8),
        ("https://rss.nytimes.com/services/xml/rss/nyt/Energy.xml",         0.9),
        ("https://www.eia.gov/rss/latest_articles.xml",                     1.0),
        ("https://www.gcaptain.com/feed/",                                  0.8),
    ],
    "Teatro_Regional": [
        ("https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",         0.9),
        ("https://www.aljazeera.com/xml/rss/all.xml",                       0.7),
        ("https://rss.nytimes.com/services/xml/rss/nyt/MiddleEast.xml",     0.9),
        ("https://www.middleeasteye.net/rss",                               0.7),
        ("https://foreignpolicy.com/feed/",                                 0.9),
        ("https://www.timesofisrael.com/feed/",                             0.8),
    ],
    "Posicion_Global": [
        ("https://feeds.bbci.co.uk/news/world/rss.xml",                     0.9),
        ("https://rss.nytimes.com/services/xml/rss/nyt/World.xml",          0.9),
        ("https://foreignpolicy.com/feed/",                                 0.9),
        ("https://thediplomat.com/feed/",                                   0.8),
        ("https://feeds.skynews.com/feeds/rss/world.xml",                   0.8),
        ("https://www.defensenews.com/rss/",                                0.8),
    ],
    "Sanciones_Economia": [
        ("https://feeds.bbci.co.uk/news/business/rss.xml",                  0.9),
        ("https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",       0.9),
        ("https://foreignpolicy.com/feed/",                                 0.9),
        ("https://feeds.skynews.com/feeds/rss/business.xml",                0.8),
        ("https://www.ft.com/rss/home",                                     0.9),
    ],
    "Diplomatico": [
        ("https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",         0.9),
        ("https://rss.nytimes.com/services/xml/rss/nyt/MiddleEast.xml",     0.9),
        ("https://foreignpolicy.com/feed/",                                 0.9),
        ("https://www.aljazeera.com/xml/rss/all.xml",                       0.7),
        ("https://www.middleeasteye.net/rss",                               0.7),
        ("https://thediplomat.com/feed/",                                   0.8),
    ],
}

# ─── CANDIDATOS NUEVOS (solo para Nuclear y Energia_Hormuz) ──────
CANDIDATOS = {
    "Nuclear": [
        ("https://www.38north.org/feed/",                                   1.0, "38North — programa nuclear DPRK/Iran"),
        ("https://nonproliferation.org/feed/",                              1.0, "James Martin CNS"),
        ("https://carnegieendowment.org/rss/solr/?query=iran+nuclear",      0.9, "Carnegie Endowment Nuclear"),
        ("https://www.washingtonpost.com/national-security/rss/",           0.9, "WaPo National Security"),
        ("https://www.reuters.com/rssFeed/worldNews",                       0.9, "Reuters World"),
        ("https://feeds.skynews.com/feeds/rss/world.xml",                   0.8, "Sky News World"),
        ("https://www.haaretz.com/cmlink/1.4482668",                        0.8, "Haaretz"),
        ("https://www.jpost.com/rss/rssfeedsfrontpage.aspx",                0.8, "Jerusalem Post"),
        ("https://www.timesofisrael.com/feed/",                             0.8, "Times of Israel"),
        ("https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",  0.9, "BBC Science/Environment"),
        ("https://www.defensenews.com/rss/",                                0.8, "Defense News"),
        ("https://www.middleeasteye.net/rss",                               0.7, "Middle East Eye"),
        ("https://www.aljazeera.com/xml/rss/all.xml",                       0.7, "Al Jazeera"),
        ("https://api.breakingnews.com/api/v1/item/?format=rss&q=nuclear+iran", 0.7, "Breaking News Nuclear Iran"),
    ],
    "Energia_Hormuz": [
        ("https://oilprice.com/rss/main",                                   0.8, "OilPrice.com"),
        ("https://www.rigzone.com/news/rss/rigzone_latest.aspx",            0.8, "Rigzone"),
        ("https://www.offshore-technology.com/feed/",                       0.8, "Offshore Technology"),
        ("https://www.reuters.com/rssFeed/businessNews",                    0.9, "Reuters Business"),
        ("https://www.seatrade-maritime.com/rss.xml",                       0.8, "Seatrade Maritime"),
        ("https://www.hellenicshippingnews.com/feed/",                      0.8, "Hellenic Shipping News"),
        ("https://splash247.com/feed/",                                     0.8, "Splash247 Maritime"),
        ("https://lloydslist.maritimeintelligence.informa.com/rss",         0.9, "Lloyd's List"),
        ("https://www.maritimeexecutive.com/rss",                           0.8, "Maritime Executive"),
        ("https://www.tankeroperator.com/rss",                              0.8, "Tanker Operator"),
        ("https://www.spglobal.com/commodityinsights/en/rss",               0.9, "S&P Global Commodities"),
        ("https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",        0.9, "BBC Middle East"),
        ("https://www.aljazeera.com/xml/rss/all.xml",                       0.7, "Al Jazeera"),
        ("https://www.reuters.com/rssFeed/worldNews",                       0.9, "Reuters World"),
    ],
}

# ─── VERIFICADOR ─────────────────────────────────────────────────
def verificar_feed(url: str, nombre: str = "") -> tuple:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            content = r.read()
        root  = ET.fromstring(content)
        items = root.findall(".//item")
        n     = len(items)
        return True, n
    except Exception as e:
        return False, str(e)[:50]

# ─── MAIN ────────────────────────────────────────────────────────
print(f"\n{'='*70}")
print(f"SIEG-Iran — Verificador de Fuentes | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"{'='*70}")

resultados = {}   # vector -> [(url, cf, items, ok)]
muertos    = []   # [(vector, url)]

# 1. Verificar actuales
print("\n── FUENTES ACTUALES ─────────────────────────────────────────────────")
for vector, feeds in ACTUALES.items():
    resultados[vector] = []
    total_items = 0
    vivos = 0
    for url, cf in feeds:
        ok, n = verificar_feed(url)
        if ok:
            resultados[vector].append((url, cf, n, True))
            total_items += n
            vivos += 1
            print(f"  ✅ [{vector:20}] {n:4} items | CF:{cf} | {url[:55]}")
        else:
            muertos.append((vector, url, n))
            print(f"  ❌ [{vector:20}] ERROR  | CF:{cf} | {url[:55]}")
            print(f"     → {n}")

# 2. Verificar candidatos nuevos para Nuclear y Energia_Hormuz
print("\n── CANDIDATOS NUEVOS (Nuclear + Energia_Hormuz) ─────────────────────")
aprobados = {"Nuclear": [], "Energia_Hormuz": []}

for vector, candidatos in CANDIDATOS.items():
    urls_existentes = [u for u, _, _, _ in resultados.get(vector, [])]
    print(f"\n  Vector: {vector}")
    for url, cf, desc in candidatos:
        if url in urls_existentes:
            print(f"  ↩  Ya existe: {url[:55]}")
            continue
        ok, n = verificar_feed(url, desc)
        if ok and isinstance(n, int) and n >= 5:
            aprobados[vector].append((url, cf, n, desc))
            print(f"  ✅ {desc:35} {n:4} items | {url[:45]}")
        else:
            print(f"  ❌ {desc:35} {'ERR: '+str(n)[:30] if not ok else str(n)+' items (pocos)'}")

# 3. Resumen
print(f"\n{'='*70}")
print("RESUMEN DE COBERTURA")
print(f"{'='*70}")
for vector in ACTUALES:
    vivos   = [r for r in resultados[vector] if r[3]]
    n_items = sum(r[2] for r in vivos)
    nuevos  = len(aprobados.get(vector, []))
    n_con_nuevos = n_items + sum(r[2] for r in aprobados.get(vector, []))
    calidad = "🟢 VERDE" if n_items >= 80 else "🔵 AZUL" if n_items >= 60 else "🟡 AMARILLO" if n_items >= 40 else "🟠 NARANJA"
    cal_new = "🟢 VERDE" if n_con_nuevos >= 80 else "🔵 AZUL" if n_con_nuevos >= 60 else "🟡 AMARILLO" if n_con_nuevos >= 40 else "🟠 NARANJA"
    mejora  = f" → {cal_new} (+{nuevos} feeds, {n_con_nuevos} items)" if nuevos > 0 else ""
    print(f"  {vector:22} {n_items:4} items | {calidad}{mejora}")

# 4. Fuentes muertas
if muertos:
    print(f"\n── FUENTES A ELIMINAR ───────────────────────────────────────────────")
    for vector, url, err in muertos:
        print(f"  ❌ [{vector}] {url}")

# 5. Generar mapa_iran.txt actualizado
print(f"\n{'='*70}")
print("GENERANDO mapa_iran_v2.txt ...")
print(f"{'='*70}")

lineas = [
    "# SIEG-Iran — Mapa de Fuentes V2.0 (verificado)",
    f"# Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    "# Formato: VECTOR | URL | CF | TIPO | DESCRIPCION",
    "",
]

for vector in ACTUALES:
    lineas.append(f"# ─── {vector.upper()} {'─'*(50-len(vector))}")
    # Fuentes actuales vivas
    for url, cf, n, ok in resultados[vector]:
        if ok:
            lineas.append(f"{vector} | {url} | {cf} | rss | {n} items/ciclo")
    # Candidatos aprobados
    for url, cf, n, desc in aprobados.get(vector, []):
        lineas.append(f"{vector} | {url} | {cf} | rss | NUEVO: {desc} ({n} items)")
    lineas.append("")

with open("mapa_iran_v2.txt", "w") as f:
    f.write("\n".join(lineas))

print("  → mapa_iran_v2.txt generado")
print("\nPara aplicar: cp mapa_iran_v2.txt mapa_iran.txt && python3 iran_scanner.py")
print()
