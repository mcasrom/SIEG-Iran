#!/bin/bash
# ============================================================
# SIEG-Iran — Limpieza y reorganización del repo
# Ejecutar UNA SOLA VEZ en el Odroid desde /home/dietpi/SIEG-Iran
# ============================================================
set -e
cd /home/dietpi/SIEG-Iran

echo "=== Limpieza SIEG-Iran ==="

# 1. Eliminar ficheros duplicados en subdirectorios incorrectos
rm -rf app/
rm -rf scanner/
rm -rf sources/

# 2. Eliminar JSONs con nombre en MAYÚSCULAS (duplicados del scanner antiguo)
rm -f data/live/iran_Conflicto_Directo.json
rm -f data/live/iran_Diplomatico.json
rm -f data/live/iran_Energia_Hormuz.json
rm -f data/live/iran_Nuclear.json
rm -f data/live/iran_Posicion_Global.json
rm -f data/live/iran_Proxies_Regionales.json
rm -f data/live/iran_Sanciones_Economia.json
rm -f data/live/iran_Teatro_Regional.json

# 3. Eliminar requirements duplicado
rm -f requirements_iran.txt

# 4. Estructura final correcta
echo ""
echo "=== Estructura final ==="
find . -not -path './.git/*' -type f | sort

# 5. Verificar ficheros clave en root
for f in app_iran.py iran_scanner.py mapa_iran.txt update_iran.sh requirements.txt; do
    [ -f "$f" ] && echo "OK: $f" || echo "FALTA: $f"
done

echo ""
echo "=== Git status ==="
git status --short
