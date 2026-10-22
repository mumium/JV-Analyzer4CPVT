"""Exercise the bundled application without external data or network access."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import traceback


def run(report_path):
    report = {"ok": False, "checks": []}
    app = None
    try:
        import numpy as np
        import pandas as pd
        from .gui import App
        from .io import analyze_file, batch_analyze, export_result

        app = App()
        app.update()
        report["window_title"] = app.title()
        from .windows import taskbar_icon_size
        icon_size = taskbar_icon_size(app)
        if icon_size is not None:
            if icon_size != (256, 256):
                raise AssertionError(f"Taskbar ICON_BIG must be 256 px, got {icon_size}")
            report["taskbar_icon_size"] = list(icon_size)
        app.withdraw()
        report["checks"].append("GUI, TkAgg backend and bundled icons")
        settings = app.settings()
        with TemporaryDirectory(prefix="jv-offline-test-") as folder:
            folder = Path(folder)
            voltage = np.r_[np.linspace(1.1, -0.1, 25), np.linspace(-0.1, 1.1, 25)[1:]]
            current = -20 * (1 - voltage) * settings["area_cm2"] / 1000
            table = pd.DataFrame(np.nan, index=range(36 + len(voltage)), columns=range(5))
            table.iloc[36:, settings["voltage_col"] - 1] = voltage
            table.iloc[36:, settings["current_col"] - 1] = current
            source = folder / "sample.xlsx"
            table.to_excel(source, index=False, header=False, engine="openpyxl")
            result = analyze_file(source, settings)
            if len(result["results"]) != 2:
                raise AssertionError("Expected forward and reverse scans")
            for scan in result["results"]:
                if not (abs(scan.jsc - 20) < 0.01 and abs(scan.voc - 1) < 0.01
                        and abs(scan.ff - 25) < 0.2 and abs(scan.pce - 5) < 0.05):
                    raise AssertionError(f"Unexpected JV parameters: {scan}")
            report["checks"].append("Excel reading and forward/reverse JV parameters")

            app.file, app.result = str(source), result
            app.show_results()
            for name, v, j in result["scans"]:
                app.ax.plot(v, j, label=name)
            app.canvas.draw()
            for extension in ("png", "svg"):
                image = folder / f"curve.{extension}"
                app.fig.savefig(image)
                if image.stat().st_size == 0:
                    raise AssertionError(f"Empty {extension} plot")
            report["checks"].append("Result display and PNG/SVG export")

            exports = folder / "exports"
            exports.mkdir()
            output = exports / "result.xlsx"
            export_result(output, source.name, result, settings)
            with pd.ExcelFile(output, engine="openpyxl") as workbook:
                if workbook.sheet_names != ["Summary", "Processed_Data"]:
                    raise AssertionError("Missing exported worksheets")
                if len(pd.read_excel(workbook, sheet_name="Summary")) != 2:
                    raise AssertionError("Missing exported scan results")
            report["checks"].append("Excel result export and readback")

            batch_output = exports / "batch.xlsx"
            count, errors = batch_analyze(folder, settings, batch_output)
            if (count, errors) != (1, 0) or len(pd.read_excel(batch_output)) != 2:
                raise AssertionError("Unexpected batch results")
            report["checks"].append("Batch analysis and summary export")
        report["ok"] = True
    except Exception:
        report["error"] = traceback.format_exc()
    finally:
        if app is not None:
            app.destroy()
    Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if report["ok"] else 1
