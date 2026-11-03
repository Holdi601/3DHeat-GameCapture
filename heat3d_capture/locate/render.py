"""
Pictures of the level from any pose, offscreen, with the depth of every pixel.

OpenGL through moderngl (MIT), in a standalone context: no window, no
display, and it runs on whatever OpenGL 3.3 driver the machine has, which on
Windows is every current NVIDIA, AMD and Intel GPU.

Each render gives two things, from the same pass:

- **colour**: the level's base colour textures, lit by a sun and a sky
  (`Light`), optionally with the sun's shadows. The game's own lighting -
  baked light maps, bounce, fog, post effects - is not reproduced. What the
  matcher needs is the texture's detail and the edges of the structure, and
  those are there; the difference in light is what the localization has to
  be robust to (see docs/locate.md, "Renders against frames").
- **depth**: the distance along the view axis to the surface at every pixel,
  in level units, 0 where nothing was hit. With the pose it turns a pixel of
  a render into a 3D point of the level, which is what makes a 2D-2D match
  between a frame and a render a 2D-3D one.

Cut-out materials (glTF `alphaMode` MASK: foliage cards, fences) are cut
out: a fragment whose alpha (texture times factor) is below the material's
`alphaCutoff` (0.5 when the file names none) is discarded, so neither its
colour nor its depth is written and what is behind it shows. Blended ones and
decals are drawn after the rest, over it, and leave the depth alone. Parts
named `nav:` (the navigation mesh) are not drawn at all.

**Speed.** A game level is millions of triangles and the database is tens of
thousands of renders, so the layout is chosen for it. Every texture goes into
one texture array (resized to a common size), every triangle of a pass into
one vertex buffer carrying its material with it, so a pass is a single draw
call rather than one per material. The triangles are sorted into square tiles
across the level, and only the tiles inside the view are drawn (one
multi-draw call where the driver has OpenGL 4.3, a call per run of visible
tiles where it has not).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .camera import Pose, gl_projection, gl_view
from .level import Level

_VERTEX = """
#version 330
uniform mat4 mvp;
uniform mat4 view;
uniform mat4 sun_mvp;
in vec3 in_pos;
in vec3 in_normal;
in vec2 in_uv;
in vec4 in_factor;
in vec3 in_material;
out vec3 v_normal;
out vec2 v_uv;
out float v_depth;
out vec4 v_sun;
flat out vec4 v_factor;
flat out vec3 v_material;
void main() {
    v_depth = -(view * vec4(in_pos, 1.0)).z;
    v_normal = in_normal;
    v_uv = in_uv;
    v_sun = sun_mvp * vec4(in_pos, 1.0);
    v_factor = in_factor;
    v_material = in_material;
    gl_Position = mvp * vec4(in_pos, 1.0);
}
"""

_FRAGMENT = """
#version 330
uniform sampler2DArray tex;
uniform bool textured;
uniform vec3 sun;
uniform float ambient;
uniform float diffuse;
uniform float sky;
uniform bool shadows;
uniform sampler2DShadow shadow_map;
uniform float shadow_texel;
in vec3 v_normal;
in vec2 v_uv;
in float v_depth;
in vec4 v_sun;
flat in vec4 v_factor;
flat in vec3 v_material;
layout(location = 0) out vec4 color;
layout(location = 1) out vec2 aux;
void main() {
    // v_material: texture layer (-1 for none), alpha cut-off (-1 for none).
    vec4 c = v_factor;
    if (v_material.x >= 0.0) c *= texture(tex, vec3(v_uv, v_material.x));
    if (v_material.y >= 0.0 && c.a < v_material.y) discard;
    if (!textured) c = vec4(0.6, 0.6, 0.6, c.a);
    vec3 n = normalize(v_normal);
    if (!gl_FrontFacing) n = -n;
    float lit = max(dot(n, sun), 0.0);
    if (shadows && lit > 0.0) {
        vec3 s = v_sun.xyz / v_sun.w * 0.5 + 0.5;
        float bias = shadow_texel * (1.5 + 2.0 * (1.0 - lit));
        float seen = 0.0;
        for (int dx = -1; dx <= 1; dx++)
            for (int dy = -1; dy <= 1; dy++)
                seen += texture(shadow_map, vec3(s.xy + vec2(dx, dy) * shadow_texel, s.z - bias));
        lit *= seen / 9.0;
    }
    float light = ambient + diffuse * lit + sky * (0.5 + 0.5 * n.y);
    color = vec4(c.rgb * light, c.a);
    // aux.y: 1 seen from the front, plus 2 on a part the game can destroy.
    aux = vec2(v_depth, (gl_FrontFacing ? 1.0 : 0.0) + 2.0 * v_material.z);
}
"""

_SHADOW_VERTEX = """
#version 330
uniform mat4 mvp;
in vec3 in_pos;
void main() {
    gl_Position = mvp * vec4(in_pos, 1.0);
}
"""

_SHADOW_FRAGMENT = """
#version 330
void main() {}
"""

#: Floats per vertex: position 3, normal 3, uv 2, factor 4, material 3 (layer, cut-off, destructible).
_STRIDE = 15


@dataclass
class Light:
    """
    How a render is lit: a sun (direction towards it, level frame), a sky from
    above, a flat ambient. `textured=False` draws every surface the same grey,
    so only the shape and the light are left - the look of a level whose
    textures were not exported.
    """

    sun: tuple[float, float, float] = (0.35, 0.85, 0.4)
    ambient: float = 0.35
    diffuse: float = 0.55
    sky: float = 0.25
    textured: bool = True
    #: Cast the sun's shadows (a shadow map over the whole level).
    shadows: bool = False

    @classmethod
    def flat(cls) -> "Light":
        """Base colour only, no shading."""
        return cls(ambient=1.0, diffuse=0.0, sky=0.0)


@dataclass
class Render:
    pose: Pose
    hfov: float
    #: (h, w, 3) uint8 RGB.
    color: np.ndarray
    #: (h, w) float32, distance along the view axis; 0 where nothing was hit.
    depth: np.ndarray
    #: (h, w) bool: the surface was seen from its front. Mostly back faces is a camera inside geometry.
    front: np.ndarray
    #: (h, w) bool: the surface is on a part the game can destroy (level.Batch.destructible).
    destructible: np.ndarray | None = None


class _Pass:
    """One vertex buffer of triangles sorted by tile, and where each tile's run of indices lies."""

    def __init__(self, ctx, prog, shadow_prog, vertices: np.ndarray, triangles: np.ndarray, tile_size: float, origin: np.ndarray):
        corners = vertices[:, :3][triangles]  # (n, 3, 3)
        centre = corners.mean(axis=1)
        cell = np.floor((centre[:, [0, 2]] - origin) / tile_size).astype(np.int64)
        key = cell[:, 0] * 100_003 + cell[:, 1]
        order = np.argsort(key, kind="stable")
        triangles, key, corners = triangles[order], key[order], corners[order]
        starts = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
        ends = np.r_[starts[1:], len(key)]
        self.first = (starts * 3).astype(np.int64)
        self.count = ((ends - starts) * 3).astype(np.int64)
        flat = corners.reshape(-1, 9)
        lo = np.minimum.reduceat(np.minimum(np.minimum(flat[:, 0:3], flat[:, 3:6]), flat[:, 6:9]), starts, axis=0)
        hi = np.maximum.reduceat(np.maximum(np.maximum(flat[:, 0:3], flat[:, 3:6]), flat[:, 6:9]), starts, axis=0)
        self.lo, self.hi = lo, hi
        vbo = ctx.buffer(vertices.astype("f4").tobytes())
        ibo = ctx.buffer(triangles.astype("u4").tobytes())
        self.vao = ctx.vertex_array(
            prog, [(vbo, "3f 3f 2f 4f 3f", "in_pos", "in_normal", "in_uv", "in_factor", "in_material")], ibo
        )
        self.shadow_vao = ctx.vertex_array(shadow_prog, [(vbo, "3f 48x", "in_pos")], ibo)
        self.total = len(triangles) * 3
        self.indirect = ctx.buffer(reserve=max(1, len(starts)) * 20)

    def visible(self, planes: np.ndarray) -> list[tuple[int, int]]:
        """Runs (first index, index count) of the tiles inside the view frustum, adjacent ones joined."""
        # A box is outside when it lies wholly behind one plane: test its most positive corner.
        n = planes[:, :3]
        corner_x = np.where(n[None, :, 0] > 0, self.hi[:, None, 0], self.lo[:, None, 0])
        corner_y = np.where(n[None, :, 1] > 0, self.hi[:, None, 1], self.lo[:, None, 1])
        corner_z = np.where(n[None, :, 2] > 0, self.hi[:, None, 2], self.lo[:, None, 2])
        d = corner_x * n[None, :, 0] + corner_y * n[None, :, 1] + corner_z * n[None, :, 2] + planes[None, :, 3]
        inside = (d >= 0).all(axis=1)
        runs: list[tuple[int, int]] = []
        for k in np.flatnonzero(inside):
            f, c = int(self.first[k]), int(self.count[k])
            if runs and runs[-1][0] + runs[-1][1] == f:
                runs[-1] = (runs[-1][0], runs[-1][1] + c)
            else:
                runs.append((f, c))
        return runs

    def draw(self, runs: list[tuple[int, int]], multi: bool) -> None:
        if not runs:
            return
        if multi and len(runs) > 1:
            cmd = np.zeros((len(runs), 5), np.uint32)
            cmd[:, 0] = [c for _, c in runs]
            cmd[:, 1] = 1
            cmd[:, 2] = [f for f, _ in runs]
            self.indirect.write(cmd.tobytes())
            self.vao.render_indirect(self.indirect, count=len(runs))
            return
        for f, c in runs:
            self.vao.render(vertices=c, first=f)


