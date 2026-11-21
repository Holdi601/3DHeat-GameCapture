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
