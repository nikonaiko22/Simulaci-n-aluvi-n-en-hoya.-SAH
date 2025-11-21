@echo off
REM Script para construir en Windows con PyInstaller usando sah_app.spec
REM Uso: build_windows.bat [--onefile]
SETLOCAL

REM 1) Activar (o crear) entorno virtual
if not exist ".venv\Scripts\activate" (
  echo Creando entorno virtual...
  python -m venv .venv
)
call .venv\Scripts\activate

REM 2) Instalar dependencias necesarias
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

REM 3) Asegurar directorio MPLCONFIGDIR (evita errores al ejecutar matplotlib embebido)
set "MPLCONFIGDIR=%CD%\_mplconfig"
if not exist "%MPLCONFIGDIR%" mkdir "%MPLCONFIGDIR%"

REM 4) Ejecutar PyInstaller con la spec. Si pasas --onefile, PyInstaller lo respetará.
if "%1"=="--onefile" (
  pyinstaller --noconfirm --clean --onefile --windowed sah_app_v3_final.py
) else (
  pyinstaller --noconfirm --clean sah_app.spec
)

echo.
echo BUILD FINALIZADO.
echo Revisa la carpeta "dist\SAHApp" (o "dist\*exe" si usaste --onefile).
ENDLOCAL
pause