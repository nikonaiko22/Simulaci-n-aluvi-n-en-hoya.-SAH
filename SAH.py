#!/usr/bin/env python3
"""
SAH - Versión 3 actualizada (mantiene tu UI preferida)
Cambios aplicados:
 - El cuadro de resultados (self.txt) ahora es de sólo lectura para el usuario.
   El código sigue escribiendo con helpers (print_line, clear_results_display).
 - Pequeños retoques estéticos (tema 'clam' si está disponible, fuente y paddings)
 - Mantengo intacta la lógica de cálculo y el simulador que indicabas.
Requisitos: Python 3.8+, numpy, matplotlib, tkinter
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Intentar importar 3D
try:
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    HAS_3D = True
except Exception:
    HAS_3D = False

# --------------------------
# Modelo (misma lógica)
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
    fig.clf()
    if style == "Bar 3D" and HAS_3D:
        ax3 = fig.add_subplot(111, projection='3d')
        xs = np.arange(1, W.size + 1)
        zs = np.zeros_like(xs)
        dx = np.ones_like(xs) * 0.5
        dy = np.ones_like(xs) * 0.5
        heights = flows if graph_type.startswith("Caudal") else W
        ax3.bar3d(xs, zs, np.zeros_like(heights), dx, dy, heights, shade=True)
        ax3.set_xlabel("Hora")
        ax3.set_title(graph_type)
        return fig, ax3
    else:
        ax2 = fig.add_subplot(111)
        hours = np.arange(1, W.size + 1)
        y = flows if graph_type.startswith("Caudal") else W
        ylabel = "Caudal (m³/s)" if graph_type.startswith("Caudal") else "Volumen (m³)"
        if style == "Bar 2D":
            ax2.bar(hours, y, color="#2a9d8f")
        elif style == "Line 2D":
            ax2.plot(hours, y, marker='o', linestyle='-', color="#264653", linewidth=2)
            ax2.fill_between(hours, y, alpha=0.08, color="#264653")
        else:
            ax2.bar(hours, y, color="#2a9d8f")
        ax2.set_xlabel("Hora")
        ax2.set_ylabel(ylabel)
        ax2.set_title(graph_type)
        ax2.grid(True, linestyle='--', alpha=0.4)
        return fig, ax2

def open_watershed_simulator_realistic(root, areas_km2, V_matrix, p):
    a = len(areas_km2)
    h = a + p - 1
    top = tk.Toplevel(root)
    top.title("Simulador - Esquema de la cuenca (realista)")

    frm = ttk.Frame(top, padding=8)
    frm.pack(fill="both", expand=True)

    # left: matplotlib canvas
    fig = plt.Figure(figsize=(7,4), dpi=100)
    ax = fig.add_subplot(111)
    canvas = FigureCanvasTkAgg(fig, master=frm)
    canvas.get_tk_widget().pack(side="left", fill="both", expand=True, padx=6, pady=6)

    # right: controls
    ctrl = ttk.Frame(frm, width=240)
    ctrl.pack(side="right", fill="y", padx=6, pady=6)
    ttk.Label(ctrl, text="Simulador - Teoría rápida", font=("Segoe UI", 10, "bold")).pack(pady=(0,6))
    theory_text = (
        "PVCS model: cada hora j de precipitación P_j produce Q_{i,j} = P_j * Ce_j * Cm_j.\n"
        "V_{i,j} = A_i * Q_{i,j}.\n"
        "Las salidas W_k se obtienen sumando las antidiagonales V_{i,j} (i+j-1=k).\n"
        "Este simulador muestra contribuciones por área en la hora seleccionada."
    )
    lbl = tk.Label(ctrl, text=theory_text, wraplength=220, justify="left")
    lbl.pack(pady=(0,8))

    ttk.Label(ctrl, text="Hora (k):").pack(anchor="w")
    slider = ttk.Scale(ctrl, from_=1, to=h, orient="horizontal")
    slider.set(1)
    slider.pack(fill="x", pady=4)

    # legend area
    legend = ttk.LabelFrame(ctrl, text="Leyenda")
    legend.pack(fill="x", pady=6)
    ttk.Label(legend, text="Rectángulos: sub-áreas (proporción de área)").pack(anchor="w", padx=6, pady=2)
    ttk.Label(legend, text="Color: aporte en la hora k").pack(anchor="w", padx=6, pady=2)

    def draw_for_hour(k):
        ax.clear()
        # compute contribution per area for W_k
        contribs = np.zeros(a)
        for i in range(a):
            for j in range(p):
                if (i + j + 1) == k:
                    contribs[i] += V_matrix[i, j]
        # normalize contributions for color
        maxc = contribs.max() if contribs.max() > 0 else 1.0
        norm = contribs / maxc
        # draw topographic-like layout (stacked terraces)
        total_width = 1.0
        widths = np.array(areas_km2) / np.sum(areas_km2)
        widths = np.clip(widths, 0.01, None)
        widths = widths / widths.sum() * total_width
        x = 0.02
        y_base = 0.1
        height_unit = 0.6 / a
        for idx, w in enumerate(widths):
            # height to visualize area ranking (not hydrologic real altitude, just graphic)
            h_rect = 0.12 + idx * 0.02 + height_unit * (widths[idx] * 10)
            rect = plt.Rectangle((x, y_base + idx * 0.02), w, h_rect,
                                 facecolor=plt.cm.viridis(0.2 + 0.8 * norm[idx]),
                                 edgecolor='k')
            ax.add_patch(rect)
            ax.text(x + w/2, y_base + idx * 0.02 + h_rect/2,
                    f"A{idx+1}\n{areas_km2[idx]:.3f} km²\nV={contribs[idx]:.0f} m³",
                    ha='center', va='center', fontsize=8, color='white')
            x += w + 0.01
        # draw diagonal isochrones lines across the layout to illustrate travel times
        for iso in range(1, a + p):
            ax.plot([0, 1], [0.05 + 0.9 * (iso / (a + p)), 0.05 + 0.9 * (iso / (a + p))],
                    color="#888", linestyle="--", linewidth=0.6, alpha=0.6)
        # draw exit arrow at right
        ax.annotate("Salida", xy=(1.02, 0.5), xytext=(1.02, 0.8), arrowprops=dict(facecolor='black', shrink=0.05))
        ax.axis('off')
        ax.set_xlim(0, 1.1)
        ax.set_ylim(0, 1)
        ax.set_title(f"Contribuciones a la hora {k} (W_k = {contribs.sum():.2f} m³)")
        canvas.draw()

    draw_for_hour(1)

    def on_slide(val):
        k = int(float(val))
        draw_for_hour(k)

    slider.config(command=on_slide)

    ttk.Button(ctrl, text="Cerrar", command=top.destroy).pack(pady=6)

class SAHAppV3:
    def __init__(self, root):
        self.root = root
        root.title("SAH - Volúmenes Pasantes ")

        # styling (más corporativo)
        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        # Paleta y tipografías sutiles
        style.configure(".", background="#f6f7f9", foreground="#212121")
        style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"), foreground="#1b5e20")
        style.configure("TButton", padding=6)
        style.map("TButton",
                  foreground=[("active", "#ffffff")],
                  background=[("active", "#2a9d8f")])

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

        # header
        header = ttk.Frame(root, padding=8)
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="SAH - Cálculo de Volúmenes Pasantes", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="Teoría", command=self.open_theory).grid(row=0, column=1, sticky="e", padx=6)

        # main layout: left controls, right canvas+results
        main = ttk.Frame(root, padding=8)
        main.grid(row=1, column=0, sticky="nsew")
        root.rowconfigure(1, weight=1)
        root.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        # left controls
        controls = ttk.Frame(main, padding=6, relief="flat")
        controls.grid(row=0, column=0, sticky="nsw", padx=(0,8))
        ttk.Label(controls, text="Parámetros iniciales", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,6))
        ttk.Label(controls, text="Cantidad áreas (a):").grid(row=1, column=0, sticky="w")
        ttk.Entry(controls, textvariable=self.a_var, width=6).grid(row=1, column=1, sticky="w")
        ttk.Button(controls, text="Editar Áreas", command=self.edit_areas).grid(row=2, column=0, columnspan=2, pady=(6,6), sticky="ew")

        ttk.Label(controls, text="Cantidad precip. (p):").grid(row=3, column=0, sticky="w")
        ttk.Entry(controls, textvariable=self.p_var, width=6).grid(row=3, column=1, sticky="w")
        ttk.Button(controls, text="Editar Precipitaciones", command=self.edit_precips).grid(row=4, column=0, columnspan=2, pady=(6,10), sticky="ew")

        ttk.Label(controls, text="Tipo gráfico:").grid(row=5, column=0, sticky="w")
        graph_combo = ttk.Combobox(controls, textvariable=self.graph_type_var, state="readonly",
                                   values=["Caudal vs Hora", "Volumen vs Hora"])
        graph_combo.grid(row=5, column=1, sticky="w")
        ttk.Label(controls, text="Estilo:").grid(row=6, column=0, sticky="w", pady=(6,0))
        style_combo = ttk.Combobox(controls, textvariable=self.style_var, state="readonly", values=default_styles)
        style_combo.grid(row=6, column=1, sticky="w", pady=(6,0))

        ttk.Button(controls, text="Simular", command=self.simulate).grid(row=8, column=0, columnspan=2, pady=(12,6), sticky="ew")
        ttk.Button(controls, text="Mostrar resultados en ventana", command=self.open_results_window).grid(row=9, column=0, columnspan=2, sticky="ew")
        ttk.Button(controls, text="Abrir simulador cuenca", command=self.open_simulator).grid(row=10, column=0, columnspan=2, pady=(6,0), sticky="ew")

        # bind traces to auto-update plot on combobox change
        self.graph_type_var.trace_add("write", lambda *a: self._on_style_change())
        self.style_var.trace_add("write", lambda *a: self._on_style_change())

        # right area: canvas (top) + results panel (bottom)
        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        # canvas
        self.fig_main = plt.Figure(figsize=(7,4), dpi=110)
        self.ax_main = self.fig_main.add_subplot(111)
        self.canvas_main = FigureCanvasTkAgg(self.fig_main, master=right)
        self.canvas_main.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # results panel (embedded)
        results_frame = ttk.LabelFrame(right, text="Resultados")
        results_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=(2,4))
        results_frame.columnconfigure(0, weight=1)

        # info text area (read-only for user)
        self.txt = scrolledtext.ScrolledText(results_frame, width=60, height=8, state="disabled", wrap="none")
        self.txt.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # table small (treeview)
        cols = ("hora", "volumen", "caudal")
        self.tree = ttk.Treeview(results_frame, columns=cols, show="headings", height=6)
        self.tree.heading("hora", text="Hora")
        self.tree.heading("volumen", text="Volumen (m³)")
        self.tree.heading("caudal", text="Caudal (m³/s)")
        self.tree.column("hora", width=60, anchor="center")
        self.tree.column("volumen", width=140, anchor="e")
        self.tree.column("caudal", width=120, anchor="e")
        self.tree.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        # export button
        btn_frame = ttk.Frame(results_frame)
        btn_frame.grid(row=2, column=0, sticky="e", padx=6, pady=(0,6))
        ttk.Button(btn_frame, text="Exportar CSV", command=self.export_csv).pack(side="right")

        # store last results
        self.last_W = None
        self.last_flows = None
        self.last_V = None
        self.last_p = None
        self.last_a = None

        # initial greeting (use helper so text area stays read-only to user)
        self.print_line("Interfaz lista. Configure parámetros y pulse 'Simular'. Cambios en 'Tipo/Estilo' actualizan el gráfico automáticamente.")

    # helpers UI (write-safe for read-only widget)
    def print_line(self, s):
        self.txt.config(state="normal")
        self.txt.insert(tk.END, s + "\n")
        self.txt.see(tk.END)
        self.txt.config(state="disabled")

    def clear_results_display(self):
        self.txt.config(state="normal")
        self.txt.delete("1.0", tk.END)
        for r in self.tree.get_children():
            self.tree.delete(r)
        self.txt.config(state="disabled")

    # editors (mismos comportamientos)
    def edit_areas(self):
        try:
            a = int(self.a_var.get())
            if a <= 0:
                raise ValueError
        except:
            messagebox.showerror("Error", "Cantidad de áreas (a) debe ser entero positivo.")
            return
        top = tk.Toplevel(self.root)
        top.title("Editar Áreas (km²)")
        txt = scrolledtext.ScrolledText(top, width=40, height=12)
        prefill = ""
        for i in range(a):
            prefill += f"{self.areas_km2[i] if i < len(self.areas_km2) else 0.0}\n"
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
        headers = ["Hora", "Precip (mm)", "Coef. Escorr. (Ce)", "Coef. Mezcla (Cm)"]
        for j, h in enumerate(headers):
            ttk.Label(frame, text=h, relief="ridge", padding=3).grid(row=0, column=j, sticky="nsew")
        entries = []
        p = int(self.p_var.get())
        for i in range(p):
            ttk.Label(frame, text=str(i+1)).grid(row=i+1, column=0)
            e_p = ttk.Entry(frame, width=12); e_p.insert(0, str(self.precips_mm[i])); e_p.grid(row=i+1, column=1)
            e_ce = ttk.Entry(frame, width=12); e_ce.insert(0, str(self.ce[i])); e_ce.grid(row=i+1, column=2)
            e_cm = ttk.Entry(frame, width=12); e_cm.insert(0, str(self.cm[i])); e_cm.grid(row=i+1, column=3)
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

    # -------------------------
    # Simulación y UI updates
    # -------------------------
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
        # adjust lists
        if len(self.areas_km2) != a:
            if len(self.areas_km2) < a:
                self.areas_km2 += [0.0] * (a - len(self.areas_km2))
            else:
                self.areas_km2 = self.areas_km2[:a]
        while len(self.precips_mm) < p:
            self.precips_mm.append(0.0); self.ce.append(0.5); self.cm.append(1.0)
        self.precips_mm = self.precips_mm[:p]; self.ce = self.ce[:p]; self.cm = self.cm[:p]

        A_m2 = [v * 1e6 for v in self.areas_km2]
        try:
            Y = compute_Y_from_hour_vectors(self.ce, self.cm, a)
            Q = compute_Q(self.precips_mm, Y, units_mm=True)
            V = compute_V(A_m2, Q)
            W = compute_W_from_V(V)
            flows = W / 3600.0
        except Exception as e:
            messagebox.showerror("Error en cálculo", str(e))
            return

        # store last
        self.last_W = W
        self.last_flows = flows
        self.last_V = V
        self.last_p = p
        self.last_a = a

        # update results panel embedded (using read-only helpers)
        self.clear_results_display()
        h = a + p - 1
        self.print_line("---- RESULTADOS ----")
        self.print_line(f"Áreas (km²): {self.areas_km2}")
        self.print_line(f"Precipitaciones P (mm): {self.precips_mm}")
        self.print_line(f"Coef Escorr. Ce: {self.ce}")
        self.print_line(f"Coef Mezcla Cm: {self.cm}")
        self.print_line(f"Duración (h) = a + p - 1 = {h}\n")
        self.print_line("Hora  |  Volumen (m³)     |  Caudal (m³/s)")
        for idx in range(h):
            self.print_line(f"{idx+1:3d}   |  {W[idx]:12.2f}  |  {flows[idx]:10.4f}")
            self.tree.insert("", "end", values=(idx+1, f"{W[idx]:.2f}", f"{flows[idx]:.4f}"))
        max_idx = int(np.argmax(flows)); max_flow = flows[max_idx]
        max_vol_idx = int(np.argmax(W)); max_vol = W[max_vol_idx]
        self.print_line("")
        self.print_line(f"Hora crítica (máx caudal): {max_idx+1} -> {max_flow:.4f} m³/s")
        self.print_line(f"Volumen máximo por hora: {max_vol:.2f} m³ en hora {max_vol_idx+1}")

        # update main plot (immediately)
        self._update_main_plot()

    def _update_main_plot(self):
        if self.last_W is None or self.last_flows is None:
            return
        graph_type = self.graph_type_var.get()
        style = self.style_var.get()
        try:
            self.fig_main, self.ax_main = draw_main_plot(self.fig_main, self.ax_main,
                                                         self.last_W, self.last_flows,
                                                         graph_type=graph_type, style=style)
            self.canvas_main.draw()
        except Exception as e:
            messagebox.showwarning("Aviso gráfico", f"No fue posible dibujar en estilo {style}: {e}")

    def _on_style_change(self):
        # auto-update chart when style or graph type changes
        self._update_main_plot()

    def open_simulator(self):
        if self.last_V is None:
            messagebox.showinfo("Info", "Ejecuta primero 'Simular' para generar datos y luego abre el simulador.")
            return
        open_watershed_simulator_realistic(self.root, self.areas_km2, self.last_V, self.last_p)

    def open_results_window(self):
        if self.last_W is None:
            messagebox.showinfo("Info", "Ejecuta primero 'Simular' para ver resultados.")
            return
        top = tk.Toplevel(self.root)
        top.title("Resultados - ventana")
        frm = ttk.Frame(top, padding=8)
        frm.pack(fill="both", expand=True)
        txt = scrolledtext.ScrolledText(frm, width=70, height=20, state="normal")
        txt.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        # copiar el contenido del widget read-only
        content = self.txt.get("1.0", tk.END)
        txt.insert("1.0", content)
        txt.config(state="disabled")
        # add copy/export
        def save_local():
            f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", ".csv")])
            if not f:
                return
            self._export_csv_to(f)
            messagebox.showinfo("Exportado", f"CSV guardado en: {f}")
        ttk.Button(frm, text="Exportar CSV", command=save_local).pack(side="right", padx=6, pady=6)

    def export_csv(self):
        if self.last_W is None or self.last_flows is None:
            messagebox.showinfo("Info", "No hay resultados para exportar. Ejecuta Simular primero.")
            return
        f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", ".csv")])
        if not f:
            return
        self._export_csv_to(f)
        messagebox.showinfo("Exportado", f"CSV guardado en: {f}")

    def _export_csv_to(self, filepath):
        import csv
        h = self.last_W.size
        with open(filepath, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["Hora", "Volumen_m3", "Caudal_m3s"])
            for i in range(h):
                w.writerow([i+1, f"{self.last_W[i]:.6f}", f"{self.last_flows[i]:.6f}"])

    def open_theory(self):
        top = tk.Toplevel(self.root)
        top.title("Teoría del modelo PVCS")
        frm = ttk.Frame(top, padding=8)
        frm.pack(fill="both", expand=True)
        text = (
            "Estructura del modelo PVCS:\n\n"
            "Parámetros:\n"
            " P_j: precipitación en la hora j (m o mm). Convertir a m si es mm.\n"
            " A_i: área i (m²).\n"
            " Ce_j: coeficiente de escorrentía por hora j (adimensional).\n"
            " Cm_j: coeficiente de mezcla por hora j (adimensional).\n\n"
            "Ecuaciones principales:\n"
            " Q_{i,j} = P_j * Ce_j * Cm_j  (profundidad eficaz en m)\n"
            " V_{i,j} = A_i * Q_{i,j}      (volumen m³)\n"
            " W_k = sum_{i,j: i+j-1=k} V_{i,j}  (volumen pasante en la hora k)\n\n"
            "h = a + p - 1 es la duración total de evacuación.\n\n"
            "Este programa usa estas fórmulas, permite visualizar contribuciones por hora\n"
            "y exportar resultados."
        )
        txt = scrolledtext.ScrolledText(frm, width=80, height=20)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", text)
        txt.config(state="disabled")
        ttk.Button(frm, text="Cerrar", command=top.destroy).pack(pady=6)

# --------------------------
# Ejecutar app
# --------------------------
def main():
    root = tk.Tk()
    root.geometry("1100x700")
    app = SAHAppV3(root)
    root.mainloop()

if __name__ == "__main__":
    main()