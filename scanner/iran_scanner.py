#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iran_scanner.py — V1.0
Escaneo de 8 vectores Iran-Israel con autolearning y salida JSON/CSV.
"""

import os
import json
import csv
import datetime
from pathlib import Path

# Carpeta de datos
LIVE_DIR = Path("../data/live")
ARCHIVE_FILE = Path("../data/archive/history_iran.csv")
VECTORS = [
    "Conflicto_Directo",
    "Proxies_Regionales",
    "Nuclear",
    "Energia_Hormuz",
    "Teatro_Regional",
    "Posicion_Global",
    "Sanciones_Economia",
    "Diplomatico"
]

# Crear carpetas si no existen
LIVE_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_FILE.parent.mkdir(parents=True, exist_ok=True)

def fetch_vector_data(vector):
    """
    Función placeholder: recolecta datos del vector
    Aquí se integrarán fuentes como Times of Israel, ISW, MEMRI, IAEA...
    """
    # Dummy data inicial
    timestamp = datetime.datetime.utcnow().isoformat()
    data = {
        "vector": vector,
        "timestamp": timestamp,
        "score": 0,  # placeholder, luego autolearning
        "events": []
    }
    return data

def save_live_data(vector, data):
    """
    Guarda snapshot del vector en JSON
    """
    filename = LIVE_DIR / f"iran_{vector}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[LIVE] {vector} → {filename}")

def append_archive(data):
    """
    Guarda registro histórico en CSV
    """
    write_header = not ARCHIVE_FILE.exists()
    with open(ARCHIVE_FILE, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["timestamp", "vector", "score"])
        if write_header:
            writer.writeheader()
        writer.writerow({
            "timestamp": data["timestamp"],
            "vector": data["vector"],
            "score": data["score"]
        })
    print(f"[ARCHIVE] {data['vector']} → {ARCHIVE_FILE}")

def main():
    for vector in VECTORS:
        data = fetch_vector_data(vector)
        save_live_data(vector, data)
        append_archive(data)

if __name__ == "__main__":
    main()
