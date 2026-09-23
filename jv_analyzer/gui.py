import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from .io import analyze_file, export_result, batch_analyze

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("JV Analyzer"); self.geometry("1080x600"); self.result=None; self.file=None
        self.vars={k:tk.StringVar(value=v) for k,v in {"start_row":"37","voltage_col":"3","current_col":"4","area_cm2":"0.1","incident_mw_cm2":"100"}.items()}; self.flip=tk.BooleanVar(value=True)
        left=ttk.Frame(self,padding=8); left.pack(side="left",fill="y"); center=ttk.Frame(self); center.pack(side="left",fill="both",expand=True); right=ttk.Frame(self,padding=8); right.pack(side="right",fill="y")
        for label,key in [("File",None),("Start row","start_row"),("Voltage column","voltage_col"),("Current column","current_col"),("Mask area (cm²)","area_cm2"),("Incident power (mW/cm²)","incident_mw_cm2")]:
            ttk.Label(left,text=label).pack(anchor="w",pady=(5,0))
            if key:
                entry=ttk.Entry(left,textvariable=self.vars[key],width=18); entry.pack(anchor="w")
            else: self.file_label=ttk.Label(left,text="No file selected",wraplength=180); self.file_label.pack(anchor="w")
        ttk.Button(left,text="Choose Excel",command=self.choose).pack(fill="x",pady=8); ttk.Checkbutton(left,text="Current × -1",variable=self.flip).pack(anchor="w"); ttk.Button(left,text="Read and analyze",command=self.run).pack(fill="x",pady=8); ttk.Button(left,text="Export result",command=self.export).pack(fill="x"); ttk.Button(left,text="Batch analyze folder",command=self.batch).pack(fill="x",pady=4); ttk.Button(left,text="Save plot",command=self.save_plot).pack(fill="x")
        self.fig=Figure(figsize=(7,6),dpi=100); self.ax=self.fig.add_subplot(111); self.ax.set_xlabel("Voltage (V)"); self.ax.set_ylabel("Current Density (mA/cm²)"); self.ax.grid(True,alpha=.3); self.canvas=FigureCanvasTkAgg(self.fig,center); self.canvas.get_tk_widget().pack(fill="both",expand=True); NavigationToolbar2Tk(self.canvas,center).update()
        ttk.Label(right,text="Results",font=("Segoe UI",12,"bold")).pack(anchor="w"); self.text=tk.Text(right,width=34,height=34); self.text.pack(fill="both",expand=True)
        self.status=tk.StringVar(value="Ready"); ttk.Label(self,textvariable=self.status,relief="sunken",anchor="w").pack(side="bottom",fill="x")
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
            self.ax.set_xlabel("Voltage (V)"); self.ax.set_ylabel("Current Density (mA/cm²)"); self.ax.grid(True,alpha=.3); self.ax.legend(); self.canvas.draw(); self.show_results(); self.status.set("Complete")
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
