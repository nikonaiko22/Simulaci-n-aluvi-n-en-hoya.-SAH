# -*- mode: python -*-
"""
PyInstaller spec para sah_app_v3_final.py
- Recolecta los datos de matplotlib necesarios para que los backends y fuentes funcionen en el .exe.
- Incluye la carpeta assets/ si existe.
- Genera un bundle en dist/SAHApp (COLLECT). Para single-file, usa pyinstaller --onefile sah_app.spec
"""
import os
from PyInstaller.utils.hooks import collect_data_files
block_cipher = None

# recopilar archivos de datos de matplotlib (backends, fonts, etc.)
datas = collect_data_files('matplotlib')

# incluir carpeta assets si existe (íconos, imágenes)
assets_dir = 'assets'
if os.path.isdir(assets_dir):
    for root, dirs, files in os.walk(assets_dir):
        for f in files:
            src = os.path.join(root, f)
            # destino relativo dentro del paquete
            dest_dir = os.path.join('assets', os.path.relpath(root, assets_dir))
            datas.append((src, dest_dir))

a = Analysis(
    ['sah_app_v3_final.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SAHApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # ventana GUI, sin consola
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SAHApp',
)