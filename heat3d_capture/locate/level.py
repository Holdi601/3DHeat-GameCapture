"""
A level's geometry and its look, read from glTF, for rendering.

The level is whatever the 3DHeat tools wrote for it: a `.glb` (or a `.gltf`
with its files beside it) in the viewer's frame, **Y up**, with parts named
`ground:<what>` and `structure:<what>`. Only what a renderer needs is kept:
positions, normals, texture coordinates, triangles, and per material the
base colour (a texture, a factor, or both) and how it handles alpha. Normal
maps, roughness and the like are left: the game's own lighting is not
reproduced anyway (see `render.py`), and they would add nothing a feature
matcher can use.

The level's frame is the frame every position this package writes is in. Its
unit is whatever the file uses; `unit_metres` says how many metres one is
(read from the file's `extras.unit_metres` when it has one, otherwise 1, the
glTF convention).

Like geometry/glb.py, this is read by hand: the subset is small, and a glTF
library would carry its version skew for the few functions below.
"""

from __future__ import annotations

import base64
import json
import struct
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

_COMPONENT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
_WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
_NORMALIZED_MAX = {5121: 255.0, 5123: 65535.0, 5120: 127.0, 5122: 32767.0}

#: A face whose normal is at least this far up is ground a player can stand on
#: (about 45 degrees, the slope most games let a player walk).
GROUND = 0.7
#: Parts that describe the level rather than show it - the navigation mesh
#: (`nav:walkable`): where players can walk. Never drawn.
HELPER = "nav:"


@dataclass
class Material:
    name: str
    #: RGBA, 0..1, multiplied with the texture.
    factor: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    #: The base colour texture as RGBA uint8 (top row first), or None.
    image: np.ndarray | None = None
    #: OPAQUE, MASK (cut out below `cutoff`) or BLEND (drawn over, after the rest).
    alpha: str = "OPAQUE"
    cutoff: float = 0.5
    #: A decal lying on another surface: drawn after it, pulled towards the camera.
    decal: bool = False


@dataclass
class Batch:
    """Triangles of one material, in the level's frame."""

    name: str
    positions: np.ndarray  # (n, 3) float32
    normals: np.ndarray  # (n, 3) float32
    uv: np.ndarray  # (n, 2) float32
    indices: np.ndarray  # (m*3,) uint32
    material: int
    #: The game can destroy this part (a wall, a house, a rock): matches on it are trusted less.
    destructible: bool = False


