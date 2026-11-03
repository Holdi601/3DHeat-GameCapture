"""
A small level for the locate tests, made up on the spot: a walled yard with
crates in it, every surface carrying its own procedurally drawn texture, as a
textured .glb in the viewer's frame (Y up, metres).

Drawn, not loaded, so the tests carry no game's data. The textures are
random shapes and text from a fixed seed - enough detail for keypoints, and
different on every wall, so the yard has no symmetry that would make two
places look alike.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path

import numpy as np


def texture(seed: int, size: int = 256) -> np.ndarray:
    import cv2

    rng = np.random.default_rng(seed)
    img = np.full((size, size, 3), rng.integers(60, 200, 3), np.uint8)
    for _ in range(40):
        colour = tuple(int(c) for c in rng.integers(0, 255, 3))
        kind = rng.integers(0, 3)
        x, y = (int(v) for v in rng.integers(0, size, 2))
        if kind == 0:
            cv2.circle(img, (x, y), int(rng.integers(4, 30)), colour, -1)
        elif kind == 1:
            cv2.rectangle(img, (x, y), (x + int(rng.integers(5, 50)), y + int(rng.integers(5, 50))), colour, -1)
        else:
            cv2.putText(img, chr(65 + int(rng.integers(0, 26))) * 2, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, colour, 2)
    return img


def _quad(a, b, c, d, repeat=(1.0, 1.0), toward=None, away=None):
    """
    Two triangles a-b-c, a-c-d with texture coordinates, wound so the front
    faces `toward` a point (or `away` from one).
    """
    p = np.array([a, b, c, d], np.float32)
    uv = np.array([[0, repeat[1]], [repeat[0], repeat[1]], [repeat[0], 0], [0, 0]], np.float32)
    tris = np.array([0, 1, 2, 0, 2, 3], np.uint32)
    normal = np.cross(p[1] - p[0], p[2] - p[0])
    centre = p.mean(axis=0)
    if toward is not None and normal @ (np.asarray(toward) - centre) < 0:
        tris = tris.reshape(-1, 3)[:, ::-1].ravel().copy()
    if away is not None and normal @ (centre - np.asarray(away)) < 0:
        tris = tris.reshape(-1, 3)[:, ::-1].ravel().copy()
    return p, uv, tris


def _box(lo, hi):
    """The four sides and the top of a box, facing out."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    mid = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    return [
        _quad((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), away=mid),
        _quad((x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0), away=mid),
        _quad((x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1), away=mid),
        _quad((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0), away=mid),
        _quad((x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0), away=mid),
    ]


def yard() -> list[tuple[str, list, int]]:
    """Parts as (name, quads, texture seed)."""
    s, h = 20.0, 6.0
    inside = (0.0, 1.0, 0.0)
    parts = [
        ("ground:floor", [_quad((-s, 0, s), (s, 0, s), (s, 0, -s), (-s, 0, -s), (8, 8), toward=(0, 5, 0))], 1),
        # The walls face inwards.
        ("structure:north", [_quad((s, 0, -s), (-s, 0, -s), (-s, h, -s), (s, h, -s), (6, 1), toward=inside)], 2),
        ("structure:south", [_quad((-s, 0, s), (s, 0, s), (s, h, s), (-s, h, s), (6, 1), toward=inside)], 3),
        ("structure:east", [_quad((s, 0, s), (s, 0, -s), (s, h, -s), (s, h, s), (6, 1), toward=inside)], 4),
        ("structure:west", [_quad((-s, 0, -s), (-s, 0, s), (-s, h, s), (-s, h, -s), (6, 1), toward=inside)], 5),
    ]
    rng = np.random.default_rng(9)
    for k in range(10):
        x, z = rng.uniform(-15, 15, 2)
        w, d, hh = rng.uniform(1.0, 3.0), rng.uniform(1.0, 3.0), rng.uniform(1.0, 3.5)
        parts.append((f"structure:crate{k}", _box((x - w / 2, 0, z - d / 2), (x + w / 2, hh, z + d / 2)), 10 + k))
    return parts


