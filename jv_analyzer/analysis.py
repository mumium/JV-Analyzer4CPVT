from dataclasses import dataclass, asdict
from typing import Optional
import numpy as np

@dataclass
class ScanResult:
    name: str
    voc: Optional[float] = None
    jsc: Optional[float] = None
    ff: Optional[float] = None
    pce: Optional[float] = None
    vmpp: Optional[float] = None
    jmpp: Optional[float] = None
    pmax: Optional[float] = None
    warnings: list[str] = None
    def to_dict(self): return asdict(self)

def _interp_at_x(x, y, target=0.0):
    x, y = np.asarray(x, float), np.asarray(y, float)
    exact = np.flatnonzero(np.isclose(x, target, atol=1e-12))
    if exact.size: return float(y[exact[0]])
    order = np.argsort(x)
    x, y = x[order], y[order]
    idx = np.where((x[:-1] <= target) & (x[1:] >= target))[0]
    if not idx.size: return None
    i = idx[0]
    if x[i+1] == x[i]: return float(np.mean(y[i:i+2]))
    return float(y[i] + (target-x[i]) * (y[i+1]-y[i])/(x[i+1]-x[i]))

def _interp_x_at_y(x, y, target=0.0):
    x, y = np.asarray(x, float), np.asarray(y, float)
    exact = np.flatnonzero(np.isclose(y, target, atol=1e-12))
    if exact.size: return float(x[exact[0]])
    candidates = []
    for i in range(len(y)-1):
        if (y[i] <= target <= y[i+1]) or (y[i] >= target >= y[i+1]):
            if y[i+1] != y[i]: candidates.append(x[i] + (target-y[i])*(x[i+1]-x[i])/(y[i+1]-y[i]))
    if not candidates: return None
    positive = [v for v in candidates if v >= 0]
    return float(min(positive, key=abs) if positive else min(candidates, key=abs))

def split_scans(v, j, tolerance=1e-12):
    v, j = np.asarray(v, float), np.asarray(j, float)
    dv = np.diff(v)
    signs = np.sign(np.where(np.abs(dv) <= tolerance, 0, dv))
    nonzero = np.flatnonzero(signs)
    if nonzero.size < 2: return [("Scan 1", v, j)]
    direction = signs[nonzero[0]]
    turn = None
    for k in nonzero[1:]:
        if signs[k] != direction:
            turn = k + 1; break
    if turn is None or turn < 3 or len(v)-turn < 3: return [("Scan 1", v, j)]
    first = ("Reverse scan" if direction < 0 else "Forward scan", v[:turn], j[:turn])
    second = ("Forward scan" if direction < 0 else "Reverse scan", v[turn-1:], j[turn-1:])
    return [first, second]

def analyze_scan(name, v, j, area_cm2, incident_mw_cm2=100.0, power_density=None):
    if area_cm2 <= 0 or incident_mw_cm2 <= 0: raise ValueError("Area and incident power must be positive")
    v, j = np.asarray(v, float), np.asarray(j, float)
    warnings = []
    jsc = _interp_at_x(v, j)
    voc = _interp_x_at_y(v, j)
    if jsc is None: warnings.append("Cannot reliably calculate Jsc: V=0 is outside the scan range.")
    if voc is None: warnings.append("Cannot reliably calculate Voc: no J=0 crossing found.")
    valid = np.isfinite(v) & np.isfinite(j)
    if voc is not None: valid &= (v >= 0) & (v <= voc)
    p = np.asarray(power_density, float) if power_density is not None else v * j
    valid &= p >= 0
    if not np.any(valid): warnings.append("No valid power-producing region found."); mpp = None
    else:
        k = np.nanargmax(np.where(valid, p, np.nan)); mpp = (float(v[k]), float(j[k]), float(p[k]))
    vmpp, jmpp, pmax = mpp if mpp else (None, None, None)
    ff = (pmax/(voc*jsc)*100) if pmax is not None and voc and jsc else None
    pce = (pmax/incident_mw_cm2*100) if pmax is not None else None
    if voc is not None and voc <= 0: warnings.append("Voc is not positive.")
    if jsc is not None and jsc <= 0: warnings.append("Jsc is not positive after sign correction.")
    if ff is not None and not 0 <= ff <= 100: warnings.append("FF is outside 0–100%.")
    return ScanResult(name, voc, jsc, ff, pce, vmpp, jmpp, pmax, warnings)

def analyze_arrays(v, current_a, area_cm2, multiply_minus_one=True, incident_mw_cm2=100.0, excel_power=None, mpp_method="calculated"):
    current_a = np.asarray(current_a, float)
    corrected = -current_a if multiply_minus_one else current_a
    j = corrected * 1000.0 / area_cm2
    scans = split_scans(v, j)
    results = []
    for name, sv, sj in scans:
        power_density = None
        if mpp_method == "excel" and excel_power is not None:
            n = len(sv); start = 0 if not results else len(v) - len(sv)
            power_density = np.asarray(excel_power[start:start+n], float)
            if not np.isfinite(power_density).any(): power_density = None
        results.append(analyze_scan(name, sv, sj, area_cm2, incident_mw_cm2, power_density))
    return {"voltage": np.asarray(v), "raw_current": current_a, "corrected_current": corrected,
            "current_density": j, "scans": [(n, sv, sj) for n, sv, sj in scans], "results": results}
