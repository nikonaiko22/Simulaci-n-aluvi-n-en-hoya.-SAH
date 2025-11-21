#!/usr/bin/env bash
# Script para construir en Linux/macOS con PyInstaller usando sah_app.spec
# Uso: ./build_unix.sh [--onefile]
set -euo pipefail

# 1) Crear/activar venv
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
. .venv/bin/activate

# 2) Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# 3) Preparar MPLCONFIGDIR
export MPLCONFIGDIR="${PWD}/_mplconfig"
mkdir -p "$MPLCONFIGDIR"

# 4) Ejecutar PyInstaller
if [ "${1-}" = "--onefile" ]; then
  pyinstaller --noconfirm --clean --onefile --windowed sah_app_v3_final.py
else
  pyinstaller --noconfirm --clean sah_app.spec
fi

echo "BUILD FINALIZADO. Revisa la carpeta dist/SAHApp (o dist/*.exe si usaste --onefile)."