"""
Reading text off the screen, locally.

RapidOCR runs the PaddleOCR detection and recognition models through ONNX
Runtime: no service, no upload, the frames never leave the machine. It is
imported only when text is actually read, so the rest of the package works
(and its tests run) without it.

Two settings differ from the library's defaults, both for HUD text: the
detector is not made to upscale a small crop to 736 pixels (the default),
which made it five times slower for nothing on text that is already large
enough; and the 180-degree classifier is off, since HUD text is never upside
down and the classifier now and then decided a name was.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np


@dataclass
class Text:
    """A line of text found in an image: its box (pixels of that image), the text and the model's confidence."""

    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    score: float

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def height(self) -> float:
        return self.y1 - self.y0


class NoOcr(RuntimeError):
    pass


class Reader:
    """The OCR models, loaded once. Safe to share between threads."""

    def __init__(self, *, limit: int = 960, gpu: bool = True):
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError as exc:  # pragma: no cover - depends on the install
            raise NoOcr(
                "reading the HUD needs rapidocr_onnxruntime: "
                "pip install --no-deps rapidocr_onnxruntime pyclipper Shapely PyYAML six"
            ) from exc
        self._ocr = RapidOCR(use_angle_cls=False)
        resize = self._ocr.text_detector.preprocess_op[0]
        resize.limit_side_len = limit
        resize.limit_type = "max"
        self.device = "cpu"
        if gpu:
            self._to_gpu()

    def _to_gpu(self) -> None:
        """Run both models on the graphics card through DirectML or CUDA, when ONNX Runtime has either."""
        try:
            import onnxruntime as ort
        except ImportError:  # pragma: no cover
            return
        have = ort.get_available_providers()
        chosen = [p for p in ("CUDAExecutionProvider", "DmlExecutionProvider") if p in have][:1]
        if not chosen:
            return
        opts = ort.SessionOptions()
        opts.log_severity_level = 3
        try:
            for wrap in (self._ocr.text_detector.infer, self._ocr.text_recognizer.session):
                path = wrap.session._model_path
                wrap.session = ort.InferenceSession(path, opts, providers=[chosen[0], "CPUExecutionProvider"])
            self.device = chosen[0].replace("ExecutionProvider", "")
        except Exception:  # pragma: no cover - a driver that will not load: the CPU sessions stay
            self.device = "cpu"

    def read(self, image: np.ndarray) -> list[Text]:
        """Every line of text in a BGR image."""
        result, _ = self._ocr(image)
        out = []
        for box, text, score in result or []:
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            out.append(Text(min(xs), min(ys), max(xs), max(ys), str(text), float(score)))
        return out

    def detect(self, image: np.ndarray) -> list[Text]:
        """Where the lines of text are, without reading them (`text` is empty)."""
        boxes, _ = self._ocr.text_detector(image)
        out = []
        for box in boxes if boxes is not None else []:
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            out.append(Text(float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys)), "", 0.0))
        out.sort(key=lambda t: (round(t.cy / 8), t.x0))
        return out

    def recognise(self, crops: list[np.ndarray]) -> list[tuple[str, float]]:
        """The text of each crop, which is already known to be one line."""
        if not crops:
            return []
        res, _ = self._ocr.text_recognizer(crops)
        return [(str(t), float(s)) for t, s in res]


#: What a player name can be made of on screen. Anything else in a read is the
#: recogniser making a character out of an icon edge.
_NAME_JUNK = re.compile(r"[^0-9A-Za-z_\-\.\[\]\(\) <>|#*!@$&+=~^]")


def clean_name(text: str) -> str:
    text = _NAME_JUNK.sub("", text)
    # Icons next to a name come through as dashes and dots at its ends.
    return text.strip(" -._|·").strip()


def similarity(a: str, b: str) -> float:
    """0..1, how alike two reads of a name are, forgiving the recogniser's usual confusions."""
    from difflib import SequenceMatcher

    def norm(s: str) -> str:
        s = s.lower()
        for x, y in (("0", "o"), ("1", "l"), ("i", "l"), ("|", "l"), ("5", "s"), ("8", "b"), ("rn", "m"), ("vv", "w"), (" ", "")):
            s = s.replace(x, y)
        return s

    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()
