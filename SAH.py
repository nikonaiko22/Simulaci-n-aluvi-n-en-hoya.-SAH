#!/usr/bin/env python3
# sah_app.py
"""
SAH - Versión mejorada con selección de gráficos y simulador de cuenca.
- Selector: Volumen vs Hora / Caudal vs Hora
- Estilos: Barra 2D, Línea 2D, Barra 3D
- Gráfico principal actualizado en la ventana principal al pulsar Simular
- Botón para "Mostrar esquema de la cuenca" con slider por hora
Requisitos: Python 3.8+, numpy, matplotlib, tkinter
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Intentar importar 3D (si no está disponible, deshabilitamos opción 3D)
try:
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    HAS_3D = True
except Exception:
    HAS_3D = False

# --------------------------
# Funciones del modelo (PVCS)
# --------------------------
def compute_Y_from_hour_vectors(Ce_vec, Cm_vec, a):
    Ce = np.asarray(Ce_vec, dtype=float).reshape(-1)
    Cm = np.asarray(Cm_vec, dtype=float).reshape(-1)
    if Ce.size != Cm.size:
        raise ValueError("Ce y Cm deben tener igual longitud (p).")
    p = Ce.size
    Y_row = (Ce * Cm).reshape(1, p)
    Y = np.tile(Y_row, (a, 1))
    return Y

def compute_Q(P_mm, Y, units_mm=True):
    P = np.asarray(P_mm, dtype=float).reshape(-1)
    p = P.size
    a, py = Y.shape
    if p != py:
        raise ValueError("Longitud de P debe ser igual número de columnas de Y (p).")
    if units_mm:
        P = P / 1000.0
    Pmat = np.tile(P.reshape(1, p), (a, 1))
    Q = Pmat * Y
    return Q

def compute_V(A_m2, Q):
    A = np.asarray(A_m2, dtype=float).reshape(-1)
    a = A.size
    ay, p = Q.shape
    if a != ay:
        raise ValueError("Longitud de A debe ser igual número de filas de Q (a).")
    Amat = np.tile(A.reshape(a, 1), (1, p))
    V = Amat * Q
    return V

def compute_W_from_V(V):
    a, p = V.shape
    h = a + p - 1
    W = np.zeros(h, dtype=float)
    for i in range(a):
        for j in range(p):
            k = i + j
            W[k] += V[i, j]
    return W

# --------------------------
# Gráficos
# --------------------------
def draw_main_plot(fig, ax, W, flows, graph_type="Caudal vs Hora", style="Bar 2D"):
    """
    Dibuja en 'fig' y 'ax' (objetos matplotlib) según las opciones.
    graph_type: "Caudal vs Hora" o "Volumen vs Hora"
    style: "Bar 2D", "Line 2D", "Bar 3D" (si no hay 3D, se cae a Bar 2D)
    """
    # limpiamos figura
    fig.clf()
    if style == "Bar 3D" and HAS_3D:
        ax3 = fig.add_subplot(111, projection='3d')
        xs = np.arange(1, W.size + 1)
        zs = np.zeros_like(xs)
        dx = np.ones_like(xs) * 0.5
        dy = np.ones_like(xs) * 0.5
        if graph_type.startswith("Caudal"):
            heights = flows
            ax3.set_zlabel("Caudal (m³/s)")
        else:
            heights = W
            ax3.set_zlabel("Volumen (m³)")
        # 3D bars: x, y fixed
        ax3.bar3d(xs, zs, np.zeros_like(heights), dx, dy, heights, shade=True)
        ax3.set_xlabel("Hora")
        ax3.set_ylabel("")  # vacío
        ax3.set_title(graph_type)
        return fig, ax3
    else:
        ax2 = fig.add_subplot(111)
        hours = np.arange(1, W.size + 1)
        if graph_type.startswith("Caudal"):
            y = flows
            ylabel = "Caudal (m³/s)"
        else:
            y = W
            ylabel = "Volumen (m³)"
        if style == "Bar 2D":
            ax2.bar(hours, y, color="tab:orange")
        elif style == "Line 2D":
            ax2.plot(hours, y, marker='o', linestyle='-', color="tab:blue")
        else:
            # fallback
            ax2.bar(hours, y, color="tab:orange")
        ax2.set_xlabel("Hora")
        ax2.set_ylabel(ylabel)
        ax2.set_title(graph_type)
        ax2.grid(True, linestyle=':', alpha=0.5)
        return fig, ax2

# --------------------------
# Esquema de la cuenca (simulador sencillo)
# --------------------------
def open_watershed_simulator(root, areas_km2, V_matrix, p):
    """
    Abre ventana con esquema simplificado de la cuenca.
    - areas_km2: lista de áreas (km2)
    - V_matrix: matriz V (a x p) en m3, para poder mostrar contribuciones por hora
    - p: número de horas de precipitación
    En la ventana hay un slider para seleccionar la hora de evacuación (1..h)
    y se colorean las áreas según su contribución a esa hora (desde 0 a max).
    """
    a = len(areas_km2)
    h = a + p - 1
    top = tk.Toplevel(root)
    top.title("Simulador - Esquema de la cuenca")
    frm = ttk.Frame(top, padding=8)
    frm.pack(fill="both", expand=True)

    # canvas con matplotlib
    fig = plt.Figure(figsize=(6,4), dpi=100)
    ax = fig.add_subplot(111)
    canvas = FigureCanvasTkAgg(fig, master=frm)
    canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

    # slider para seleccionar hora (1..h)
    slider = tk.Scale(frm, from_=1, to=h, orient="horizontal", label="Hora de evacuación (k)")
    slider.pack(fill="x", padx=8, pady=6)

    # función para dibujar la cuenca para la hora k
    def draw_for_hour(k):
        ax.clear()
        # calcular contribuciones por área para la hora k
        # V is a x p, we need contributions V[i,j] such that i+j-1 == k (1-based)
        contribs = np.zeros(a)
        for i in range(a):
            for j in range(p):
                if (i + j + 1) == k:
                    contribs[i] += V_matrix[i, j]
        # colores según contribución (normalize)
        maxc = contribs.max() if contribs.max() > 0 else 1.0
        norm = contribs / maxc
        # dibujar áreas como rectángulos left-to-right
        total_width = 1.0
        widths = np.array([max(0.05, w) for w in (np.array(areas_km2) / np.sum(areas_km2))])  # proporcionales
        # normalize widths to total_width
        widths = widths / widths.sum() * total_width
        x = 0.05
        for idx, w in enumerate(widths):
            rect = plt.Rectangle((x, 0.3), w, 0.4, facecolor=plt.cm.Reds(norm[idx]), edgecolor='k')
            ax.add_patch(rect)
            ax.text(x + w/2, 0.5, f"A{idx+1}\n{areas_km2[idx]:.3f} km²\nV={contribs[idx]:.0f} m³",
                    ha='center', va='center', fontsize=8)
            x += w + 0.01
        ax.set_xlim(0,1.1)
        ax.set_ylim(0,1)
        ax.axis('off')
        ax.set_title(f"Contribuciones a la hora {k} (W_k = {contribs.sum():.2f} m³)")
        canvas.draw()

    # initialize
    draw_for_hour(1)

    def on_slider_change(val):
        k = int(float(val))
        draw_for_hour(k)

    slider.config(command=on_slider_change)

    # botón para cerrar
    ttk.Button(frm, text="Cerrar", command=top.destroy).pack(pady=6)

# --------------------------
# GUI principal
# --------------------------
class SAHAppV2:
    def __init__(self, root):
        self.root = root
        root.title("SAH - Simulación Volúmenes Pasantes (v2)")

        # variables
        self.a_var = tk.IntVar(value=3)
        self.p_var = tk.IntVar(value=4)
        self.graph_type_var = tk.StringVar(value="Caudal vs Hora")
        default_styles = ["Bar 2D", "Line 2D"]
        if HAS_3D:
            default_styles.append("Bar 3D")
        self.style_var = tk.StringVar(value=default_styles[0])

        # datos por defecto
        self.areas_km2 = [1.0, 0.5, 0.2]
        self.precips_mm = [10.0, 5.0, 0.0, 2.0]
        self.ce = [0.5, 0.6, 0.0, 0.4]
        self.cm = [1.0, 1.0, 1.0, 1.0]

        # top frame: inputs + graph options
        topf = ttk.Frame(root, padding=6)
        topf.grid(row=0, column=0, sticky="ew")
        ttk.Label(topf, text="Cantidad áreas (a):").grid(row=0, column=0, sticky="w")
        ttk.Entry(topf, textvariable=self.a_var, width=6).grid(row=0, column=1, sticky="w", padx=4)
        ttk.Button(topf, text="Editar Áreas", command=self.edit_areas).grid(row=0, column=2, padx=6)

        ttk.Label(topf, text="Cantidad precipitaciones (p):").grid(row=0, column=3, sticky="w", padx=(20,0))
        ttk.Entry(topf, textvariable=self.p_var, width=6).grid(row=0, column=4, sticky="w", padx=4)
        ttk.Button(topf, text="Editar Precipitaciones", command=self.edit_precips).grid(row=0, column=5, padx=6)

        # graph options
        ttk.Label(topf, text="Tipo gráfico:").grid(row=1, column=0, sticky="w", pady=(6,0))
        graph_combo = ttk.Combobox(topf, textvariable=self.graph_type_var, state="readonly",
                                   values=["Caudal vs Hora", "Volumen vs Hora"])
        graph_combo.grid(row=1, column=1, sticky="w", padx=4, pady=(6,0))

        ttk.Label(topf, text="Estilo:").grid(row=1, column=3, sticky="w", padx=(20,0), pady=(6,0))
        style_combo = ttk.Combobox(topf, textvariable=self.style_var, state="readonly",
                                   values=default_styles)
        style_combo.grid(row=1, column=4, sticky="w", padx=4, pady=(6,0))

        ttk.Button(topf, text="Simular", command=self.simulate).grid(row=1, column=6, padx=8)
        ttk.Button(topf, text="Limpiar", command=self.clear_output).grid(row=1, column=7, padx=4)
        ttk.Button(topf, text="Mostrar esquema de la cuenca", command=self.open_simulator).grid(row=1, column=8, padx=6)

        # bottom: text + main plot
        bottom = ttk.Frame(root, padding=6)
        bottom.grid(row=1, column=0, sticky="nsew")
        root.rowconfigure(1, weight=1)
        root.columnconfigure(0, weight=1)

        self.txt = scrolledtext.ScrolledText(bottom, width=60, height=16)
        self.txt.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        bottom.rowconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=1)

        # main matplotlib figure for the principal screen
        self.fig_main = plt.Figure(figsize=(6,4), dpi=100)
        self.ax_main = self.fig_main.add_subplot(111)
        self.canvas_main = FigureCanvasTkAgg(self.fig_main, master=bottom)
        self.canvas_main.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=4, pady=4)

        self.print_line("Aplicación lista. Ajusta 'a' y 'p', edita Áreas/Precipitaciones y pulsa Simular.")

        # store last V matrix for simulator
        self.last_V = None
        self.last_p = None
        self.last_a = None

    def print_line(self, s):
        self.txt.insert(tk.END, s + "\n")
        self.txt.see(tk.END)

    def clear_output(self):
        self.txt.delete("1.0", tk.END)
        # clear main plot
        self.fig_main.clf()
        self.ax_main = self.fig_main.add_subplot(111)
        self.ax_main.set_xlabel("Hora")
        self.ax_main.set_ylabel("Caudal (m³/s)")
        self.canvas_main.draw()
        self.print_line("Salida limpiada.")

    # -----------------
    # Editores (mismo comportamiento que v1)
    # -----------------
    def edit_areas(self):
        try:
            a = int(self.a_var.get())
            if a <= 0:
                raise ValueError
        except:
            messagebox.showerror("Error", "Cantidad de áreas (a) debe ser entero positivo.")
            return
        top = tk.Toplevel(self.root)
        top.title("Editar Áreas (km²) - uno por línea")
        txt = scrolledtext.ScrolledText(top, width=40, height=12)
        prefill = ""
        for i in range(a):
            if i < len(self.areas_km2):
                prefill += f"{self.areas_km2[i]}\n"
            else:
                prefill += "0.0\n"
        txt.insert("1.0", prefill)
        txt.pack(padx=8, pady=8)
        def save():
            content = txt.get("1.0", tk.END).strip()
            if not content:
                messagebox.showerror("Error", "Introduce al menos un valor.")
                return
            parts = []
            for line in content.splitlines():
                for token in line.split(","):
                    tok = token.strip()
                    if tok != "":
                        parts.append(tok)
            if len(parts) < a:
                messagebox.showerror("Error", f"Se esperaban {a} valores, se obtuvieron {len(parts)}.")
                return
            try:
                areas = [float(parts[i]) for i in range(a)]
            except Exception as e:
                messagebox.showerror("Error", f"Valores inválidos: {e}")
                return
            self.areas_km2 = areas
            self.print_line(f"Áreas guardadas (km²): {self.areas_km2}")
            top.destroy()
        ttk.Button(top, text="Guardar", command=save).pack(pady=6)

    def edit_precips(self):
        try:
            p = int(self.p_var.get())
            if p <= 0:
                raise ValueError
        except:
            messagebox.showerror("Error", "Cantidad de precipitaciones (p) debe ser entero positivo.")
            return
        # ensure lists lengths
        while len(self.precips_mm) < p:
            self.precips_mm.append(0.0)
            self.ce.append(0.5)
            self.cm.append(1.0)
        if len(self.precips_mm) > p:
            self.precips_mm = self.precips_mm[:p]
            self.ce = self.ce[:p]
            self.cm = self.cm[:p]

        top = tk.Toplevel(self.root)
        top.title("Editor Precipitaciones (cada fila = hora)")
        frame = ttk.Frame(top, padding=8)
        frame.pack(fill="both", expand=True)

        headers = ["Hora", "Precipitación (mm)", "Coef. Escorrentía (Ce)", "Coef. Mezcla (Cm)"]
        for j, h in enumerate(headers):
            lbl = ttk.Label(frame, text=h, relief="ridge", padding=3)
            lbl.grid(row=0, column=j, sticky="nsew")
        entries = []
        for i in range(p):
            ttk.Label(frame, text=str(i+1)).grid(row=i+1, column=0)
            e_p = ttk.Entry(frame, width=12)
            e_p.insert(0, str(self.precips_mm[i]))
            e_p.grid(row=i+1, column=1)
            e_ce = ttk.Entry(frame, width=12)
            e_ce.insert(0, str(self.ce[i]))
            e_ce.grid(row=i+1, column=2)
            e_cm = ttk.Entry(frame, width=12)
            e_cm.insert(0, str(self.cm[i]))
            e_cm.grid(row=i+1, column=3)
            entries.append((e_p, e_ce, e_cm))

        def save():
            newP, newCe, newCm = [], [], []
            try:
                for i in range(p):
                    newP.append(float(entries[i][0].get()))
                    newCe.append(float(entries[i][1].get()))
                    newCm.append(float(entries[i][2].get()))
            except Exception as e:
                messagebox.showerror("Error", f"Valores inválidos: {e}")
                return
            self.precips_mm = newP
            self.ce = newCe
            self.cm = newCm
            self.print_line(f"Precipitaciones guardadas (p={len(self.precips_mm)}): P(mm)={self.precips_mm}")
            top.destroy()
        ttk.Button(top, text="Guardar", command=save).pack(pady=6)

    # -----------------
    # Simulación
    # -----------------
    def simulate(self):
        try:
            a = int(self.a_var.get())
            p = int(self.p_var.get())
        except:
            messagebox.showerror("Error", "a y p deben ser enteros.")
            return
        if a <= 0 or p <= 0:
            messagebox.showerror("Error", "a y p deben ser positivos.")
            return
        # validar arrays
        if len(self.areas_km2) != a:
            if len(self.areas_km2) < a:
                self.areas_km2 += [0.0] * (a - len(self.areas_km2))
            else:
                self.areas_km2 = self.areas_km2[:a]
        if len(self.precips_mm) != p or len(self.ce) != p or len(self.cm) != p:
            while len(self.precips_mm) < p:
                self.precips_mm.append(0.0)
                self.ce.append(0.5)
                self.cm.append(1.0)
            self.precips_mm = self.precips_mm[:p]
            self.ce = self.ce[:p]
            self.cm = self.cm[:p]

        A_m2 = [v * 1e6 for v in self.areas_km2]  # km2 -> m2
        try:
            Y = compute_Y_from_hour_vectors(self.ce, self.cm, a)  # a x p
            Q = compute_Q(self.precips_mm, Y, units_mm=True)      # a x p (m)
            V = compute_V(A_m2, Q)                                # a x p (m3)
            W = compute_W_from_V(V)                               # h
            flows = W / 3600.0                                    # m3/s
        except Exception as e:
            messagebox.showerror("Error en cálculo", str(e))
            return

        h = a + p - 1
        # Guardar V para el simulador
        self.last_V = V
        self.last_p = p
        self.last_a = a

        # Escribir salida
        self.clear_output()
        self.print_line("---- RESULTADOS ----")
        self.print_line(f"Áreas (km²): {self.areas_km2}")
        self.print_line(f"Precipitaciones P (mm): {self.precips_mm}")
        self.print_line(f"Coef Escorrentía Ce (por hora): {self.ce}")
        self.print_line(f"Coef Mezcla Cm (por hora): {self.cm}")
        self.print_line(f"Duración de evacuación (h) = a + p - 1 = {h}")
        self.print_line("")
        self.print_line("Hora  |  Volumen (m³)     |  Caudal (m³/s)")
        for idx in range(h):
            self.print_line(f"{idx+1:3d}   |  {W[idx]:12.2f}  |  {flows[idx]:10.4f}")

        # máximos
        max_idx = int(np.argmax(flows))
        max_flow = flows[max_idx]
        max_vol_idx = int(np.argmax(W))
        max_vol = W[max_vol_idx]
        self.print_line("")
        self.print_line(f"Hora crítica (máx caudal): {max_idx+1} -> {max_flow:.4f} m³/s")
        self.print_line(f"Volumen máximo por hora: {max_vol:.2f} m³ en hora {max_vol_idx+1}")

        # actualizar gráfico principal según opciones seleccionadas
        graph_type = self.graph_type_var.get()
        style = self.style_var.get()
        # dibujar en figura principal
        try:
            self.fig_main, ax_main = draw_main_plot(self.fig_main, self.ax_main, W, flows,
                                                    graph_type=graph_type, style=style)
            self.canvas_main.draw()
        except Exception as e:
            messagebox.showwarning("Aviso gráfico", f"No fue posible dibujar en estilo {style}: {e}")
            # fallback simple
            self.fig_main.clf()
            self.ax_main = self.fig_main.add_subplot(111)
            self.ax_main.plot(np.arange(1, W.size+1), flows, marker='o')
            self.canvas_main.draw()

        # además abrimos la ventana de tabla y gráfico opcional (como antes)
        self.show_table_and_plot(W, flows)

    def open_simulator(self):
        if self.last_V is None:
            messagebox.showinfo("Info", "Ejecuta primero 'Simular' para generar datos y luego abre el simulador.")
            return
        open_watershed_simulator(self.root, self.areas_km2, self.last_V, self.last_p)

    def show_table_and_plot(self, W, flows):
        top = tk.Toplevel(self.root)
        top.title("Resultados - Tabla y Gráfico")
        frm = ttk.Frame(top, padding=8)
        frm.pack(fill="both", expand=True)
        # tabla
        cols = ("hora", "volumen_m3", "caudal_m3s")
        tree = ttk.Treeview(frm, columns=cols, show="headings", height=10)
        tree.heading("hora", text="Hora")
        tree.heading("volumen_m3", text="Volumen (m³)")
        tree.heading("caudal_m3s", text="Caudal (m³/s)")
        tree.column("hora", width=60, anchor="center")
        tree.column("volumen_m3", width=140, anchor="e")
        tree.column("caudal_m3s", width=120, anchor="e")
        tree.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        frm.rowconfigure(0, weight=1)
        frm.columnconfigure(1, weight=1)
        for i, (v, q) in enumerate(zip(W, flows), start=1):
            tree.insert("", "end", values=(i, f"{v:.2f}", f"{q:.4f}"))

        # grafico (matplotlib) en ventana emergente
        fig2 = plt.Figure(figsize=(5,3), dpi=100)
        ax2 = fig2.add_subplot(111)
        hours = np.arange(1, W.size + 1)
        ax2.bar(hours, flows, color="tab:red")
        ax2.set_xlabel("Hora")
        ax2.set_ylabel("Caudal (m³/s)")
        ax2.set_title("Caudal vs Tiempo")
        canvas2 = FigureCanvasTkAgg(fig2, master=frm)
        canvas2.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        canvas2.draw()

# --------------------------
# Ejecutar aplicación
# --------------------------
def main():
    root = tk.Tk()
    app = SAHAppV2(root)
    root.mainloop()

if __name__ == "__main__":
    main()