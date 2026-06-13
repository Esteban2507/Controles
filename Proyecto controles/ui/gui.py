"""Módulo de interfaz gráfica."""
import sys
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import threading
import logging
from datetime import datetime

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.process import process_data
from ui.styles import get_status_color


logger = logging.getLogger(__name__)


class ProgressRedirector:
    """Redirige stdout a la GUI para mostrar progreso."""
    
    def __init__(self, string_var, progress_bar, root):
        self.string_var = string_var
        self.progress_bar = progress_bar
        self.root = root

    def write(self, string):
        s = string.strip()
        if s:
            self.root.after(0, self._update_gui, s)

    def _update_gui(self, s):
        if len(s) > 100:
            s_short = s[:97] + "..."
        else:
            s_short = s

        match = re.search(r"(\d)/8", s_short)
        if match:
            step = int(match.group(1))
            self.progress_bar["value"] = (step / 8.0) * 100
            self.string_var.set(s_short)
        else:
            if ">>>" not in s_short:
                self.string_var.set(s_short)

    def flush(self):
        pass


class ControlApp:
    """Aplicación principal de interfaz gráfica."""
    
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.root.title("Control de Facturas")
        self.root.geometry("1200x700")
        
        # Variables
        self.arca_path = tk.StringVar()
        self.cdp_path = tk.StringVar()
        self.e1_path = tk.StringVar()
        self.fecha_posting = tk.StringVar(value="Todas las fechas")
        self.status_var = tk.StringVar(value="Listo")
        self.last_out_path = None
        self.update_report_optional_var = tk.BooleanVar(value=True) # Nuevo: para controlar visibilidad del botón de actualizar
        
        # UI Setup
        self._create_widgets()
        
        # Traces para habilitar/deshabilitar el botón de actualizar dinámicamente
        self.arca_path.trace_add("write", lambda *args: self.check_update_btn_state())
        self.cdp_path.trace_add("write", lambda *args: self.check_update_btn_state())
        self.e1_path.trace_add("write", lambda *args: self.check_update_btn_state())
        
        # Redirect stdout
        sys.stdout = ProgressRedirector(self.status_var, self.progress, self.root)

    def _create_widgets(self):
        """Crea los widgets de la interfaz."""
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === Panel de entrada ===
        input_frame = ttk.LabelFrame(main_frame, text="Archivos de Entrada", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # ARCA
        ttk.Label(input_frame, text="ARCA:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(input_frame, textvariable=self.arca_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(input_frame, text="Examinar", command=self.select_arca).grid(row=0, column=2)
        
        # CDP
        ttk.Label(input_frame, text="CDP:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(input_frame, textvariable=self.cdp_path, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(input_frame, text="Examinar", command=self.select_cdp).grid(row=1, column=2)
        
        # E1
        ttk.Label(input_frame, text="E1:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(input_frame, textvariable=self.e1_path, width=50).grid(row=2, column=1, padx=5)
        ttk.Button(input_frame, text="Examinar", command=self.select_e1).grid(row=2, column=2)
        
        # Filtro de fecha
        ttk.Label(input_frame, text="Fecha Posting:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.fecha_combo = ttk.Combobox(input_frame, textvariable=self.fecha_posting, width=47, state="readonly")
        self.fecha_combo['values'] = ["Todas las fechas"]
        self.fecha_combo.grid(row=3, column=1, padx=5)
        
        # === Panel de ejecución ===
        exec_frame = ttk.Frame(main_frame)
        exec_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_run = ttk.Button(exec_frame, text="Ejecutar Procesamiento", command=self.run_process_thread)
        self.btn_run.pack(side=tk.LEFT, padx=5)
        
        self.btn_open = ttk.Button(exec_frame, text="Abrir Reporte", command=self.open_report, state=tk.DISABLED)
        self.btn_open.pack(side=tk.LEFT, padx=5)

        self.btn_update_report = ttk.Button(exec_frame, text="Actualizar", command=self.update_report, state=tk.DISABLED)
        self.btn_update_report.pack(side=tk.LEFT, padx=5)

        
        # === Progreso ===
        progress_frame = ttk.LabelFrame(main_frame, text="Progreso", padding=5)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        
        status_label = ttk.Label(progress_frame, textvariable=self.status_var, foreground="blue")
        status_label.pack(fill=tk.X, padx=5)
        
        # === Resultados (Tabla + Gráfico) ===
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tabla
        table_frame = ttk.LabelFrame(content_frame, text="Detalles de Errores")
        table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.tree_scroll_y = ttk.Scrollbar(table_frame)
        self.tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree_scroll_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        self.tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree = ttk.Treeview(table_frame, yscrollcommand=self.tree_scroll_y.set,
                                  xscrollcommand=self.tree_scroll_x.set, selectmode="extended")
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)
        
        # Gráfico
        self.chart_frame = ttk.LabelFrame(content_frame, text="Resumen Gráfico", width=400)
        self.chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(10, 0))
        self.chart_frame.pack_propagate(False)

    def check_update_btn_state(self):
        """Habilita o deshabilita el botón de actualizar según si hay archivos cargados."""
        if self.arca_path.get().strip() or self.cdp_path.get().strip() or self.e1_path.get().strip():
            self.btn_update_report.config(state=tk.NORMAL)
        else:
            self.btn_update_report.config(state=tk.DISABLED)

    def select_arca(self):
        """Selecciona archivo ARCA."""
        path = filedialog.askopenfilename(title="Seleccionar Archivo ARCA", 
                                         filetypes=[("Excel", "*.xlsx *.xls")])
        if path:
            self.arca_path.set(path)

    def select_cdp(self):
        """Selecciona archivo CDP y carga fechas."""
        path = filedialog.askopenfilename(title="Seleccionar Archivo CDP",
                                         filetypes=[("Excel", "*.xlsx *.xls")])
        if path:
            self.cdp_path.set(path)
            self.load_fechas_posting(path)

    def select_e1(self):
        """Selecciona archivo E1."""
        path = filedialog.askopenfilename(title="Seleccionar Archivo E1",
                                         filetypes=[("Excel", "*.xlsx *.xls")])
        if path:
            self.e1_path.set(path)

    def load_fechas_posting(self, cdp_path):
        """Carga fechas de posting del archivo CDP."""
        def _is_posting_column(col_name):
            col_lower = str(col_name).lower()
            return "posting" in col_lower and ("fecha" in col_lower or "date" in col_lower or "posting" in col_lower)

        try:
            xls = pd.ExcelFile(cdp_path, engine="openpyxl")
            sheet_names = xls.sheet_names
            candidate_sheets = [sheet for sheet in ["CDP"] + sheet_names if sheet in sheet_names]

            col_fecha_posting = None
            sheet_con_found = None
            for sheet in candidate_sheets:
                try:
                    df_temp = pd.read_excel(cdp_path, sheet_name=sheet, nrows=0, engine="openpyxl")
                except Exception:
                    continue
                for col in df_temp.columns:
                    if _is_posting_column(col):
                        col_fecha_posting = col
                        sheet_con_found = sheet
                        break
                if col_fecha_posting:
                    break

            if col_fecha_posting:
                df_fechas = pd.read_excel(cdp_path, sheet_name=sheet_con_found, usecols=[col_fecha_posting], engine="openpyxl")
                fechas = pd.to_datetime(df_fechas[col_fecha_posting], errors='coerce').dropna().dt.date.unique()
                fechas_ordenadas = sorted(fechas)

                opciones = ["Todas las fechas"] + [fecha.strftime("%Y-%m-%d") for fecha in fechas_ordenadas]
                self.fecha_combo['values'] = opciones
                self.fecha_posting.set("Todas las fechas")
                print(f"Fechas de posting cargadas: {len(fechas_ordenadas)} fechas únicas")
            else:
                print(f"[AVISO] No se encontró columna de posting date")
                self.fecha_combo['values'] = ["Todas las fechas"]
                self.fecha_posting.set("Todas las fechas")
        
        except Exception as e:
            logger.error(f"Error al cargar fechas: {e}", exc_info=True)
            print(f"Error al cargar fechas: {e}")
            self.fecha_combo['values'] = ["Todas las fechas"]
            self.fecha_posting.set("Todas las fechas")

    def run_process_thread(self):
        """Ejecuta el procesamiento en un thread separado."""
        if not self.arca_path.get() or (not self.cdp_path.get() and not self.e1_path.get()):
            messagebox.showwarning("Advertencia", "Debe seleccionar ARCA y al menos uno de CDP/E1.")
            return
        
        self.btn_run.config(state=tk.DISABLED)
        self.btn_open.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.status_var.set("Iniciando proceso...")
        self.tree.delete(*self.tree.get_children())
        
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        thread = threading.Thread(target=self.run_process)
        thread.daemon = True
        thread.start()

    def run_process(self):
        """Ejecuta el procesamiento."""
        try:
            fecha_filtro = None
            if self.fecha_posting.get() != "Todas las fechas":
                fecha_filtro = datetime.strptime(self.fecha_posting.get(), "%Y-%m-%d").date()
            
            out_path, df_resumen, df_err = process_data(
                self.config,
                self.arca_path.get(),
                self.cdp_path.get(),
                self.e1_path.get(),
                fecha_filtro
            )
            
            self.root.after(0, self.process_success, out_path, df_resumen, df_err)
        
        except Exception as e:
            logger.error("Error crítico", exc_info=True)
            self.root.after(0, self.process_error, str(e))

    def process_success(self, out_path, df_resumen, df_err):
        """Maneja procesamiento exitoso."""
        self.progress["value"] = 100
        self.status_var.set(f"Proceso finalizado. Reporte: {Path(out_path).name}")
        self.btn_run.config(state=tk.NORMAL)
        
        self.last_out_path = out_path
        self.btn_open.config(state=tk.NORMAL)
        
        self.draw_chart(df_resumen)
        self.populate_treeview(df_err)
        
        try:
            import os
            os.startfile(Path(out_path).parent)
        except Exception:
            pass
        
        messagebox.showinfo("Éxito", "Procesamiento completado correctamente.")

    def open_report(self):
        """Abre el reporte generado."""
        if hasattr(self, 'last_out_path') and self.last_out_path:
            try:
                import os
                os.startfile(self.last_out_path)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir:\n{e}")

    def populate_treeview(self, df_err):
        """Llena la tabla de errores."""
        self.tree.delete(*self.tree.get_children())
        
        if df_err.empty:
            return
        
        columns = list(df_err.columns)
        self.tree["columns"] = columns
        self.tree["show"] = "headings"
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, minwidth=50)
        
        for _, row in df_err.iterrows():
            vals = [str(x) if not pd.isna(x) else "" for x in row.tolist()]
            self.tree.insert("", tk.END, values=vals)

    def process_error(self, err_msg):
        """Maneja errores en procesamiento."""
        print(f"\n[ERROR] {err_msg}")
        self.btn_run.config(state=tk.NORMAL)
        messagebox.showerror("Error", f"Error en la ejecución:\n{err_msg}")

    def draw_chart(self, df_resumen):
        """Dibuja gráfico de resumen."""
        if df_resumen.empty:
            ttk.Label(self.chart_frame, text="Sin datos para graficar").pack(pady=20)
            return
        
        colors_cfg = self.config.get("dashboard_colors", {})
        
        labels = df_resumen["Status"].tolist()
        sizes = df_resumen["Cantidad"].tolist()
        colors = [get_status_color(st, colors_cfg) for st in labels]
        
        fig = Figure(figsize=(4, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
        ax.axis('equal')
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_report(self):
        """Actualiza los Excels ingresados refrescando sus consultas y tablas."""
        # Obtener rutas ingresadas y no vacías
        paths = []
        for p_var in [self.arca_path, self.cdp_path, self.e1_path]:
            val = p_var.get().strip()
            if val:
                paths.append(val)
                
        if not paths:
            messagebox.showwarning("Advertencia", "No hay archivos cargados para actualizar.")
            return

        # Desactivar controles para evitar ejecuciones concurrentes
        self.btn_run.config(state=tk.DISABLED)
        self.btn_update_report.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.status_var.set("Iniciando actualización de archivos...")

        # Iniciar el hilo de actualización
        thread = threading.Thread(target=self._run_excel_refresh, args=(paths,))
        thread.daemon = True
        thread.start()

    def _run_excel_refresh(self, paths):
        """Método auxiliar que ejecuta el refresco de Excel COM en segundo plano."""
        from utils.excel import refresh_excel_workbooks
        
        def update_progress(msg):
            # Imprimir en consola para que sea redirigido por el redirector
            print(f">>> {msg}")
            # Actualizar el estado de la barra y texto de progreso en el hilo principal
            self.root.after(0, self._update_refresh_gui_state, msg)

        try:
            refresh_excel_workbooks(paths, progress_callback=update_progress)
            self.root.after(0, self._on_refresh_success)
        except Exception as e:
            self.root.after(0, self._on_refresh_error, str(e))

    def _update_refresh_gui_state(self, msg):
        """Actualiza el texto de estado y avanza de manera progresiva la barra de progreso."""
        self.status_var.set(msg)
        # Incrementar un poco el valor de la barra según la fase del mensaje
        if "Abriendo" in msg:
            self.progress["value"] = min(self.progress["value"] + 10, 80)
        elif "Refrescando" in msg:
            self.progress["value"] = min(self.progress["value"] + 15, 85)
        elif "Guardando" in msg:
            self.progress["value"] = min(self.progress["value"] + 5, 90)

    def _on_refresh_success(self):
        """Acciones a tomar tras finalizar con éxito la actualización."""
        self.progress["value"] = 100
        self.status_var.set("Listo")
        self.btn_run.config(state=tk.NORMAL)
        self.check_update_btn_state()
        messagebox.showinfo("Éxito", "Los archivos Excel ingresados se actualizaron correctamente.")

    def _on_refresh_error(self, err_msg):
        """Acciones a tomar en caso de error durante la actualización."""
        self.progress["value"] = 0
        self.status_var.set("Error al actualizar")
        self.btn_run.config(state=tk.NORMAL)
        self.check_update_btn_state()
        messagebox.showerror("Error", f"Error al actualizar los archivos Excel:\n{err_msg}")

