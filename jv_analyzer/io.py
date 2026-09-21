from pathlib import Path
import pandas as pd
from .analysis import analyze_arrays

def load_excel(path, start_row=37, voltage_col=3, current_col=5, power_col=None, sheet_name=0, **kwargs):
    df = pd.read_excel(path, sheet_name=sheet_name, header=None, skiprows=start_row-1)
    cols = {"Voltage": voltage_col-1, "Raw_Current": current_col-1}
    if power_col: cols["Excel_Power"] = power_col-1
    data = pd.DataFrame({k: pd.to_numeric(df.iloc[:, c], errors="coerce") for k,c in cols.items()})
    before = len(data); data = data.dropna(subset=["Voltage", "Raw_Current"]).reset_index(drop=True)
    if "Excel_Power" in data: data["Excel_Power"] = pd.to_numeric(data["Excel_Power"], errors="coerce")
    return data, before-len(data)

def analyze_file(path, settings):
    data, removed = load_excel(path, **settings)
    use_power = settings.get("mpp_method") == "excel"
    excel_power = data["Excel_Power"].to_numpy() if use_power and "Excel_Power" in data else None
    out = analyze_arrays(data.Voltage.to_numpy(), data.Raw_Current.to_numpy(), settings["area_cm2"], settings.get("multiply_minus_one", True), settings.get("incident_mw_cm2", 100.0), excel_power, settings.get("mpp_method", "calculated"))
    out["data"], out["removed"] = data, removed
    return out

def export_result(path, source_name, result, settings):
    summary = []
    for r in result["results"]:
        row = {"Filename": source_name, "Mask_Area_cm2": settings["area_cm2"], "Incident_Power_mW_cm2": settings.get("incident_mw_cm2",100), "Scan_Direction": r.name}
        row.update({k:v for k,v in r.to_dict().items() if k not in ("name","warnings")}); summary.append(row)
    summary_df = pd.DataFrame(summary)
    pdata = result["data"].copy() if "data" in result else pd.DataFrame({"Voltage":result["voltage"],"Raw_Current":result["raw_current"]})
    pdata["Corrected_Current"] = result["corrected_current"]; pdata["Current_Density_mA_cm2"] = result["current_density"]; pdata["Calculated_Power_Density_mW_cm2"] = result["voltage"]*result["current_density"]
    labels = [""]*len(pdata)
    for name, sv, sj in result["scans"]:
        n=len(sv); start=0 if not any(labels) else next(i for i,x in enumerate(labels) if not x)
        for i in range(start,min(start+n,len(labels))): labels[i]=name
    pdata["Scan_Direction"] = labels
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False); pdata.to_excel(writer, sheet_name="Processed_Data", index=False)
