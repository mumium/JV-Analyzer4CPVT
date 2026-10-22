import tkinter as tk
import sys
from tkinter import font as tkfont
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from .io import analyze_file, export_result, batch_analyze
from .windows import configure_process, set_window_icons

class App(tk.Tk):
    def __init__(self):
        configure_process()
        super().__init__()
        self.title("JV Analyzer · MK Design")
        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()
        width = min(1200, max(320, screen_width - 80))
        height = min(740, max(240, screen_height - 100))
        self.geometry(f"{width}x{height}")
        self.minsize(min(560, width), min(360, height))
        self.result = None
        self.file = None
        assets = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)) / "assets"
        if sys.platform == "win32":
            self.iconbitmap(default=str(assets / "logo.ico"))
        else:
            self._app_icon = tk.PhotoImage(file=str(assets / "logo-window.png"))
            self.iconphoto(True, self._app_icon)
        self.vars={k:tk.StringVar(value=v) for k,v in {"start_row":"37","voltage_col":"3","current_col":"4","area_cm2":"0.1","incident_mw_cm2":"100"}.items()}; self.flip=tk.BooleanVar(value=True)
        # Reserve the status row before allocating space to the main content.
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.workspace = ttk.Frame(self)
        self.workspace.grid(row=0, column=0, sticky="nsew")
        self.workspace.rowconfigure(0, weight=1)
        self.workspace.columnconfigure(1, weight=1)
        self.status = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w").grid(
            row=1, column=0, sticky="ew"
        )

        # Sibling frames can move between the grid and notebook without losing
        # entered settings, plot navigation, or analysis results.
        self.settings_panel = ttk.Frame(self.workspace)
        self.plot_panel = ttk.Frame(self.workspace)
        self.results_panel = ttk.Frame(self.workspace, padding=8)
        self.notebook = ttk.Notebook(self.workspace)
        self.notebook.grid(row=0, column=1, sticky="nsew")
        self.notebook.add(self.plot_panel, text="JV curve")

        self.settings_panel.rowconfigure(0, weight=1)
        self.settings_panel.columnconfigure(0, weight=1)
        self.settings_canvas = tk.Canvas(self.settings_panel, highlightthickness=0, width=220)
        self.settings_canvas.grid(row=0, column=0, sticky="nsew")
        settings_scrollbar = ttk.Scrollbar(
            self.settings_panel, orient="vertical", command=self.settings_canvas.yview
        )
        settings_scrollbar.grid(row=0, column=1, sticky="ns")
        self.settings_canvas.configure(yscrollcommand=settings_scrollbar.set)
        left = ttk.Frame(self.settings_canvas, padding=8)
        self.settings_content = left
        settings_window = self.settings_canvas.create_window((0, 0), window=left, anchor="nw")
        left.bind("<Configure>", lambda event: self.settings_canvas.configure(
            scrollregion=self.settings_canvas.bbox("all")
        ))
        self.settings_canvas.bind("<Configure>", lambda event: self.settings_canvas.itemconfigure(
            settings_window, width=event.width
        ))
        for label,key in [("File",None),("Start row","start_row"),("Voltage column","voltage_col"),("Current column","current_col"),("Mask area (cm²)","area_cm2"),("Incident power (mW/cm²)","incident_mw_cm2")]:
            ttk.Label(left,text=label).pack(anchor="w",pady=(5,0))
            if key:
                entry=ttk.Entry(left,textvariable=self.vars[key],width=18); entry.pack(fill="x")
            else: self.file_label=ttk.Label(left,text="No file selected",wraplength=180); self.file_label.pack(anchor="w")
        ttk.Button(left,text="Choose Excel",command=self.choose).pack(fill="x",pady=8); ttk.Checkbutton(left,text="Current × -1",variable=self.flip).pack(anchor="w"); ttk.Button(left,text="Read and analyze",command=self.run).pack(fill="x",pady=8); ttk.Button(left,text="Export result",command=self.export).pack(fill="x"); ttk.Button(left,text="Batch analyze folder",command=self.batch).pack(fill="x",pady=4); ttk.Button(left,text="Save plot",command=self.save_plot).pack(fill="x")
        self.plot_panel.rowconfigure(0, weight=1)
        self.plot_panel.columnconfigure(0, weight=1)
        self.fig = Figure(figsize=(4, 3), dpi=100, layout="constrained")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Voltage (V)")
        self.ax.set_ylabel("Current Density (mA/cm²)")
        self.ax.grid(True, alpha=.3)
        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_panel)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_panel, pack_toolbar=False)
        # Hide the expanding coordinate label to keep all navigation buttons
        # accessible when the plot is narrow.
        self.toolbar._message_label.pack_forget()
        self.toolbar.grid(row=1, column=0, sticky="ew")
        self.toolbar.update()

        self.results_panel.rowconfigure(1, weight=1)
        self.results_panel.columnconfigure(0, weight=1)
        ttk.Label(self.results_panel, text="Results", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        self.text = tk.Text(self.results_panel, width=28, height=1, wrap="word")
        self.text.grid(row=1, column=0, sticky="nsew")
        result_scrollbar = ttk.Scrollbar(self.results_panel, command=self.text.yview)
        result_scrollbar.grid(row=1, column=1, sticky="ns")
        self.text.configure(yscrollcommand=result_scrollbar.set)

        # Use font measurements so breakpoints also adapt to display scaling.
        self.update_idletasks()
        unit = tkfont.nametofont("TkDefaultFont").measure("0")
        self._settings_width = max(220, left.winfo_reqwidth() + 8)
        self._results_width = max(260, 30 * unit + 32)
        self._plot_width = max(420, 48 * unit)
        self.settings_canvas.configure(width=self._settings_width)
        self._layout_mode = None
        self._layout_job = None
        self.bind("<Configure>", self._schedule_layout)
        self.bind("<MouseWheel>", self._scroll_settings, add="+")
        self.bind("<Button-4>", self._scroll_settings, add="+")
        self.bind("<Button-5>", self._scroll_settings, add="+")
        self._apply_layout(width)
        set_window_icons(self, assets / "logo.ico")

    def _schedule_layout(self, event):
        if event.widget is not self:
            return
        if self._layout_job is not None:
            self.after_cancel(self._layout_job)
        self._layout_job = self.after(80, self._apply_layout)

    def _apply_layout(self, width=None):
        self._layout_job = None
        width = self.winfo_width() if width is None else width
        sidebar_width = self._settings_width + self._plot_width + 40
        wide_width = sidebar_width + self._results_width
        mode = "wide" if width >= wide_width else "compact" if width >= sidebar_width else "tabs"
        if mode == self._layout_mode:
            return
        selected = self.notebook.select()
        for panel in (self.settings_panel, self.results_panel):
            if str(panel) in self.notebook.tabs():
                self.notebook.forget(panel)
            panel.grid_forget()
        if mode == "tabs":
            self.notebook.insert(0, self.settings_panel, text="Settings")
        else:
            self.settings_panel.grid(row=0, column=0, sticky="nsew")
        if mode == "wide":
            self.results_panel.grid(row=0, column=2, sticky="nsew")
        else:
            self.notebook.add(self.results_panel, text="Results")
        if selected in self.notebook.tabs():
            self.notebook.select(selected)
        # Notebook pages are siblings so they can also move into the grid.
        # Keep them above the notebook's background in the native window stack.
        for panel in (self.settings_panel, self.plot_panel, self.results_panel):
            panel.lift(self.notebook)
        self._layout_mode = mode
        self.canvas.draw_idle()

    def _scroll_settings(self, event):
        widget = event.widget
        while widget is not None and widget is not self.settings_panel:
            widget = widget.master
        if widget is None:
            return
        # Do not move short content out of view in a tall window.
        if self.settings_content.winfo_height() <= self.settings_canvas.winfo_height():
            return "break"
        if event.num in (4, 5):
            steps = -1 if event.num == 4 else 1
        else:
            steps = -int(event.delta / 120) if abs(event.delta) >= 120 else (-1 if event.delta > 0 else 1)
        self.settings_canvas.yview_scroll(steps, "units")
        return "break"
    def choose(self):
        p=filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")]);
        if p: self.file=p; self.file_label.config(text=Path(p).name); self.status.set("File selected")
    def settings(self):
        return {"start_row":int(self.vars["start_row"].get()),"voltage_col":int(self.vars["voltage_col"].get()),"current_col":int(self.vars["current_col"].get()),"area_cm2":float(self.vars["area_cm2"].get()),"incident_mw_cm2":float(self.vars["incident_mw_cm2"].get()),"multiply_minus_one":self.flip.get()}
    def run(self):
        try:
            if not self.file: raise ValueError("Choose an Excel file first")
            self.result=analyze_file(self.file,self.settings()); self.ax.clear(); self.ax.axhline(0,color="k",lw=.7); self.ax.axvline(0,color="k",lw=.7)
            for name,v,j in self.result["scans"]: self.ax.plot(v,j,".-",label=name)
            self.ax.set_xlabel("Voltage (V)"); self.ax.set_ylabel("Current Density (mA/cm²)"); self.ax.grid(True,alpha=.3); self.ax.legend(); self.show_results(); self.notebook.select(self.plot_panel); self.canvas.draw_idle(); self.status.set("Complete")
        except Exception as e: messagebox.showerror("Analysis error",str(e)); self.status.set("Error")
    def show_results(self):
        self.text.delete("1.0","end");
        for r in self.result["results"]: self.text.insert("end",f"{r.name}\nVoc: {r.voc:.5g} V\nJsc: {r.jsc:.5g} mA/cm²\nFF: {r.ff:.3f}%\nPCE: {r.pce:.3f}%\nWarnings: {'; '.join(r.warnings or ['None'])}\n\n")
    def export(self):
        if not self.result: return messagebox.showinfo("Export","Analyze a file first")
        p=filedialog.asksaveasfilename(defaultextension=".xlsx",initialfile="JV_analysis_results.xlsx");
        if p: export_result(p,Path(self.file).name,self.result,self.settings()); self.status.set("Exported")
    def batch(self):
        try:
            folder=filedialog.askdirectory(title="Select folder containing Excel files")
            if not folder: return
            output=filedialog.asksaveasfilename(defaultextension=".xlsx",initialdir=folder,initialfile="JV_analysis_results.xlsx",filetypes=[("Excel","*.xlsx")])
            if not output: return
            self.status.set("Batch processing..."); self.update_idletasks()
            count, errors=batch_analyze(folder,self.settings(),output)
            self.status.set(f"Batch complete: {count} files, {errors} errors")
            messagebox.showinfo("Batch complete",f"Processed {count} files.\nFiles with errors: {errors}\n\nSaved to:\n{output}")
        except Exception as e: messagebox.showerror("Batch error",str(e)); self.status.set("Batch error")
    def save_plot(self):
        if not self.result: return
        p=filedialog.asksaveasfilename(defaultextension=".png",filetypes=[("PNG","*.png"),("SVG","*.svg")]);
        if p: self.fig.savefig(p,dpi=300,bbox_inches="tight")

def main(): App().mainloop()
