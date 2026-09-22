import pandas as pd
from .analysis import analyze_arrays

def load_excel(path, start_row=37, voltage_col=3, current_col=5, sheet_name=0, **kwargs):
    df = pd.read_excel(path, sheet_name=sheet_name, header=None, skiprows=start_row-1)
    cols = {"Voltage": voltage_col-1, "Raw_Current": current_col-1}
    data = pd.DataFrame({k: pd.to_numeric(df.iloc[:, c], errors="coerce") for k,c in cols.items()})
    before = len(data); data = data.dropna(subset=["Voltage", "Raw_Current"]).reset_index(drop=True)
    return data, before-len(data)

def analyze_file(path, settings):
    data, removed = load_excel(path, **settings)
    out = analyze_arrays(data.Voltage.to_numpy(), data.Raw_Current.to_numpy(), settings["area_cm2"], settings.get("multiply_minus_one", True), settings.get("incident_mw_cm2", 100.0))
    out["data"], out["removed"] = data, removed
    return out

def export_result(path, source_name, result, settings):
    summary = []
    for r in result["results"]:
        row = {"Filename": source_name, "Mask_Area_cm2": settings["area_cm2"], "Incident_Power_mW_cm2": settings.get("incident_mw_cm2",100), "Scan_Direction": r.name}
        row.update({k:v for k,v in r.to_dict().items() if k not in ("name","warnings")}); summary.append(row)
    summary_df = pd.DataFrame(summary)
    pdata = result["data"].copy() if "data" in result else pd.DataFrame({"Voltage":result["voltage"],"Raw_Current":result["raw_current"]})
    pdata["Corrected_Current"] = result["corrected_current"]; pdata["Current_Density_mA_cm2"] = result["current_density"]
    labels = [""]*len(pdata)
    for name, sv, sj in result["scans"]:
        n=len(sv); start=0 if not any(labels) else next(i for i,x in enumerate(labels) if not x)
        for i in range(start,min(start+n,len(labels))): labels[i]=name
    pdata["Scan_Direction"] = labels
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False); pdata.to_excel(writer, sheet_name="Processed_Data", index=False)

def batch_analyze(folder, settings, output_path):
    """Analyze every .xlsx in a folder and write one summary workbook."""
    from pathlib import Path
    rows = []
    output = Path(output_path).resolve()
    for source in sorted(Path(folder).glob("*.xlsx")):
        if source.resolve() == output or source.name.startswith("~$"):
            continue
        try:
            result = analyze_file(source, settings)
            for scan in result["results"]:
                rows.append({
                    "Filename": source.name, "Scan_Direction": scan.name,
                    "Voc_V": scan.voc, "Jsc_mA_cm2": scan.jsc,
                    "FF_percent": scan.ff, "PCE_percent": scan.pce,
                    "Warnings": "; ".join(scan.warnings or []), "Error": "",
                })
        except Exception as exc:
            rows.append({"Filename": source.name, "Scan_Direction": "", "Voc_V": None,
                         "Jsc_mA_cm2": None, "FF_percent": None, "PCE_percent": None,
                         "Warnings": "", "Error": str(exc)})
    if not rows:
        raise ValueError("No .xlsx files were found in the selected folder.")
    pd.DataFrame(rows).to_excel(output_path, index=False, engine="openpyxl")
    return len({row["Filename"] for row in rows}), sum(bool(row["Error"]) for row in rows)
