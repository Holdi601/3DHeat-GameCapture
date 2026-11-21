"""
Tests that need a library only the scanner or the offline reconstruction uses
(OpenCV, SciPy, PySide6, ONNX Runtime, PyTorch, ...) skip where it is not
installed, as on the CI that builds the lap recorders: a missing optional
library is not a failure of the code under test.
"""

from __future__ import annotations

import pytest

#: Top-level modules of the scanner's and the reconstruction's own requirements (requirements*.txt).
OPTIONAL = {
    "cv2", "scipy", "skimage", "PySide6", "shiboken6", "onnxruntime", "torch", "torchvision",
    "windows_capture", "rapidocr_onnxruntime", "pyclipper", "shapely", "yaml", "six",
    "transformers", "einops", "safetensors", "huggingface_hub", "vggt", "moderngl", "glcontext",
    "kornia", "kornia_rs", "PIL",
}


#: The scanner's core libraries; without them its code runs into a missing import deep in a worker
#: thread, which a test sees only as a scan that stopped early.
SCANNER_LIBS = ("cv2", "scipy", "skimage")
#: Parts of the package that need none of them: the lap recorders, the standalone app, the updater.
LIGHT = ("heat3d_capture.telemetry", "heat3d_capture.app", "heat3d_capture.standalone_spec", "heat3d_update")


def _scanner_missing() -> str | None:
    import importlib.util

    for m in SCANNER_LIBS:
        try:
            if importlib.util.find_spec(m) is None:
                return m
        except (ImportError, ValueError):
            return m
    return None


def _uses_scanner(path) -> bool:
    """A test file that imports any of the package beyond its light parts (or a test helper module)."""
    import ast

    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except (OSError, SyntaxError):
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level:  # the tests' own helpers (scene, hud_synth, locate_world) build scanner input
                return True
            names = [node.module or ""]
            if node.module == "heat3d_capture":
                names = [f"heat3d_capture.{a.name}" for a in node.names]
        elif isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        else:
            continue
        for name in names:
            if name == "heat3d_capture" or (name.startswith("heat3d_capture.") and not name.startswith(LIGHT)):
                return True
    return False


def pytest_collection_modifyitems(config, items):
    lib = _scanner_missing()
    if lib is None:
        return
    seen: dict[str, bool] = {}
    mark = pytest.mark.skip(reason=f"needs the scanner's libraries ({lib} is not installed; see requirements.txt)")
    for item in items:
        path = str(item.path)
        if path not in seen:
            seen[path] = _uses_scanner(path)
        if seen[path]:
            item.add_marker(mark)


def _missing(exc: BaseException | None) -> str | None:
    while exc is not None:
        if isinstance(exc, ModuleNotFoundError) and (exc.name or "").split(".")[0] in OPTIONAL:
            return exc.name.split(".")[0]
        exc = exc.__cause__ or exc.__context__
    return None


@pytest.hookimpl(hookwrapper=True)
def pytest_make_collect_report(collector):
    outcome = yield
    report = outcome.get_result()
    if report.failed and isinstance(collector, pytest.Module):
        text = str(report.longrepr)
        for name in OPTIONAL:
            if f"No module named '{name}'" in text or f"No module named '{name}." in text:
                report.outcome = "skipped"
                report.longrepr = (str(collector.path), 0, f"Skipped: needs {name}, which is not installed")
                break


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if call.excinfo is not None and report.failed:
        name = _missing(call.excinfo.value)
        if name:
            report.outcome = "skipped"
            report.longrepr = (str(item.path), item.location[1] or 0, f"Skipped: needs {name}, which is not installed")