def fence_texture(size: int = 64) -> np.ndarray:
    """A bright red fence with square holes: alpha 0 in the holes (BGRA, as OpenCV writes it)."""
    img = np.zeros((size, size, 4), np.uint8)
    img[:, :] = (30, 30, 230, 255)
    step = size // 4
    for y in range(0, size, step):
        for x in range(0, size, step):
            img[y + 2 : y + step - 2, x + 2 : x + step - 2, 3] = 0
    return img


def write_yard(path: Path, *, extras: bool = False) -> Path:
    """
    The yard as a textured .glb (one unit = 1 m). With `extras`: a cut-out
    fence (alphaMode MASK) across the south of the yard, and a navigation
    mesh (`nav:walkable`) over the floor except a square round the middle.
    """
    import cv2

    blob = bytearray()
    views, accessors, meshes, nodes, materials, images = [], [], [], [], [], []

    def add(data: bytes, target: int | None = None) -> int:
        while len(blob) % 4:
            blob.append(0)
        view = {"buffer": 0, "byteOffset": len(blob), "byteLength": len(data)}
        if target:
            view["target"] = target
        views.append(view)
        blob.extend(data)
        return len(views) - 1

    def accessor(array: np.ndarray, kind: str, component: int, target: int) -> int:
        acc = {"bufferView": add(array.tobytes(), target), "componentType": component, "count": len(array), "type": kind}
        if kind == "VEC3":
            acc["min"] = array.min(axis=0).tolist()
            acc["max"] = array.max(axis=0).tolist()
        accessors.append(acc)
        return len(accessors) - 1

    parts = [(name, quads, seed, None) for name, quads, seed in yard()]
    if extras:
        parts.append(("structure:fence", [_quad((-8, 0, 12), (8, 0, 12), (8, 4, 12), (-8, 4, 12), (8, 2), toward=(0, 1, 0))], -1, "MASK"))
        nav = [_quad((x0, 0.05, z1), (x1, 0.05, z1), (x1, 0.05, z0), (x0, 0.05, z0), toward=(0, 5, 0))
               for x0, x1, z0, z1 in ((-18, 18, -18, -4), (-18, 18, 4, 18), (-18, -4, -4, 4), (4, 18, -4, 4))]
        parts.append(("nav:walkable", nav, 1, None))
    for name, quads, seed, alpha in parts:
        ok, png = cv2.imencode(".png", fence_texture() if alpha else texture(seed))
        images.append({"bufferView": add(png.tobytes()), "mimeType": "image/png"})
        material = {"name": name, "pbrMetallicRoughness": {"baseColorTexture": {"index": len(images) - 1}}}
        if alpha:
            material.update({"alphaMode": alpha, "alphaCutoff": 0.5, "doubleSided": True})
        materials.append(material)
        p = np.concatenate([q[0] for q in quads])
        uv = np.concatenate([q[1] for q in quads])
        idx = np.concatenate([q[2] + 4 * k for k, q in enumerate(quads)]).astype(np.uint32)
        prim = {
            "attributes": {"POSITION": accessor(p, "VEC3", 5126, 34962), "TEXCOORD_0": accessor(uv, "VEC2", 5126, 34962)},
            "indices": accessor(idx, "SCALAR", 5125, 34963),
            "material": len(materials) - 1,
        }
        meshes.append({"name": name, "primitives": [prim]})
        nodes.append({"name": name, "mesh": len(meshes) - 1})
    doc = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": meshes,
        "materials": materials,
        "images": images,
        "textures": [{"source": i, "sampler": 0} for i in range(len(images))],
        "samplers": [{"magFilter": 9729, "minFilter": 9987}],
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{"byteLength": len(blob)}],
    }
    text = json.dumps(doc).encode()
    text += b" " * (-len(text) % 4)
    while len(blob) % 4:
        blob.append(0)
    data = struct.pack("<III", 0x46546C67, 2, 28 + len(text) + len(blob))
    data += struct.pack("<II", len(text), 0x4E4F534A) + text + struct.pack("<II", len(blob), 0x004E4942) + bytes(blob)
    path.write_bytes(data)
    return path