@dataclass
class Level:
    path: Path
    batches: list[Batch]
    materials: list[Material]
    unit_metres: float = 1.0
    extras: dict = field(default_factory=dict)

    def floors_at(self, x: float, z: float, parts: str = HELPER) -> list[float]:
        """
        The heights of the walkable floors straight above or below (x, z): the
        navigation mesh's triangles (`nav:`) that cover the point, one height
        each, lowest first. Empty where it covers nothing.
        """
        if getattr(self, "_floor_tris", None) is None:
            a, b, c = self.ground(parts=parts)
            self._floor_tris = (a, b, c)
        a, b, c = self._floor_tris
        if not len(a):
            return []
        # Barycentric coordinates in the x-z plane.
        v0, v1 = b[:, [0, 2]] - a[:, [0, 2]], c[:, [0, 2]] - a[:, [0, 2]]
        v2 = np.array([x, z]) - a[:, [0, 2]]
        den = v0[:, 0] * v1[:, 1] - v1[:, 0] * v0[:, 1]
        ok = np.abs(den) > 1e-12
        den = np.where(ok, den, 1.0)
        u = (v2[:, 0] * v1[:, 1] - v1[:, 0] * v2[:, 1]) / den
        v = (v0[:, 0] * v2[:, 1] - v2[:, 0] * v0[:, 1]) / den
        inside = ok & (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6)
        ys = a[inside, 1] + u[inside] * (b[inside, 1] - a[inside, 1]) + v[inside] * (c[inside, 1] - a[inside, 1])
        out: list[float] = []
        for y in sorted(ys):
            if not out or y - out[-1] > 1.0 / self.unit_metres:
                out.append(float(y))
        return out

    def has(self, prefix: str) -> bool:
        """Whether any part's name starts with `prefix` (`nav:` - the level carries its navigation mesh)."""
        return any(b.name.startswith(prefix) for b in self.batches)

    @property
    def triangles(self) -> int:
        return sum(len(b.indices) // 3 for b in self.batches)

    @property
    def bounds(self) -> tuple[np.ndarray, np.ndarray]:
        lo = np.min([b.positions.min(axis=0) for b in self.batches if len(b.positions)], axis=0)
        hi = np.max([b.positions.max(axis=0) for b in self.batches if len(b.positions)], axis=0)
        return lo, hi

    def ground(self, parts: str | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Every upward-facing triangle: corners a, b, c, each (n, 3).

        Taken from the geometry, not from the part names: a `structure:` part
        has floors too (the top of a crate, a balcony), and a player stands on
        those just as well. `parts` keeps only parts whose name starts with
        it (`ground:`: the terrain and roads, not the roofs and crates few
        players stand on).
        """
        out = []
        for b in self.batches:
            if self.materials[b.material].decal or self.materials[b.material].alpha == "BLEND":
                continue
            if parts and not b.name.startswith(parts):
                continue
            if not parts and b.name.startswith(HELPER):
                continue
            t = b.indices.reshape(-1, 3)
            p = b.positions.astype(np.float64)
            a, bb, c = p[t[:, 0]], p[t[:, 1]], p[t[:, 2]]
            n = np.cross(bb - a, c - a)
            length = np.linalg.norm(n, axis=1)
            up = np.divide(n[:, 1], length, out=np.zeros(len(length)), where=length > 0)
            keep = up >= GROUND
            out.append((a[keep], bb[keep], c[keep]))
        if not out:
            z = np.zeros((0, 3))
            return z, z, z
        return tuple(np.concatenate([o[k] for o in out]) for k in range(3))  # type: ignore[return-value]


def _chunks(path: Path) -> tuple[dict, bytes]:
    data = path.read_bytes()
    if path.suffix.lower() == ".glb" or data[:4] == b"glTF":
        magic, _, length = struct.unpack_from("<III", data, 0)
        if magic != 0x46546C67:
            raise ValueError(f"{path} is not a .glb")
        doc, blob, at = None, b"", 12
        while at < length:
            size, kind = struct.unpack_from("<II", data, at)
            chunk = data[at + 8 : at + 8 + size]
            if kind == 0x4E4F534A:
                doc = json.loads(chunk)
            elif kind == 0x004E4942:
                blob = chunk
            at += 8 + size
        if doc is None:
            raise ValueError(f"{path} has no JSON chunk")
        return doc, blob
    return json.loads(data.decode("utf-8")), b""


def _uri(path: Path, uri: str) -> bytes:
    if uri.startswith("data:"):
        return base64.b64decode(uri.split(",", 1)[1])
    return (path.parent / uri).read_bytes()


def _buffers(path: Path, doc: dict, blob: bytes) -> list[bytes]:
    out = []
    for i, b in enumerate(doc.get("buffers", [])):
        out.append(_uri(path, b["uri"]) if "uri" in b else blob if i == 0 else b"")
    return out


def _accessor(doc: dict, buffers: list[bytes], index: int) -> np.ndarray:
    a = doc["accessors"][index]
    kind = np.dtype(_COMPONENT[a["componentType"]])
    width = _WIDTH[a["type"]]
    count = a["count"]
    if "bufferView" not in a:
        return np.zeros((count, width), kind)
    view = doc["bufferViews"][a["bufferView"]]
    blob = buffers[view.get("buffer", 0)]
    start = view.get("byteOffset", 0) + a.get("byteOffset", 0)
    item = kind.itemsize * width
    stride = view.get("byteStride", 0) or item
    if stride == item:
        out = np.frombuffer(blob, kind, count=count * width, offset=start).reshape(count, width)
    else:
        raw = np.frombuffer(blob, np.uint8, count=stride * (count - 1) + item, offset=start)
        out = raw[np.arange(count)[:, None] * stride + np.arange(item)[None, :]].copy().view(kind).reshape(count, width)
    if a.get("normalized") and a["componentType"] in _NORMALIZED_MAX:
        out = out.astype(np.float32) / _NORMALIZED_MAX[a["componentType"]]
    return out


def _local(node: dict) -> np.ndarray:
    if "matrix" in node:
        return np.array(node["matrix"], dtype=float).reshape(4, 4).T
    x, y, z, w = node.get("rotation", [0.0, 0.0, 0.0, 1.0])
    rotation = np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )
    m = np.eye(4)
    m[:3, :3] = rotation * np.array(node.get("scale", [1.0, 1.0, 1.0]))
    m[:3, 3] = node.get("translation", [0.0, 0.0, 0.0])
    return m


def _image(path: Path, doc: dict, buffers: list[bytes], index: int) -> np.ndarray | None:
    import cv2

    img = doc["images"][index]
    if "bufferView" in img:
        view = doc["bufferViews"][img["bufferView"]]
        start = view.get("byteOffset", 0)
        data = buffers[view.get("buffer", 0)][start : start + view["byteLength"]]
    elif "uri" in img:
        try:
            data = _uri(path, img["uri"])
        except OSError:
            return None
    else:
        return None
    pic = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_UNCHANGED)
    if pic is None:
        return None
    if pic.ndim == 2:
        pic = cv2.cvtColor(pic, cv2.COLOR_GRAY2RGBA)
    elif pic.shape[2] == 3:
        pic = cv2.cvtColor(pic, cv2.COLOR_BGR2RGBA)
    else:
        pic = cv2.cvtColor(pic, cv2.COLOR_BGRA2RGBA)
    if pic.dtype != np.uint8:
        pic = (pic / (256 if pic.dtype == np.uint16 else 1)).astype(np.uint8)
    return np.ascontiguousarray(pic)


def _materials(path: Path, doc: dict, buffers: list[bytes]) -> list[Material]:
    images: dict[int, np.ndarray | None] = {}
    out = []
    for i, m in enumerate(doc.get("materials", [])):
        pbr = m.get("pbrMetallicRoughness", {})
        image = None
        if "baseColorTexture" in pbr:
            source = doc["textures"][pbr["baseColorTexture"]["index"]].get("source")
            if source is not None:
                if source not in images:
                    images[source] = _image(path, doc, buffers, source)
                image = images[source]
        out.append(
            Material(
                name=m.get("name", f"material{i}"),
                factor=tuple(pbr.get("baseColorFactor", [1.0, 1.0, 1.0, 1.0])),  # type: ignore[arg-type]
                image=image,
                alpha=m.get("alphaMode", "OPAQUE"),
                cutoff=float(m.get("alphaCutoff", 0.5)),
                decal=bool(m.get("extras", {}).get("decal", False)),
            )
        )
    # Primitives without a material are drawn in glTF's default: white, opaque.
    out.append(Material(name="default"))
    return out


def load(path: str | Path) -> Level:
    """Read a .glb or .gltf: every triangle primitive, placed by the scene's node transforms."""
    path = Path(path)
    doc, blob = _chunks(path)
    buffers = _buffers(path, doc, blob)
    materials = _materials(path, doc, buffers)
    default = len(materials) - 1
    batches: list[Batch] = []

    def walk(index: int, parent: np.ndarray) -> None:
        node = doc["nodes"][index]
        world = parent @ _local(node)
        if "mesh" in node:
            linear = world[:3, :3]
            normal_m = np.linalg.inv(linear).T
            flip = np.linalg.det(linear) < 0
            for prim in doc["meshes"][node["mesh"]]["primitives"]:
                if prim.get("mode", 4) != 4:
                    continue
                at = prim["attributes"]
                p = _accessor(doc, buffers, at["POSITION"]).astype(np.float64)
                p = p @ linear.T + world[:3, 3]
                tris = (
                    _accessor(doc, buffers, prim["indices"]).reshape(-1, 3).astype(np.uint32)
                    if "indices" in prim
                    else np.arange(len(p), dtype=np.uint32).reshape(-1, 3)
                )
                if flip:
                    tris = tris[:, ::-1]
                if "NORMAL" in at:
                    n = _accessor(doc, buffers, at["NORMAL"]).astype(np.float64) @ normal_m.T
                else:
                    n = _vertex_normals(p, tris)
                n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
                uv = (
                    _accessor(doc, buffers, at["TEXCOORD_0"]).astype(np.float32)
                    if "TEXCOORD_0" in at
                    else np.zeros((len(p), 2), np.float32)
                )
                name = node.get("name", doc["meshes"][node["mesh"]].get("name", ""))
                batches.append(
                    Batch(
                        name=name,
                        destructible=_destructible(name, node, doc["meshes"][node["mesh"]], prim),
                        positions=p.astype(np.float32),
                        normals=n.astype(np.float32),
                        uv=np.ascontiguousarray(uv[:, :2]),
                        indices=np.ascontiguousarray(tris.ravel()),
                        material=prim.get("material", default),
                    )
                )
        for child in node.get("children", []):
            walk(child, world)

    scenes = doc.get("scenes") or [{"nodes": list(range(len(doc.get("nodes", []))))}]
    for root in scenes[doc.get("scene", 0)].get("nodes", []):
        walk(root, np.eye(4))
    if not batches:
        raise ValueError(f"{path} has no triangles")
    extras = doc.get("extras", {}) if isinstance(doc.get("extras"), dict) else {}
    return Level(path, batches, materials, float(extras.get("unit_metres", 1.0)), extras)


#: Part names that mark what the game can destroy, for exports that tag it in the name (or end it
#: with "(destructible)").
DESTRUCTIBLE = ("destructible:", "destructible ")


def _destructible(name: str, node: dict, mesh: dict, prim: dict) -> bool:
    """A part the game can destroy: tagged in its name, or `extras.destructible` on its node, mesh or primitive."""
    low = name.lower().strip()
    if low.startswith(DESTRUCTIBLE) or low.endswith("(destructible)"):
        return True
    for d in (node, mesh, prim):
        extras = d.get("extras")
        if isinstance(extras, dict) and extras.get("destructible"):
            return True
    return False


def _vertex_normals(p: np.ndarray, tris: np.ndarray) -> np.ndarray:
    a, b, c = p[tris[:, 0]], p[tris[:, 1]], p[tris[:, 2]]
    face = np.cross(b - a, c - a)
    n = np.zeros_like(p)
    for k in range(3):
        np.add.at(n, tris[:, k], face)
    return n
