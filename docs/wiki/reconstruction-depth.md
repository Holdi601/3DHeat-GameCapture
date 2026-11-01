
# Depth

The one thing external capture cannot give is geometry. The game knows every pixel's depth and
it sits in a buffer this project deliberately does not touch, so depth is **inferred from the
picture**. That is the accuracy ceiling of the whole approach.

Code: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(what the scanner runs),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(the PyTorch path and the scale fit),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## The model

**Depth Anything V2**, relative variant. It predicts *relative inverse depth*: a disparity-like
field correct only up to an unknown affine transform,
`metric_disparity = a * predicted + b`, different for every frame. The network is good at what
is hard from one image (relative shape, edges, thin structure) and silent about what it cannot
know (scale). Scale comes from elsewhere - see [Camera pose and scale](reconstruction-pose).

| Size | Hugging Face id | Licence |
|---|---|---|
| **Small** (default) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** - commercial use permitted |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 - non-commercial only |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 - non-commercial only |

A reconstruction inherits the licence of the model that made it. Small is the default
everywhere precisely so that a scan carries no restriction unless someone chooses otherwise.
The metric variants (`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) are
named in the code but not used by the scanner. See [Models and licences](models-and-licences).

## Building the model

The scanner runs an ONNX file and never imports PyTorch. The file has to be made once:

- **From the window**: "Set up the depth model" (see [The scan window](reconstruction-scan-ui#when-there-is-no-depth-model-yet)),
  which runs the command below with `--size small`.
- **By hand**, in an environment with PyTorch, `transformers` and `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Option | Default | Meaning |
|---|---|---|
| `--size` | `small` | `small`, `base` or `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | output file |
| `--side` | `518` | square input size; must be a multiple of 14 (the ViT patch size); 518 = 14 x 37 is the training resolution |
| `--opset` | `17` | ONNX opset; 17 is widely supported by DirectML and CUDA |

What the converter does:

- Downloads the checkpoint from Hugging Face (`AutoModelForDepthEstimation`).
- Wraps it so the **ImageNet normalisation is inside the graph**: the model takes RGB in the
  0-255 range as float (`pixels`, shape `batch x 3 x side x side`) and outputs
  `inverse_depth`. There is exactly one copy of the mean and standard deviation, so they cannot
  drift from the checkpoint.
- **Fixed spatial size**, dynamic batch. DirectML and TensorRT compile per shape; a dynamic
  height and width would recompile on the first frame of every new resolution, a visible stall
  in a live capture.
- Exports through the **TorchScript path** (`dynamo=False`): the dynamo graph failed on
  DirectML at a Reshape node, and it writes the weights as a separate `.onnx.data` file. The
  TorchScript path produces one self-contained file.
- Prints the file and its size. The tracer's warnings about baked-in shapes are expected.

The scanner looks for `models/depth-*.onnx` and uses the first by file name.

## Running it: ONNX Runtime

`OnnxDepthEstimator` builds one ONNX Runtime session, lazily, with full graph optimisation, on
the backend the ladder chose, with CPU appended as a fallback so a provider that fails at
session creation (an old driver) means a slow scan, not a crash. See
[Runtime and dependencies](runtime#inference-backends).

- `warm_up()` builds the session and runs one blank frame (the first inference on a fresh
  graph is several times slower than the steady state).
- `measure_throughput(frames)` times that many blank frames after warm-up; the window uses 6
  and quotes the result as views per second.

### Letterboxing, not stretching

The graph takes a fixed square; gameplay is 16:9. Squashing a frame into a square would change
the apparent shape of everything, and since the output is a geometric estimate that would be
fused as real wrong geometry. So each frame is:

1. scaled to fit the square, keeping its aspect ratio (area interpolation down, cubic up);
2. padded with **mid-grey (114)** - black or white reads as a strong edge and bleeds a false
   depth discontinuity into the content beside it;
3. run through the model;
4. the padding is cropped off the prediction **before** it is resized back (cubic) to the
   frame's resolution, so the margin never bleeds into real pixels.

The result is a `DepthMap` with `metric=False` at the source frame's size.

## The PyTorch path

`DepthEstimator` runs the Hugging Face model directly (fp16 on CUDA, fp32 on CPU), batched by
frame size, each prediction resized back bicubically. The scanner does not use it; the offline
`reconstruct` command does (see [Offline reconstruction](reconstruction-offline)), which is
one reason that command needs PyTorch and `transformers`.

## From relative to metric: `fit_scale` and `AffineFit`

Turning predicted inverse depth into metres needs the affine `scale * predicted + shift`. When
anchors of known depth are available (feature points triangulated between known poses, or the
previous frame's anchored depth), `fit_scale` solves it:

- least squares **in disparity**, not in depth - the network's error is roughly uniform in
  disparity, while in depth a few distant anchors (where one pixel of disparity is tens of
  metres) would dominate;
- **iteratively reweighted** (12 iterations, Cauchy-style weights `1 / (1 + (r / 3 MAD)^2)`),
  because anchors carry gross outliers (a match on a moving car, a tracking glitch) and one such
  anchor in a plain fit drags the whole frame;
- needs at least 2 usable anchors; reports the median absolute residual and the inlier count
  (residual within 3 x the median).

`AffineFit.apply` returns depth in metres with **+inf** for sky. It checks the predicted value
as well as the anchored one: a sky pixel predicting zero comes out at `shift` - small, positive,
finite - and would otherwise land every sky pixel on a phantom shell at one distance. Anything
predicted at or below `1e-4` is sky, whatever the fit says.

Fusion then keeps only depths between 0.35 m and 60 m (see
[Fusion](reconstruction-fusion-and-texture#from-depth-to-points)).
