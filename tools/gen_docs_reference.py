"""Write docs/cli-reference.md from the program itself - its `--help` and the column lists in the
code - so the reference cannot drift from what the tool does.

    python tools/gen_docs_reference.py            # rewrite the page
    python tools/gen_docs_reference.py --check    # exit 1 when the committed page is stale

The other pages explain each command step by step; this one is the exhaustive list."""

import os
import re
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "docs", "cli-reference.md")
sys.path.insert(0, ROOT)


def help_of(args):
    env = dict(os.environ, HEAT3D_NO_UPDATE="1", COLUMNS="100", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-m", "heat3d_capture", *args, "--help"], capture_output=True,
                       text=True, env=env, encoding="utf-8", cwd=ROOT)
    return (r.stdout or r.stderr).rstrip()


def verbs(text):
    # A sub-command list is the positional `{a,b,c} ...`; an option's choices are `[--x {a,b}]`.
    m = re.search(r"(?<![\[\w-] )\{([a-z0-9_,-]+)\}\s+\.\.\.", text.split("\n\n")[0])
    return m.group(1).split(",") if m else []


def commands(prefix=()):
    """(path, help) for the program and every verb under it, depth first."""
    text = help_of(prefix)
    yield prefix, text
    for v in verbs(text):
        yield from commands(prefix + (v,))


def units_table(units):
    rows = ["| Channel | Unit |", "|---|---|"]
    rows += [f"| `{k}` | {v} |" for k, v in units.items()]
    return rows


def build():
    from heat3d_capture.hud.output import COLUMNS as HUD_COLUMNS
    from heat3d_capture.telemetry import fulllap, lapfile

    out = ["---", "title: Command reference", "nav_order: 95", "---", "",
           "# Command reference", "",
           "Generated from the program by `tools/gen_docs_reference.py`; do not edit by hand. The other",
           "pages explain each command step by step; this page lists every option and column.", "",
           "## Commands", ""]
    for path, text in commands():
        name = " ".join(("python -m heat3d_capture",) + path)
        out += [f"### `{name}`", "", "```text", text, "```", ""]
    out += ["## Output columns", "",
            "### Lap files: units every recorder writes (`units`)", ""]
    out += units_table(lapfile.UNITS)
    out += ["", "Per-wheel channels end in `." + "`, `.".join(lapfile.WHEELS) + "`.", "",
            "### Forza lap files: channel units", ""]
    out += units_table(fulllap.UNITS)
    out += ["", "Taken once per lap, under `car`: " + ", ".join(f"`{c}`" for c in fulllap.CAR_FIELDS) + ".",
            "Not a channel: " + ", ".join(f"`{c}`" for c in sorted(fulllap.DROPPED - set(fulllap.CAR_FIELDS)))
            + " (`trackOrdinal` goes in once, as `lap.trackOrdinal`). Every other field of the packet is a channel.",
            "", "### `hud` table columns, in order", "",
            ", ".join(f"`{c}`" for c in HUD_COLUMNS) + ". Anything else a row carries follows them.", ""]
    return "\n".join(out)


if __name__ == "__main__":
    text = build()
    if "--check" in sys.argv:
        cur = open(OUT, encoding="utf-8", newline="").read().replace("\r\n", "\n") if os.path.exists(OUT) else ""
        if cur != text:
            print("docs/cli-reference.md is stale: run python tools/gen_docs_reference.py")
            sys.exit(1)
        print("docs/cli-reference.md is current")
        sys.exit(0)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote", OUT)
