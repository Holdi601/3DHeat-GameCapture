
# Camera pose and scale

A depth map says how far things are from *a* viewpoint. Turning many of them into one level
needs to know where each viewpoint was, and in what units. This page covers the live paths;
the offline feed-forward solve is on [Offline reconstruction](reconstruction-offline).

Code: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## The camera model

`Intrinsics.from_fov(width, height, fov)` builds a pinhole camera from the **horizontal field of
view** you set in the window: `fx = (width / 2) / tan(fov / 2)`, square pixels (`fy = fx`), the
principal point at the frame's centre. A game does not publish its projection, so this is the
one assumed number: too narrow and the scene reads deeper than it is. The offline path uses
65 degrees.

A `Pose` is stored **world-from-camera**: `rotation` (3 x 3) and `translation` = the camera's
centre in the world, which is what the trajectory, the coverage map and the overlay all want.

## Visual odometry (the default)

`VisualOdometry` tracks each keyframe against the previous one:

1. **Features**: ORB, up to 1500 per frame, detected only on the world mask (see
   [Capture](reconstruction-capture#what-is-not-the-world)).
2. **Matches** to the previous keyframe: brute force, Hamming distance, cross-checked (only
   mutually best pairs).
3. **Lift to 3D**: the previous frame's depth is already in world units, so its matched pixels
   become world points.
4. **Place the camera**: `solvePnPRansac` among those points (reprojection error 3 px,
   confidence 0.999, 200 iterations). The translation comes out in the same units, so **the
   scale crosses the gap**.
5. **Anchor this frame's depth**: its own predicted inverse depth is fitted (`fit_scale`)
   against the PnP inliers' depths, and the cycle repeats.

The **first frame** is the origin: identity pose, and its depth's affine is either the ground
calibration below or, without one, the identity (the reconstruction is then self-consistent
but unit-less).

A pose needs at least **18 RANSAC inliers** - clearly more than PnP's minimum of six, since a
solution from barely enough points is exactly the one that is confidently wrong.

### Confidence

Each placed frame gets a confidence in 0..1 that weights its fusion and its coverage:

| Pose from | Confidence |
|---|---|
| telemetry | 1.0 |
| a feed-forward solve | 0.85 |
| visual tracking | `inliers / matches x min(1, inliers / 60)` |

### When tracking breaks

A frame that cannot be placed is reported, never guessed: `no features in the frame (N
found)`, `too few matches to place the camera`, `could not relocalise`. No pose is recorded,
and nothing is fused. Carrying on from the last pose, or starting a fresh origin, would put the
next stretch of level at an arbitrary offset - a seam that looks like real geometry.

After a break, each new frame is **relocalised** against a database of past keyframes (every
4th tracked frame is added, up to 120, oldest dropped), most recent first, with the same
match-and-PnP step. Until one succeeds, frames are dropped. A recovered frame continues in the
same coordinate frame. Recoveries are counted and shown in the window (`N recovered`).

### Loop closure: off

The same database supports loop closure: matching against keyframes from much earlier to
detect a revisit and snap the track back onto it. **It is off by default, and the scanner never
turns it on** (`Reconstructor(loop_closure=False)`). On repetitive scenery - a rally stage, a
corridor, a row of trees - every stretch looks like every other and feature matching confirms
false revisits, which pins the camera near where it started while it drives on. Doing it
properly needs place recognition (a bag-of-words vocabulary or a learned descriptor) and
geometric verification against a map, which is not built.

When enabled from code, a closure needs: a keyframe at least 60 keyframes old, within 6 m of
the current pose, matched with at least 90 inliers, moving the pose by more than 0.02 m and less
than 6 m. Even then it only replaces the current pose; it is not a pose graph and does not move
earlier frames or fused geometry.

## Telemetry poses

With **Racing telemetry (Forza) -> Listen for position data** on, the camera path comes from
Forza's Data Out instead of from the pictures (`ForzaPoseSource`):

- A thread listens on `127.0.0.1:<port>` (5300 by default) with the same layout detection as the
  recorders ([Forza](telemetry-forza)); packets are used while `isRaceOn` is set. A busy port
  is reported, not raised: telemetry is an upgrade and the scan carries on visually.
- Each packet is stamped with the **monotonic time it arrived** - the same clock the capture
  stamps frames with. The game's own timestamp counts from something unrelated, so it is not
  used for alignment. Loopback jitter of a millisecond or two is about 6 cm at 200 km/h.
- A rolling 30-second buffer is kept. A frame's pose is **interpolated** from the samples either
  side of its capture time: position linearly, rotation by spherical interpolation (a blended
  matrix is not a rotation and would skew every point). Across a gap longer than **0.35 s**, or
  outside the buffer, there is no pose.
- `pose_from_forza`: the camera is placed at the car (a chase camera's offset is not published).
  **Positions are kept exactly as the game sends them**: Forza's world is already Y-up (x and z
  across the map, y the height), which is how the lap files and route files write it, so the
  surface lands on the same coordinates as the laps recorded over it. (An earlier version swapped
  y and z for a "Z-up" world and laid the track on its side.)
- The rotation is yaw, then pitch, then roll, with the senses read off recorded laps: the
  direction of travel `atan2(dx, dz)` equals the yaw, the slope climbed equals minus the pitch
  (positive is nose down), and the roll is positive when the right-hand suspension is compressed
  (positive drops the right side). The car's axes (x right, y up, z forward) are then turned into
  the camera's (x right, y down, z forward) by flipping y.
- Forza's world is **left-handed** and the camera's frame is not, so the resulting
  world-from-camera matrix is a reflection (determinant -1), and the scan comes out left-handed
  like the lap files. Interpolation is unaffected (the turn between two such poses is a proper
  rotation).
- When a frame has no telemetry pose (a gap), the reconstructor falls back to **visual tracking**
  for that frame, carrying on from the last telemetry pose, and goes back to the feed's poses as
  soon as it answers. PnP only returns rotations, so in a mirrored world it is solved with the
  world mirrored through z and the mirror folded back in; the frame lands in the game's
  coordinates. Only if visual tracking fails too is the frame untracked.

### Depth scale from telemetry

The game says where the camera is, not how far away anything is, so each frame's depth still
needs anchoring - but not by chaining from frame zero, whose unit is arbitrary while the poses
are in metres. Instead, features matched between the previous and the current frame (at least
8) are **triangulated directly from the two known poses**, in metres, and the depth map is
fitted to the points in front of the camera. Every frame is anchored against the telemetry, so
there is no chain to drift.

If the two poses are less than **0.05 m** apart the rays are near-parallel and triangulation is
noise, so the frame is left unanchored: positioned exactly, but not fused ("positioned, but its
depth has no scale yet"). That is why the window counts *placed* and *fused* frames separately.

## Scale

Visual odometry chains relative scale correctly, but the whole level still floats on one unknown
factor. Depth Anything's relative output comes out in arbitrary units, so leaving the first
frame at the identity puts the world within metres of the camera at an arbitrary size.

`GroundCalibrator` pins that factor from **how high the camera is above the ground**, measured on
the **first keyframe** and, when that has no usable ground, on the following ones:

- Camera height: **1.15 m** (a driver's eye line) - the window always uses this; scripts can
  pass 1.70 m (`WALKING_HEIGHT`, a standing player) or `None` (no calibration).
- Ground sample: rows 62-92% down the frame (below the horizon, above the bonnet or weapon) and
  columns 30-70% across (away from the verges).
- Each pixel there with a usable prediction is lifted with depth `1 / predicted` in the network's
  units; points below the optical axis give a height below the camera. Their median is the
  camera height in network units, so `metres per unit = 1.15 / median`, and the frame's affine is
  `scale = 1 / metres_per_unit`, shift 0.
- Trusted only with at least 200 ground samples and a **scatter** (median absolute deviation over
  median) below **0.60**.
- On the first keyframe the fit becomes the origin's unit, so the scan is in metres from the
  start. When the first keyframe has no usable ground, the scan starts unit-less and each later
  tracked keyframe is tried, up to **30 frames** in all. The first one that calibrates gives
  *metres per unit*: the median, over the ground band, of the depth its ground implies over the
  depth the chain gave that frame. Everything already fused is in the first frame's unit, so the
  factor is not fed back into the chain; it is applied to the whole level (and to the marked
  spots) when it is written, and to the distance shown meanwhile. Voxel size is then in the first
  frame's units, so its size in metres differs from the setting by that factor.
- After 30 frames without ground the scan stays unit-less, and says so.
- With telemetry, later keyframes are not tried: the depth is anchored to the telemetry's metres.

Being within ten per cent of the true size beats being out by a factor of a thousand; telemetry,
where available, makes it unnecessary. The note is shown in the window under the tracking line,
as `Size: ...`: `measuring the ground`, `no flat ground in view yet - still looking (N frames
tried)`, `scaled from a 1.15 m camera height, ...` (with `found on frame N, so the level is scaled
by F when it is written` when it came later), `no usable ground in the first N frames - sizes are
relative, not metres`, or `in metres, from the telemetry's positions`.

## Bundle adjustment and long tracks (not wired in)

Two pieces exist for a future windowed solver and are **not used by the scanner**:

- **`FeatureTracks`** keeps feature identity across hundreds of frames with Lucas-Kanade
  tracking (600 features, re-seeded below 60%, forward-backward tolerance 1 px, new features 10 px
  from existing ones), which is what bundle adjustment needs - descriptor matching between
  consecutive frames only gives pairs.
- **`bundle_adjust`** refines a window of poses and points together with
  `scipy.optimize.least_squares` (trust region, soft-L1 loss with a 2 px scale, an explicit
  Jacobian sparsity pattern, fixed cameras restored exactly). Tested against known truth in
  `tests/test_bundle.py`.

`WindowedOdometry` combines them (12-keyframe windows, a solve every 3 keyframes, the first two
cameras fixed, points over 6 px of error dropped, jumps over 6 times the recent step refused). Its
docstring records that on real footage it **collapsed the path and was much slower** than
frame-to-frame tracking, with gauge freedom (scale) and a depth-based bootstrap as known causes and
a third cause unidentified. So frame-to-frame odometry remains the default; the likely fix noted
in the code is a two-view essential-matrix bootstrap with the baseline fixed from the
ground-plane calibration.
