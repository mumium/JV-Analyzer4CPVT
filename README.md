# JV Analyzer

离线分析钙钛矿太阳能电池 JV 数据。默认从第 37 行读取，第 3 列为电压、第 5 列为电流，电流默认乘以 -1。程序不读取 Excel 功率列。

## 运行

```powershell
python main.py
```

GUI 支持 Excel 选择、列/行配置、mask 面积、入射光功率、正反扫识别、JV 曲线、结果导出、批量分析和 PNG/SVG 保存。Jsc 与 Voc 使用零点附近局部线性插值；FF 和 PCE 由 JV 曲线有效发电区间内的最大 `V×J` 计算。原始数据不会被修改。

批量处理时点击 `Batch analyze folder`，选择包含 `.xlsx` 数据的文件夹，再指定汇总文件位置。程序会对每个文件分别输出正扫/反扫的 Voc、Jsc、FF、PCE；单个文件失败不会中断整批处理，错误会记录在汇总表中。

## 离线部署

有网电脑：`pip download -r requirements.txt -d packages`

离线电脑：`pip install --no-index --find-links=packages -r requirements.txt`

打包：运行 `build_exe.bat`，生成 `dist\JV_Analyzer.exe`。
