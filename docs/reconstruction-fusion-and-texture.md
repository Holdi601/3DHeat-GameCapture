---
title: Fusion, coverage and colour
parent: Level reconstruction
nav_order: 5
---

# Fusion, coverage and colour

Code: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Every placed keyframe updates two sparse grids at once: the **surface volume**, which becomes
the mesh, and the **coverage grid**, which says how much to believe it and where to go back.
Both are updated per keyframe, not at the end, because the coverage map is what the player
steers by.

## From depth to points

For each keyframe whose pose is known **and** whose depth has a scale:

1. Every second pixel in each direction is used (`PIXEL_STRIDE = 2`; neighbouring pixels of
   one surface are not independent measurements).
2. Depth is converted to metres by the frame's affine fit.
3. Kept only between **0.35 m** (nearer is the weapon, the HUD, the bonnet) and **60 m**
   (monocular error grows roughly with the square of distance, so far points are noise shaped
   like geometry) and only on world pixels of the mask.
4. Lifted through the camera model and moved into the world by the pose.
5. Each point carries the pixel's colour.

A frame that is positioned but has no depth scale is counted as *placed* but not *fused*.

## The surface volume

`SurfaceVolume(voxel=0.25)` - the voxel is the window's "Surface detail".

### Weighted occupancy, not a TSDF

A truncated signed distance field carves along every pixel's ray and gets thin structures and
clean free space right, because it knows a ray passed *through* empty space. That means walking
the ray for every one of hundreds of millions of pixels. This volume instead accumulates
**weighted occupancy** per voxel and runs marching cubes on the smoothed result: fast enough to
run while scanning, on a machine with no usable GPU, and the output is a closed surface rather
than a point cloud. The cost: thin structures and free space are worse than a TSDF would get.

### Integrating a frame

- Points are binned into voxels (`floor(point / voxel)`).
- Each voxel touched gets `weight x sqrt(count / max_count)`, where `count` is how many of the
  frame's points fell in it and `weight = max(0.1, pose confidence)`. Square root: past a point,
  more pixels of the same surface from the same place stop being evidence; weighting by pose
  confidence keeps a doubtful pose from pushing the surface around.
- Colour is a running weighted mean per voxel.

The grid is **sparse**: a walked route touches a tiny fraction of its bounding box. Voxel
coordinates are packed into one 64-bit key (21 bits per axis, up to +-1,048,575 voxels - at
0.25 m about +-262 km) and looked up with a sorted array and binary search, fully vectorised.

### Extracting the mesh

1. Voxels with weight below **0.35** are dropped (stray single points at silhouette edges would
   become spikes).
2. Weights are scaled by the **75th percentile** across the scan and clipped to 1.
3. The occupied space is cut into **blocks of 64 voxels** per side, each realised with a
   **3-voxel halo** of its neighbours' data (without it, every block boundary closes into a
   wall and a road comes out as a row of boxes).
4. Each block's field is smoothed with a Gaussian (sigma 0.8 voxel) to remove the wrinkle depth
   noise leaves.
5. **Pass one**: the 99th percentile of the smoothed field, sampled across all blocks (at most 2
   million values), sets one global level scale. Normalising per block would promote a lone
   outlier to a full surface in its own empty block.
6. **Pass two**: each block's field divided by that scale, marching cubes at **0.5**. A triangle
   belongs to the block its **centroid** falls in, so triangles straddling a seam are emitted
   exactly once.
7. Vertices move to world units at voxel centres; each vertex takes its voxel's colour
   (mid-grey where it falls outside an occupied voxel).

Block-wise extraction is what makes a track-sized scan possible: one dense array over a
kilometre-square box at 0.25 m would be billions of cells. `tests/test_track_scale.py` pins
that it works at that scale with memory proportional to what was scanned.

### Ground and structure

`classify` labels each triangle by its normal (oriented by the extracted vertex normals): within
**35 degrees of straight up** is `ground`, everything else `structure`. The viewer draws ground
solid and structures near-transparent. **Water is never claimed** - it cannot be told from flat
ground by shape, and a wrong label would render a courtyard as a lake. Each label becomes one
part of the `.glb` ([The .glb output](glb-output.md)).

## Coverage

`CoverageGrid(voxel=0.5)` records, per half-metre cell, four things that are not the same thing:

