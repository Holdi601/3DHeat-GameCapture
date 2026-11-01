"""
The HUD's pieces out of a recording, a few times a second, without decoding 4K into Python.

A 20-minute 4K recording is 72,000 frames of 25 MB each. Python never sees
them: ffmpeg decodes (on the GPU when there is one), drops to the sampling rate,
cuts out the profile's regions and stacks them into one small picture per
sample, and only that crosses the pipe. Decoding is the floor on the run time -
every frame of an H.264 stream has to be decoded to reach the next - and on an
NVIDIA card it runs at several times real time.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np

from .profiles import Profile, Region


@dataclass
class VideoInfo:
    width: int
    height: int
    fps: float
    duration: float


def probe(path: Path) -> VideoInfo:
    """Size, frame rate and length of the first video stream."""
    exe = shutil.which("ffprobe")
    if exe is None:
        raise OSError("ffprobe was not found on PATH; install ffmpeg (https://ffmpeg.org) and try again")
    out = subprocess.run(
        [
            exe, "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,duration:format=duration",
            "-of", "json", str(path),
        ],
        capture_output=True, text=True, check=False,
    )
    if out.returncode != 0:
        raise ValueError(f"{path}: not a video ffprobe can read ({out.stderr.strip()[:200]})")
    doc = json.loads(out.stdout or "{}")
    streams = doc.get("streams") or []
    if not streams:
        raise ValueError(f"{path}: no video stream")
    s = streams[0]
    num, _, den = str(s.get("r_frame_rate", "0/1")).partition("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 0.0
    duration = float(s.get("duration") or (doc.get("format") or {}).get("duration") or 0.0)
    info = VideoInfo(int(s["width"]), int(s["height"]), fps, duration)
    aspect = info.width / max(1, info.height)
    if abs(aspect - 16 / 9) > 0.02:
        raise ValueError(
            f"{path}: {info.width}x{info.height} is not 16:9. The HUD profiles are measured on a 16:9 "
            "screen and would read the wrong places on this one."
        )
    return info


@dataclass
class Layout:
    """Where each region sits in the stacked picture ffmpeg delivers."""

    width: int
    height: int
    #: name -> (x, y, w, h) in the stacked picture
    places: dict[str, tuple[int, int, int, int]]

    def cut(self, frame: np.ndarray) -> dict[str, np.ndarray]:
        return {n: frame[y : y + h, x : x + w] for n, (x, y, w, h) in self.places.items()}


def layout(regions: tuple[Region, ...] | list[Region]) -> Layout:
    """Regions in two columns, tallest first: a picture with little black in it."""
    order = sorted(regions, key=lambda r: -r.size[1])
    columns: list[list[Region]] = [[], []]
    heights = [0, 0]
    widths = [0, 0]
    for r in order:
        c = 0 if heights[0] <= heights[1] else 1
        columns[c].append(r)
        heights[c] += r.size[1]
        widths[c] = max(widths[c], r.size[0])
    places: dict[str, tuple[int, int, int, int]] = {}
    x = 0
    for c in range(2):
        y = 0
        for r in columns[c]:
            w, h = r.size
            places[r.name] = (x, y, w, h)
            y += h
        x += widths[c]
    return Layout(width=x, height=max(heights), places=places)


def filter_graph(info: VideoInfo, regions: list[Region], fps: float, plan: Layout, *, gpu: bool) -> str:
    """The ffmpeg filter that samples, cuts, scales and stacks."""
    head = f"fps={fps:g}"
    if gpu:
        # Frames stay on the card until the sampler has thrown most of them away.
        head += ",hwdownload,format=nv12"
    parts = [f"[0:v]{head},split={len(regions)}" + "".join(f"[s{i}]" for i in range(len(regions)))]
    for i, r in enumerate(regions):
        x, y, w, h = r.box.on(info.width, info.height)
        ow, oh = r.size
        parts.append(f"[s{i}]crop={w}:{h}:{x}:{y},scale={ow}:{oh}:flags=area[r{i}]")
    grid = "|".join(f"{plan.places[r.name][0]}_{plan.places[r.name][1]}" for r in regions)
    if len(regions) == 1:
        parts.append("[r0]null[out]")
    else:
        parts.append("".join(f"[r{i}]" for i in range(len(regions))) + f"xstack=inputs={len(regions)}:layout={grid}:fill=black[out]")
    return ";".join(parts)


@dataclass
class Sample:
    #: Seconds from the start of the recording.
    t: float
    index: int
    #: region name -> BGR crop (a view into one shared buffer; copy to keep)
    regions: dict[str, np.ndarray]


def samples(
    path: Path,
    profile: Profile,
    *,
    fps: float = 5.0,
    start: float = 0.0,
    duration: float | None = None,
    names: list[str] | None = None,
    gpu: bool | None = None,
) -> Iterator[Sample]:
    """
    Every `1/fps` seconds of the recording, the profile's regions as BGR images.

    `gpu=None` tries NVIDIA decoding and falls back to the CPU when the first
    frame does not arrive that way; True or False forces one.
    """
    exe = shutil.which("ffmpeg")
    if exe is None:
        raise OSError("ffmpeg was not found on PATH; install ffmpeg (https://ffmpeg.org) and try again")
    info = probe(path)
    regions = [r for r in profile.regions if names is None or r.name in names]
    plan = layout(regions)
    frame_bytes = plan.width * plan.height * 3
    tries = [True, False] if gpu is None else [gpu]
    for attempt, use_gpu in enumerate(tries):
        cmd = [exe, "-hide_banner", "-loglevel", "error", "-nostdin"]
        if use_gpu:
            cmd += ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"]
        if start > 0:
            cmd += ["-ss", f"{start:.3f}"]
        if duration is not None:
            cmd += ["-t", f"{duration:.3f}"]
        cmd += [
            "-i", str(path), "-an", "-sn",
            "-filter_complex", filter_graph(info, regions, fps, plan, gpu=use_gpu),
            "-map", "[out]", "-f", "rawvideo", "-pix_fmt", "bgr24", "pipe:1",
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=frame_bytes * 2)
        index = 0
        try:
            while True:
                buf = proc.stdout.read(frame_bytes)
                if len(buf) < frame_bytes:
                    break
                frame = np.frombuffer(buf, np.uint8).reshape(plan.height, plan.width, 3)
                yield Sample(t=start + index / fps, index=index, regions=plan.cut(frame))
                index += 1
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait()
            err = proc.stderr.read().decode("utf-8", "replace").strip() if proc.stderr else ""
        if index > 0 or attempt == len(tries) - 1:
            if index == 0:
                raise ValueError(f"{path}: ffmpeg delivered no frames ({err[:300]})")
            return
        # Nothing came out with the GPU: no NVIDIA card or driver. Decode on the CPU instead.
