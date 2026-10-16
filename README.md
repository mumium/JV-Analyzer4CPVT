# JV Analyzer

<img src="assets/logo.png" width="96" alt="JV Analyzer 图标">

离线分析钙钛矿太阳能电池 JV 数据。界面默认从第 37 行读取，第 3 列为电压、第 4 列为电流（可修改），电流默认乘以 -1。程序不读取 Excel 功率列。

## Windows 单文件版（推荐）

在有网电脑上从 [GitHub Releases](https://github.com/mumium/JV-Analyzer4CPVT/releases/latest) 下载 **JV_Analyzer.exe**，再通过公司允许的方式复制到离线电脑，双击即可运行。适用于 Windows 10/11 64 位。

- 只需复制这一个 exe，无需安装 Python、Microsoft Excel 或额外依赖，也无需管理员权限。
- Excel 读取、JV 分析、批量处理、Excel 导出和 PNG/SVG 绘图均在本地完成，程序无需联网。
- 单文件程序启动时会将内置运行环境解压到系统临时目录，首次启动可能需要几秒；无需把 exe 放在可写目录，但临时目录和导出目录需要可写。
- 选择 `.xlsx` 数据文件后，确认起始行、电压/电流列、mask 面积和光照功率，再点击 `Read and analyze`。电流输入单位为 A。
- Releases 同时提供 `SHA256SUMS.txt`，可用 PowerShell 的 `Get-FileHash .\JV_Analyzer.exe -Algorithm SHA256` 校验文件。

## 运行

```powershell
python main.py
```

GUI 支持 Excel 选择、列/行配置、mask 面积、入射光功率、正反扫识别、JV 曲线、结果导出、批量分析和 PNG/SVG 保存。Jsc 与 Voc 使用零点附近局部线性插值；FF 和 PCE 由 JV 曲线有效发电区间内的最大 `V×J` 计算。原始数据不会被修改。

界面会根据屏幕大小设置初始窗口，并随窗口宽度自动调整布局：宽窗口同时显示参数、曲线和结果；较窄窗口通过 `JV curve` / `Results` 标签切换；更窄时参数也收纳到 `Settings` 标签。参数区和结果区支持滚动，小屏幕下仍可访问全部操作。调整窗口不会清空已输入的参数或分析结果。

批量处理时点击 `Batch analyze folder`，选择包含 `.xlsx` 数据的文件夹，再指定汇总文件位置。程序会对每个文件分别输出正扫/反扫的 Voc、Jsc、FF、PCE；单个文件失败不会中断整批处理，错误会记录在汇总表中。

## 源码部署与打包

v1.0.2 恢复并保留原始 logo，采用“钙钛矿器件模拟工作台”的处理方式：ICO 包含 16–256 px 共 14 档尺寸；窗口映射后显式加载原图的 256 px 图标作为 `ICON_BIG`，供任务栏和 Alt+Tab 缩小使用，避免放大 32 px 窗口图标。标题栏独立使用系统小图标，Windows 应用标识保持固定。exe 自检同时检查运行中的大图标确为 256×256 px。

以下步骤仅供开发或自行构建，使用单文件版无需执行。

本次发布使用 Windows x64 / Python 3.13 构建；完整构建依赖版本记录在 `requirements-build.txt`。

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\build_exe.bat
```

构建使用版本库中的 `packaging/JV_Analyzer.spec`，包含 Python、Tk/Tcl、NumPy、pandas、openpyxl、Matplotlib、字体和程序图标。脚本会直接运行生成的 exe 做自检，通过后输出 `dist\JV_Analyzer.exe` 和 `dist\self-test.json`。自动化调用可使用 `build_exe.bat --no-pause`。

如需在离线开发电脑安装源码依赖，应在相同 Windows 架构和 Python 版本的有网电脑上下载：

有网电脑：`pip download -r requirements.txt -d packages`

离线电脑：`pip install --no-index --find-links=packages -r requirements.txt`

单文件版也支持自检（会短暂初始化窗口，生成临时测试数据，结束后自动清理）：

```powershell
Start-Process -FilePath .\JV_Analyzer.exe -ArgumentList '--self-test self-test.json' -Wait
Get-Content .\self-test.json
```

自检覆盖窗口及图标加载、Excel 读取、正反扫参数、结果显示、PNG/SVG 保存、Excel 导出回读和批量分析。`"ok": true` 表示全部通过。

图标原稿为 `assets/logo.png`。运行 `python packaging/build_icons.py`（需要 Pillow）可重新生成 `assets/logo.ico` 和 `assets/logo-window.png`，不会修改原稿或重画图案，然后重新打包即可。
