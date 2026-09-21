import numpy as np
from jv_analyzer.analysis import analyze_arrays, split_scans

def test_units_and_parameters():
    v=np.r_[np.linspace(1.1,-.1,25), np.linspace(-.1,1.1,25)[1:]]
    j=20*(1-v/1.0); current=-j*0.1/1000
    out=analyze_arrays(v,current,0.1,True,100)
    assert len(out["results"])==2
    assert abs(out["results"][0].jsc-20)<1

def test_split_is_not_half():
    v=np.r_[np.linspace(1,-.2,5),np.linspace(-.2,1,9)[1:]]
    assert len(split_scans(v,np.ones_like(v)))==2
