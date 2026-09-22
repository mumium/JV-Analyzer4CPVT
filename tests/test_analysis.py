import numpy as np
import pandas as pd
from pathlib import Path
from tempfile import TemporaryDirectory
from jv_analyzer.analysis import analyze_arrays, split_scans
from jv_analyzer.io import batch_analyze

def test_units_and_parameters():
    v=np.r_[np.linspace(1.1,-.1,25), np.linspace(-.1,1.1,25)[1:]]
    j=20*(1-v/1.0); current=-j*0.1/1000
    out=analyze_arrays(v,current,0.1,True,100)
    assert len(out["results"])==2
    assert abs(out["results"][0].jsc-20)<1

def test_split_is_not_half():
    v=np.r_[np.linspace(1,-.2,5),np.linspace(-.2,1,9)[1:]]
    assert len(split_scans(v,np.ones_like(v)))==2

def test_batch_without_power_column():
    with TemporaryDirectory() as folder:
        v=np.r_[np.linspace(1.1,-.1,25),np.linspace(-.1,1.1,25)[1:]]
        j=20*(1-v); current=-j*0.1/1000
        table=pd.DataFrame(np.nan,index=range(36+len(v)),columns=range(5))
        table.iloc[36:,2]=v; table.iloc[36:,4]=current
        source=Path(folder)/"sample.xlsx"; output=Path(folder)/"results.xlsx"
        table.to_excel(source,index=False,header=False)
        count,errors=batch_analyze(folder,{"start_row":37,"voltage_col":3,"current_col":5,"area_cm2":0.1,"incident_mw_cm2":100,"multiply_minus_one":True},output)
        result=pd.read_excel(output)
        assert count==1 and errors==0 and len(result)==2
        assert set(["Voc_V","Jsc_mA_cm2","FF_percent","PCE_percent"]).issubset(result.columns)
