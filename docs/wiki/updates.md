
# Updates

3DHeat GameCapture checks this repository's GitHub releases when it starts, says when a newer
version is out, and offers to update. Code:
[`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## When the check runs

- `python -m heat3d_capture <verb>` - before the command runs.
- `python -m heat3d_capture.ui` (and `scan.bat`) - before the window opens.
- `python -m heat3d_update` - on request, always asking GitHub afresh.

## How the check works

- The installed version is the `VERSION` file in the repository root (for example `1.0.1`).
- The newest release is asked from `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`,
  with a **5-second** timeout. A slow network never stalls the tool for longer.
- The answer is cached for **6 hours** in
  `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` (`~/.cache/3DHeat/...` without
  `LOCALAPPDATA`). Each 3DHeat tool has its own cache file. "No release yet" (HTTP 404) is cached
  like an answer; other failures are not cached and simply mean no notice.
- Versions are compared numerically (`v1.2.3` or `1.2.3`; anything after `-` or `+` is ignored).
- Offline, rate-limited or behind a proxy, the tool carries on with the version it has.

## What happens when a newer release is out

On start-up it prints, to the error stream:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- With a terminal to answer at, it asks `Update now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` mean
  yes). After a successful update **the same command is started again**, on the new code.
- Without one (a pipe, a scheduled run), it prints
  `Run python -m heat3d_update in <folder> to update.` and carries on unchanged.

## How an update is applied

Depends on how the tools were installed:

- **A git clone** (a `.git` folder and `git` on the PATH): `git pull --ff-only`. Refused while the
  checkout has local changes to tracked files - those are someone's work; commit or stash them
  first.
- **A downloaded copy**: the release's source archive is downloaded, extracted to a temporary
  folder (entries outside the archive's own folder are skipped), and **checked to be the version
  it claims** from its `VERSION` file. Then its files are copied over this folder. Within the
  release's own Python packages (`heat3d_*` folders at the top of the repository, and one level
  down for the old monorepo layout), `.py` modules the release no longer has are deleted, so a
  stale module cannot shadow its replacement.

Your own files - recordings, lap files, settings, exports, the `.venv` - are never touched: only
files that are part of the release are written.

## By hand

```bash
python -m heat3d_update            # check and update
python -m heat3d_update --check    # only say whether a newer release is out
```

It prints `Up to date: <version>.`, `No release found ... offline, or nothing published yet.`, or
the new version and what it did. Exit code 1 if the update could not be applied.

## Switching it off

Set **`HEAT3D_NO_UPDATE=1`** (any value except empty, `0`, `false`, `no`). That switches off the
start-up check and notice. `python -m heat3d_update` itself still checks when run by hand.