class Renderer:
    """
    Renders one level. Not thread safe: OpenGL contexts belong to the thread
    that made them, so make and use it on one thread.
    """

    def __init__(
        self,
        level: Level,
        width: int,
        height: int,
        *,
        near: float | None = None,
        far: float | None = None,
        texture_size: int = 512,
        tiles: int = 24,
    ):
        import moderngl

        self.level = level
        try:
            # 4.3 for the multi-draw; anything from 3.3 renders, a call per run of tiles.
            self.ctx = moderngl.create_standalone_context(require=430)
        except Exception:
            self.ctx = moderngl.create_standalone_context(require=330)
        self.multi = self.ctx.version_code >= 430
        self.prog = self.ctx.program(vertex_shader=_VERTEX, fragment_shader=_FRAGMENT)
        self.shadow_prog = self.ctx.program(vertex_shader=_SHADOW_VERTEX, fragment_shader=_SHADOW_FRAGMENT)
        lo, hi = level.bounds
        self._bounds = (lo, hi)
        diagonal = float(np.linalg.norm(hi - lo))
        # 5 cm, and the whole level up to 5 km (beyond that a picture holds
        # nothing to match, and the depth buffer would lose its precision).
        self.near = near if near is not None else 0.05 / level.unit_metres
        self.far = far if far is not None else min(max(diagonal * 1.5, self.near * 1000), 5000.0 / level.unit_metres)

        # Every texture as one layer of an array, all at one size.
        import cv2

        layers: dict[int, int] = {}
        pictures = []
        for i, m in enumerate(level.materials):
            if m.image is not None:
                layers[i] = len(pictures)
                pictures.append(cv2.resize(m.image, (texture_size, texture_size), interpolation=cv2.INTER_AREA))
        if not pictures:
            pictures.append(np.full((4, 4, 4), 255, np.uint8))
            texture_size = 4
        self._array = self.ctx.texture_array((texture_size, texture_size, len(pictures)), 4, np.stack(pictures).tobytes())
        self._array.build_mipmaps()
        self._array.repeat_x = self._array.repeat_y = True
        self._array.anisotropy = 8.0

        # Vertices carry their material; one buffer for what is drawn first, one for what is blended over it.
        from .level import HELPER

        solid, late = [], []
        for b in level.batches:
            if not len(b.indices) or b.name.startswith(HELPER):
                # Empty, or the navigation mesh: it describes the level, it is not seen.
                continue
            m = level.materials[b.material]
            n = len(b.positions)
            v = np.empty((n, _STRIDE), np.float32)
            v[:, 0:3] = b.positions
            v[:, 3:6] = b.normals
            v[:, 6:8] = b.uv
            v[:, 8:12] = m.factor
            v[:, 12] = layers.get(b.material, -1)
            blended = m.alpha == "BLEND" or m.decal
            v[:, 13] = m.cutoff if m.alpha == "MASK" else (0.02 if m.decal and m.alpha != "BLEND" else -1.0)
            v[:, 14] = 1.0 if b.destructible else 0.0
            (late if blended else solid).append((v, b.indices.reshape(-1, 3).astype(np.int64)))
        tile = max(float(np.max((hi - lo)[[0, 2]])) / tiles, 1e-6)
        origin = lo[[0, 2]].astype(np.float64)
        self._passes = []
        for group in (solid, late):
            if not group:
                self._passes.append(None)
                continue
            offset, vs, ts = 0, [], []
            for v, t in group:
                vs.append(v)
                ts.append(t + offset)
                offset += len(v)
            self._passes.append(_Pass(self.ctx, self.prog, self.shadow_prog, np.concatenate(vs), np.concatenate(ts), tile, origin))

        self._shadow_key: tuple | None = None
        self._shadow_map = None
        self._sun_mvp = np.eye(4)
        self._size = (0, 0)
        self.resize(width, height)

    def resize(self, width: int, height: int) -> None:
        if (width, height) == self._size:
            return
        with self.ctx:
            self._resize(width, height)

    def _resize(self, width: int, height: int) -> None:
        for name in ("fbo", "fbo_color", "_color", "_aux", "_depth"):
            old = getattr(self, name, None)
            if old is not None:
                old.release()
        self._color = self.ctx.texture((width, height), 4)
        self._aux = self.ctx.texture((width, height), 2, dtype="f4")
        self._depth = self.ctx.depth_renderbuffer((width, height))
        self.fbo = self.ctx.framebuffer(color_attachments=[self._color, self._aux], depth_attachment=self._depth)
        self.fbo_color = self.ctx.framebuffer(color_attachments=[self._color], depth_attachment=self._depth)
        self._size = (width, height)

    @property
    def size(self) -> tuple[int, int]:
        return self._size

    def render(self, pose: Pose, hfov: float, light: Light | None = None, *, want_color: bool = True) -> Render:
        # Another renderer's context may be the current one on this thread.
        with self.ctx:
            return self._render(pose, hfov, light, want_color)

    def _render(self, pose: Pose, hfov: float, light: Light | None, want_color: bool) -> Render:
        import moderngl

        light = light or Light()
        w, h = self._size
        view = gl_view(pose)
        mvp = gl_projection(w, h, hfov, self.near, self.far) @ view
        prog = self.prog
        prog["mvp"].write(mvp.T.astype("f4").tobytes())
        prog["view"].write(view.T.astype("f4").tobytes())
        sun = np.asarray(light.sun, float)
        prog["sun"].value = tuple((sun / np.linalg.norm(sun)).tolist())
        prog["ambient"].value = light.ambient
        prog["diffuse"].value = light.diffuse
        prog["sky"].value = light.sky
        prog["textured"].value = light.textured
        prog["shadows"].value = light.shadows
        prog["tex"].value = 0
        prog["shadow_map"].value = 1
        if light.shadows:
            self._shadows_for(tuple(float(v) for v in light.sun))
            self._shadow_map.use(1)
            prog["sun_mvp"].write(self._sun_mvp.T.astype("f4").tobytes())
            prog["shadow_texel"].value = 1.0 / self._shadow_map.size[0]
        self._array.use(0)
        planes = _frustum(mvp)

        ctx = self.ctx
        self.fbo.use()
        ctx.viewport = (0, 0, w, h)
        self.fbo.clear(0.62, 0.70, 0.80, 1.0, depth=1.0)
        # The colour clear above wrote the sky into the aux target too; depth 0 is "nothing".
        self._aux.write(np.zeros((h, w, 2), "f4").tobytes())
        ctx.enable(moderngl.DEPTH_TEST)
        ctx.disable(moderngl.CULL_FACE | moderngl.BLEND)
        ctx.depth_func = "<"
        solid, late = self._passes
        if solid is not None:
            solid.draw(solid.visible(planes), self.multi)
        if late is not None and want_color:
            self.fbo_color.use()
            ctx.enable(moderngl.BLEND)
            ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
            ctx.depth_mask = False
            ctx.depth_func = "<="
            ctx.polygon_offset = (-1.0, -4.0)
            late.draw(late.visible(planes), self.multi)
            ctx.polygon_offset = (0.0, 0.0)
            ctx.depth_mask = True
            ctx.disable(moderngl.BLEND)
        color = (
            np.frombuffer(self._color.read(), np.uint8).reshape(h, w, 4)[::-1, :, :3].copy()
            if want_color
            else np.zeros((h, w, 3), np.uint8)
        )
        aux = np.frombuffer(self._aux.read(), np.float32).reshape(h, w, 2)[::-1]
        flags = np.rint(aux[:, :, 1]).astype(np.int8)
        return Render(pose, hfov, color, aux[:, :, 0].copy(), (flags & 1) > 0, (flags & 2) > 0)

    def below(self, position: np.ndarray, size: int = 24) -> tuple[float, float, float]:
        """
        What is under `position`, in a 40-degree cone straight down: the
        nearest of it (the 10th percentile distance - a ledge the player stands
        at the edge of), the typical (the median), both in level units and inf
        where nothing is, and the fraction of it seen from its front - low for
        a point inside geometry.
        """
        with self.ctx:
            return self._below(position, size)

    def _below(self, position: np.ndarray, size: int) -> tuple[float, float, float]:
        if getattr(self, "_probe", None) is None:
            self._probe_aux = self.ctx.texture((size, size), 2, dtype="f4")
            self._probe_color = self.ctx.texture((size, size), 4)
            self._probe_depth = self.ctx.depth_renderbuffer((size, size))
            self._probe = self.ctx.framebuffer(color_attachments=[self._probe_color, self._probe_aux], depth_attachment=self._probe_depth)
        saved = (self.fbo, self.fbo_color, self._color, self._aux, self._depth, self._size)
        self.fbo, self.fbo_color, self._color, self._aux, self._depth, self._size = (
            self._probe, self._probe, self._probe_color, self._probe_aux, self._probe_depth, self._probe_aux.size
        )
        try:
            r = self._render(Pose(np.asarray(position, float), 0.0, -89.9), 40.0, Light.flat(), False)
        finally:
            self.fbo, self.fbo_color, self._color, self._aux, self._depth, self._size = saved
        hit = r.depth > 0
        if not hit.any():
            return float("inf"), float("inf"), 0.0
        # Misses count as infinitely far: the 10th and 50th of the sorted distances, no interpolation.
        depth = np.sort(np.where(hit, r.depth, np.inf).ravel())
        return float(depth[len(depth) // 10]), float(depth[len(depth) // 2]), float(r.front[hit].mean())

    def _shadows_for(self, sun: tuple, size: int = 8192) -> None:
        """The shadow map for this sun: the whole level seen along it, orthographically."""
        import moderngl

        if self._shadow_key == sun:
            return
        lo, hi = (np.asarray(b, float) for b in self._bounds)
        centre, radius = (lo + hi) / 2, float(np.linalg.norm(hi - lo)) / 2
        d = np.asarray(sun, float)
        d /= np.linalg.norm(d)
        up = np.array([0.0, 0.0, 1.0]) if abs(d[1]) > 0.99 else np.array([0.0, 1.0, 0.0])
        right = np.cross(up, d)
        right /= np.linalg.norm(right)
        top = np.cross(d, right)
        view = np.eye(4)
        view[:3, :3] = np.stack([right, top, d])
        view[:3, 3] = -view[:3, :3] @ (centre + d * radius)
        # Eye space looks down -z, from the sun's side: depth 0..2r maps to -1..1.
        proj = np.diag([1 / radius, 1 / radius, -1 / radius, 1.0])
        proj[2, 3] = -1.0
        self._sun_mvp = proj @ view
        if self._shadow_map is None:
            self._shadow_map = self.ctx.depth_texture((size, size))
            self._shadow_map.compare_func = "<="
            self._shadow_map.repeat_x = self._shadow_map.repeat_y = False
            self._shadow_fbo = self.ctx.framebuffer(depth_attachment=self._shadow_map)
        self._shadow_fbo.use()
        self.ctx.viewport = (0, 0, size, size)
        self._shadow_fbo.clear(depth=1.0)
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.depth_func = "<"
        self.shadow_prog["mvp"].write(self._sun_mvp.T.astype("f4").tobytes())
        solid = self._passes[0]
        if solid is not None:
            solid.shadow_vao.render(vertices=solid.total)
        self._shadow_key = sun

    def release(self) -> None:
        self.ctx.release()


def _frustum(mvp: np.ndarray) -> np.ndarray:
    """The six planes (a, b, c, d; inside where a x + b y + c z + d >= 0) of a projection-view matrix."""
    m = mvp
    planes = np.array([m[3] + m[0], m[3] - m[0], m[3] + m[1], m[3] - m[1], m[3] + m[2], m[3] - m[2]])
    return planes / np.linalg.norm(planes[:, :3], axis=1, keepdims=True)
