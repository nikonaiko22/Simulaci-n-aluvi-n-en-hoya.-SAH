# SAH — Volúmenes Pasantes

Aplicación de escritorio (Python/Tkinter) para el cálculo y visualización de volúmenes pasantes (modelo PVCS).  

---

## Resumen rápido

- Lenguaje: Python 3.8+
- UI: Tkinter + ttk (Matplotlib embebido)
- Dependencias principales: numpy, matplotlib
- Archivo principal: `SAH.py` (o el nombre que uses para el script)
- Funcionalidad:
  - Definición/edición de áreas (km²) y precipitaciones (P, Ce, Cm).
  - Cálculo de matrices Q, V, W (volúmenes por hora) con la lógica PVCS.
  - Visualización de caudales/volúmenes (gráficas 2D / 3D si matplotlib incluye mplot3d).
  - Simulador de cuenca (ventana separada) que muestra contribuciones por área.
  - Panel de resultados integrado (texto read-only y tabla), export CSV.
  - Ventana de teoría con la explicación del modelo.

---

## Requisitos

- Python 3.8 o superior
- pip
- (Windows) Se recomienda usar un entorno virtual

Dependencias Python:
- numpy
- matplotlib
- tkinter (normalmente viene incluido en Python; en Linux puede requerir instalar paquete del sistema)

Puedes crear un `requirements.txt` con:
```
numpy
matplotlib
```

---

## Instalación (rápido)

1. Clona o copia el repositorio en tu máquina.
2. (Opcional) Crea y activa un entorno virtual:

- Windows (PowerShell)
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```

- macOS / Linux
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

3. Instala dependencias:
```bash
pip install -r requirements.txt
```
o manualmente:
```bash
pip install numpy matplotlib
```

---

## Ejecutar la aplicación

Desde la carpeta del proyecto (con el entorno virtual activado):
```bash
SAH.py
```

La ventana principal se abrirá y podrás:
- Editar áreas y precipitaciones.
- Pulsar "Simular" para calcular y mostrar resultados.
- Cambiar tipo/estilo de gráfico y ver la actualización inmediata.
- Abrir el simulador de cuenca (ventana aparte).
- Exportar resultados a CSV.

---

## Estructura de archivos

- SAH.py  ← Script principal (contiene UI, lógica y simulador).
- requirements.txt     ← Dependencias Python (numpy, matplotlib).
- README.md            ← Este archivo.

---

## Notas de uso y consejos

- El cuadro de resultados es de solo lectura; el código escribe en él con helpers (`print_line`, `clear_results_display`) para evitar que el usuario borre o edite el contenido accidentalmente.
- Si la gráfica "desaparece" al redimensionar, prueba redibujar (la versión final incluye protecciones para resize).
- El simulador utiliza el resultado `V` generado por la simulación; abre el simulador solo después de pulsar "Simular".
- Las unidades: precipitaciones se ingresan en mm (internamente convertidas a m), áreas en km², resultados mostrados en m³ y m³/s.

---

## Exportar a .exe (Windows)

Puedes empaquetar la app con PyInstaller:

1. Instala PyInstaller:
```bash
pip install pyinstaller
```

2. Crear ejecutable (ejemplo básico):
```bash
pyinstaller --noconfirm --onefile --windowed SAH.py
```

Notas:
- Matplotlib puede requerir incluir datos adicionales (backends, fonts). Si el exe falla con errores de matplotlib, usa opciones `--add-data` para incluir carpetas necesarias o publica sin `--onefile` para facilitar depuración.
- Para una experiencia “corporativa” se recomienda crear instalador (MSI/MSIX) tras generar el exe.

---

## Desarrollo - modificaciones rápidas

- Cambiar paleta o tipografías:
  - Busca la sección donde se configura `ttk.Style(...)` y cambia colores y fuentes.
- Añadir presets (botón que cargue arrays `areas_km2`, `precips_mm`, `ce`, `cm`):
  - Añade una función que asigne las listas y llame a `simulate()` para refrescar.
- Mejorar simulador:
  - El simulador actual dibuja rectángulos y bandas. Para hacerlo más “foto-like” puedes reemplazar el dibujo Matplotlib por una imagen de fondo y posicionar overlays, o usar curvas Bezier para isócronas.
- Tests:
  - Extrae la lógica (compute_Y, compute_Q, compute_V, compute_W_from_V) a un módulo separado para poder añadir unit tests con pytest.

---

## Posibles mejoras futuras

- Migrar UI a PySide6/PyQt6 para un aspecto nativo y más opciones de estilo.
- Reescribir UI nativa en C# (WPF/WinUI) para distribución Windows nativa.
- Añadir generación de reportes (PDF) con matplotlib + ReportLab o WeasyPrint.
- Guardar/abrir proyectos (.json) con todos los parámetros.
- Añadir animaciones en el simulador (Play/Pause).

---