| Term | Stored | Score (each clipped to 0..1) | Why it counts separately |
|---|---|---|---|
| How many times seen | count of keyframes that saw the cell | `count / 3` | once is a guess with nothing to average against |
| From how many directions | sum of unit view directions | `(1 - spread) / (1 - 0.93)`, where spread = length of the sum / count | twenty frames walking straight at a wall have no parallax between them; two views thirty degrees apart are worth more |
| From how far | nearest viewing distance | `1 - nearest / 40 m` | depth error grows roughly with distance squared |
| How well the camera was placed | best pose confidence | the confidence | geometry fused with a doubtful pose lands in the wrong place |

A frame's points are grouped per cell first, so ten thousand pixels of one wall count as one
observation from one direction.

**Quality = the product of the four terms**, not the average: they are conditions that each have
to hold. A place seen two hundred times from one direction at sixty metres is badly observed, and
an average would hide that behind one excellent term.

Headline figures (`summary`): occupied cells, the share with quality at least 0.5 ("% well
seen" in the window), mean quality, and volume.

### Weak spots

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. cells with quality below 0.35 are weak;
2. weak cells are grouped by **connectivity** (26-neighbourhood, union-find over the occupied
   cells only - not a raster over the bounding box, which on a long drive is millions of empty
   cells);
3. groups of fewer than 8 cells are ignored;
4. each group's reason is the most common *weakest term* of its cells, and its position the mean
   of its cells;
5. sorted largest first (then worst quality), at most 8.

| Reason | Advice shown |
|---|---|
| few views | Seen only once or twice — walk past it again. |
| one direction | Only seen from one angle. Step sideways and look at it again. |
| distant | Only seen from far away. Get closer to it. |
| poor tracking | The camera was not well located here. Approach it more slowly. |

Connectivity matters: grouping by a fixed block grid reports one neglected side room as many
separate rings, and nobody can tell eight places from one place counted eight times.

### The plan view

`top_down(resolution)` projects the cells onto x/z and keeps the **best** quality per column
(someone standing in a room has poor coverage of the ceiling and excellent coverage of the
floor; averaging would paint the room amber). Never-observed columns are marked separately. The
window draws it at 200 x 200, the overlay at 120 x 120 ([The scan window](reconstruction-scan-ui.md#the-coverage-map)).

### Is this reconstructable?

Every 25 fused frames, once there are at least 500 cells:

| Finding | Verdict | Message (shortened) |
|---|---|---|
| fewer than 2% of cells have view spread below 0.93 | not reconstructable | Almost no parallax. Either the camera never looks aside, or the tracking is drifting so the same surface never lands twice in the same place. Check the placed-frame count: if that is high, it is drift. |
| median nearest distance over 25 m | not reconstructable | Everything was seen from N m away or further ... Get closer to what you want. |
| fewer than 6% with good spread | reconstructable, warned | Thin parallax — the geometry will be rough. Moving sideways relative to what you are looking at helps most. |

Low parallax has two causes this cannot tell apart, which is why the message names both.

## Colour

Fusion's per-voxel colour is cheap and live, and blurry: every pixel in a quarter-metre cell is
averaged, including ones seen edge-on from thirty metres. So at export the mesh is coloured
again, once, from the frames themselves:

- **Frames kept**: up to **160** keyframes (image and pose), chosen by reservoir sampling so they
  spread across the whole scan rather than its tail.
- **Per vertex** (`project_colours`), each kept frame contributes if the vertex is in front of
  the camera and inside the image, the surface is turned no more than about 70 degrees away from
  facing the camera head-on (`|normal . view| > 0.34`), it is nearer than **35 m**, and nothing
  nearer stood in front of it (below).
- Each such view is scored `facing x (1 - distance / 35)`, so a close head-on view beats a
  distant glancing one. The **4 highest-scoring** views of each vertex are kept - whatever order
  the frames are in, a better view replaces the weakest of the four - and blended, weighted by
  that same score.
- **Occlusion**: in each frame the mesh's own vertices in view are drawn into a depth buffer of
  2-pixel cells, keeping the nearest per cell. A vertex more than `0.3 m + 5%` of its distance
  behind the nearest one in its cell was hidden in that frame - a wall between the camera and the
  road beyond - and that view counts for nothing. The test only knows the mesh: an occluder that
  was never fused (a passing car, a cockpit pillar outside the HUD mask) is not caught.
- A vertex no frame saw keeps its voxel colour; a vertex with neither is mid-grey (black would
  read as a hole).

Colour is written as per-vertex `COLOR_0`, not as a texture atlas. The viewer's default look is a
grey map under saturated heat; colour is there to find the road on a scanned circuit, where
geometry alone does not separate it from the verge, and is shown behind the viewer's *Captured
colour* switch in its Level panel. An atlas would multiply the file size and need an unwrapper,
for a view that is deliberately not the default. Blender and other glTF tools read `COLOR_0`.
