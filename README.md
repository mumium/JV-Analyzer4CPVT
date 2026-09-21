# JV Analyzer

离线分析钙钛矿太阳能电池 JV 数据。默认从第 37 行读取，电压/电流/功率列为 3/5/6，电流默认乘以 -1。

## 运行

```powershell
python main.py
```

GUI 支持 Excel 选择、列/行配置、mask 面积、入射光功率、正反扫识别、JV 曲线、结果导出和 PNG/SVG 保存。Jsc 与 Voc 使用零点附近局部线性插值。MPP 默认使用有效发电区间中的最大 `V×J` 点；如文件有功率列，可将 MPP power source 设为 `excel`，并填写功率列号。没有功率列时将功率列号留空并使用 `calculated`。原始数据不会被修改。

## 离线部署

有网电脑：`pip download -r requirements.txt -d packages`

离线电脑：`pip install --no-index --find-links=packages -r requirements.txt`

打包：运行 `build_exe.bat`，生成 `dist\JV_Analyzer.exe`。
