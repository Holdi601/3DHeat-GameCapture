---
title: The .glb output
parent: Level reconstruction
nav_order: 6
---

# The .glb output

A reconstruction is written as a binary glTF 2.0 file (`.glb`) that the 3DHeat viewer loads
through its Level panel with no special handling - the same contract the Unreal exporter
writes. Code: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

It is written by hand rather than through a glTF library: the output is a narrow subset (one
buffer, tightly packed, no animation, no skinning) and a dependency that can write all of glTF
would bring its version skew for a few hundred lines.

## What is in a scan's file

| Part (node and mesh name) | Contents |
|---|---|
| `ground:<name>` | triangles within 35 degrees of facing up |
| `structure:<name>` | everything else |

`<name>` is the file name without extension when saving from the window, or the video's name
for `reconstruct`. A part with no triangles is left out. No `water:` part is ever written by a
scan. `asset.generator` is `heat3d-capture-scan`.

## The contract

- **One node per part**, named with the part's label; the mesh repeats the name. The viewer
  reads the *node* name first, so naming only meshes would lose the classification.
- The label is `<class>:<name>` with class `ground`, `structure` or `water` - the prefix the
  viewer matches (`^(ground|structure|water)\s*[:|]`) to take the class at its word instead of
  guessing from geometry. Ground renders solid, structures near-transparent.
- **Coordinates are viewer space**: Y up, right-handed, and **scaled to centimetres** (metres x
  100) to match the Unreal exporter, so a capture and an engine export of the same place load at
  the same size with the same camera defaults. A scan placed by Forza telemetry is the exception
  in handedness: it stays in the game's own world, Y up and left-handed, exactly as the lap files
  are, so the laps recorded over it land on it. When a scan's scale was found on a later keyframe
  ([Scale](reconstruction-pose.md#scale)), that factor is folded into the scale written.
- `COLOR_0` is read by the viewer, which shades the ground with it when its Level panel's
  *Captured colour* switch is on (off by default).
- A scan with spots marked by hand gets `<name>.marks.json` beside it; see
  [Saving](reconstruction-scan-ui.md#saving).
- Per primitive: `POSITION` (float VEC3, with `min` and `max`, which the viewer frames its camera
  from), `NORMAL` (float VEC3), optional `COLOR_0` (float VEC3, 0..1), optional `TEXCOORD_0`;
  indices as 16-bit when every index is below 65,536, else 32-bit; mode triangles.
- Every buffer view starts 4-byte aligned; the JSON chunk is padded with spaces and the BIN chunk
  with zeros to 4 bytes.

## Checks before writing

Each part is validated and refused with a message naming it when it has no vertices, an index
count that is not whole triangles, an index out of range or negative, non-finite positions, or
normals or colours that do not match the vertex count. Normals are computed when missing,
**area-weighted** (marching cubes leaves slivers beside large faces, and an unweighted average
lets tiny triangles outvote the face they sit on); a degenerate vertex gets "up". Writing no
parts at all is an error.

Export returns nothing - and the window says "Nothing to save" - when the volume yields no
surface, rather than writing an empty file that would read as a successful scan.

## Textures

The writer supports a PNG base-colour texture per part (with UVs, a double-sided, non-metallic,
fully rough material). Scans do not use it; they carry per-vertex colour. See
[colour](reconstruction-fusion-and-texture.md#colour).

## The reference level

`geometry/reference.py` builds a synthetic level of exactly known size through the same writer:
a 400 m subdivided ground, three 20 x 20 x 12 m buildings and a 50 m pond 1.5 m below ground, each
class in a distinct flat colour. The viewer's own tests generate it and parse it with the viewer's
real parser, so the file format stays under test on both sides with no game and no capture
hardware.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
