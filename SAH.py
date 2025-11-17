#!/usr/bin/env python3
# sah_app.py
"""
SAH - Simulación de Volúmenes Pasantes en una Hoya Hidrográfica
Single-file "todo en uno" con GUI Tkinter:
 - Editar cantidad de áreas y cantidad de horas de precipitación
 - Editor de Áreas (uno por línea, km²)
 - Editor "tipo Excel" para Precipitaciones (por hora): columnas [Precipitación mm, Coef. Escorrentía, Coef. Mezcla]
 - Cálculo del modelo PVCS (Q = P * Ce * Cm, V = A * Q), suma por antidiagonales -> W, caudal = W/3600
 - Muestra tabla de resultados, valores máximos y gráfico Caudal vs Tiempo (matplotlib)
Requisitos: Python 3.8+, numpy, matplotlib
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --------------------------
# Funciones del modelo (PVCS)
# --------------------------
def compute_Y_from_hour_vectors(Ce_vec, Cm_vec, a):
    """
    Ce_vec, Cm_vec: vectores de longitud p (por hora).
    Retorna matriz Y (a x p) = Cm_j * Ce_j replicada por filas.
    """
    Ce = np.asarray(Ce_vec, dtype=float).reshape(-1)
    Cm = np.asarray(Cm_vec, dtype=float).reshape(-1)
    if Ce.size != Cm.size:
        raise ValueError("Ce y Cm deben tener igual longitud (p).")
    p = Ce.size
    Y_row = (Ce * Cm).reshape(1, p)  # 1 x p
    Y = np.tile(Y_row, (a, 1))       # a x p
    return Y

def compute_Q(P_mm, Y, units_mm=True):
    """
    Q_{i,j} = P_j * Y_{i,j}
    P_mm: vector longitud p (mm) si units_mm True
    Devuelve Q (a x p) en metros (m)
    """
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
    """
    V_{i,j} = A_i * Q_{i,j}, A_m2: vector longitud a (m^2)
    Devuelve V (a x p) en m^3
    """
    A = np.asarray(A_m2, dtype=float).reshape(-1)
    a = A.size
    ay, p = Q.shape
    if a != ay:
        raise ValueError("Longitud de A debe ser igual número de filas de Q (a).")
    Amat = np.tile(A.reshape(a, 1), (1, p))
    V = Amat * Q
    return V

def compute_W_from_V(V):
    """
    Suma por antidiagonales: h = a + p - 1
    Retorna W (h,) vector de volúmenes por hora en m^3
    """
    a, p = V.shape
    h = a + p - 1
    W = np.zeros(h, dtype=float)
    for i in range(a):
        for j in range(p):
            k = i + j
            W[k] += V[i, j]
    return W

# --------------------------
# GUI
# --------------------------
class SAHApp:
    def __init__(self, root):
        self.root = root
        root.title("SAH - Simulación Volúmenes Pasantes")

        # variables
        self.a_var = tk.IntVar(value=3)
        self.p_var = tk.IntVar(value=4)

        # datos por defecto
        self.areas_km2 = [1.0, 0.5, 0.2]   # km2
        # Por defecto p=4 -> listas por hora
        self.precips_mm = [10.0, 5.0, 0.0, 2.0]
        self.ce = [0.5, 0.6, 0.0, 0.4]
        self.cm = [1.0, 1.0, 1.0, 1.0]

        # top frame (inputs)
        topf = ttk.Frame(root, padding=8)
        topf.grid(row=0, column=0, sticky="ew")
        ttk.Label(topf, text="Cantidad áreas (a):").grid(row=0, column=0, sticky="w")
        ttk.Entry(topf, textvariable=self.a_var, width=6).grid(row=0, column=1, sticky="w", padx=4)
        ttk.Button(topf, text="Editar Áreas", command=self.edit_areas).grid(row=0, column=2, padx=6)

        ttk.Label(topf, text="Cantidad precipitaciones (p):").grid(row=1, column=0, sticky="w")
        ttk.Entry(topf, textvariable=self.p_var, width=6).grid(row=1, column=1, sticky="w", padx=4)
        ttk.Button(topf, text="Editar Precipitaciones", command=self.edit_precips).grid(row=1, column=2, padx=6)

        ttk.Button(topf, text="Simular", command=self.simulate).grid(row=2, column=0, pady=8)
        ttk.Button(topf, text="Limpiar", command=self.clear_output).grid(row=2, column=1, pady=8)

        # bottom: output text + plot
        bottom = ttk.Frame(root, padding=8)
        bottom.grid(row=1, column=0, sticky="nsew")
        root.rowconfigure(1, weight=1)
        root.columnconfigure(0, weight=1)

        self.txt = scrolledtext.ScrolledText(bottom, width=60, height=18)
        self.txt.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        bottom.rowconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=1)

        # matplotlib canvas
        self.fig = plt.Figure(figsize=(6,4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Hora")
        self.ax.set_ylabel("Caudal (m³/s)")
        self.canvas = FigureCanvasTkAgg(self.fig, master=bottom)
        self.canvas.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=4, pady=4)

        self.print_line("Aplicación lista. Ajusta 'a' y 'p', edita Áreas/Precipitaciones y pulsa Simular.")

    def print_line(self, s):
        self.txt.insert(tk.END, s + "\n")
        self.txt.see(tk.END)

    def clear_output(self):
        self.txt.delete("1.0", tk.END)
        self.ax.clear()
        self.ax.set_xlabel("Hora")
        self.ax.set_ylabel("Caudal (m³/s)")
        self.canvas.draw()
        self.print_line("Salida limpiada.")

    # -----------------
    # Editores
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
        # leer conteos
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
            messagebox.showwarning("Aviso", "La lista de áreas no coincide con 'a'. Ajustando longitud.")
            # trim or pad zeros
            if len(self.areas_km2) < a:
                self.areas_km2 += [0.0] * (a - len(self.areas_km2))
            else:
                self.areas_km2 = self.areas_km2[:a]
        if len(self.precips_mm) != p or len(self.ce) != p or len(self.cm) != p:
            messagebox.showwarning("Aviso", "Las listas de precipitación/coef no coinciden con 'p'. Ajustando longitud.")
            while len(self.precips_mm) < p:
                self.precips_mm.append(0.0)
                self.ce.append(0.5)
                self.cm.append(1.0)
            self.precips_mm = self.precips_mm[:p]
            self.ce = self.ce[:p]
            self.cm = self.cm[:p]

        # conversiones
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
        # Imprimir resultados
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

        # tabla en ventana (Treeview)
        self.show_table_and_plot(W, flows)

    def show_table_and_plot(self, W, flows):
        # crear nuevo toplevel con tabla y grafico
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

        # grafico (matplotlib)
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
    app = SAHApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()