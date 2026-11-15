"""Draw this repository's documentation diagrams as SVG from the specs at the end of this file, so the
labels live in one place and a translated page can draw the same diagram with its own strings.

    python tools/docs_diagrams.py                 # English, into docs/assets/img/
    python tools/docs_diagrams.py --lang de       # labels from docs/assets/i18n/de.json, into docs/assets/img/de/
    python tools/docs_diagrams.py --strings       # also write docs/assets/i18n/en.json: every label, to translate

A strings file maps an English label to its translation; a missing label stays English.
Every label is one <text> node. Width at most 860, text at least 14 units, so the pictures
stay readable at the page's width."""
import html
import json
import os
import sys

W = 860
FONT = "Segoe UI,Helvetica,Arial,sans-serif"
MONO = "Consolas,Menlo,DejaVu Sans Mono,monospace"
INK, SUB, LINE, CARD, BOX, HI = "#1f2328", "#3d4450", "#8a94a3", "#f7f8fa", "#ffffff", "#e8f0fe"

_strings = {}
_seen = []


def t(s):
    if s not in _seen:
        _seen.append(s)
    return _strings.get(s, s)


def esc(s):
    return html.escape(t(s), quote=True)


def text(x, y, s, size=15, weight="400", fill=INK, anchor="middle", mono=False):
    fam = MONO if mono else FONT
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-family="{fam}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}">{esc(s)}</text>')


def svg(w, h, title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="{esc(title)}">\n<rect width="{w}" height="{h}" rx="10" fill="{CARD}" stroke="#d0d4db"/>\n'
            + "\n".join(body) + "\n</svg>\n")


ARROW = ('<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
         f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker></defs>')


def steps(title, items, per_row=3, notes=()):
    """items: (heading, line, line, ...) boxes in order, wrapped `per_row` to a row.
    notes: (heading, line, ...) dashed boxes under the chain: remedies or side facts, not steps."""
    gap, bw, bh, top = 40, 0, 104, 52
    bw = (W - 40 - gap * (per_row - 1)) / per_row
    rows = (len(items) + per_row - 1) // per_row
    h = top + rows * bh + (rows - 1) * 36 + 24 + (len(notes) and (bh + 30))
    out = [ARROW, text(20, 32, title, 18, "600", anchor="start")]
    pos = []
    for i, item in enumerate(items):
        r, c = divmod(i, per_row)
        x, y = 20 + c * (bw + gap), top + r * (bh + 36)
        pos.append((x, y))
        out.append(f'<rect x="{x:.0f}" y="{y}" width="{bw:.0f}" height="{bh}" rx="8" fill="{BOX}" stroke="{LINE}"/>')
        out.append(text(x + bw / 2, y + 28, item[0], 16, "600"))
        for k, line in enumerate(item[1:]):
            out.append(text(x + bw / 2, y + 54 + k * 21, line, 14, fill=SUB))
    for i in range(len(items) - 1):
        (x0, y0), (x1, y1) = pos[i], pos[i + 1]
        if y0 == y1:
            out.append(f'<line x1="{x0 + bw + 4:.0f}" y1="{y0 + bh / 2}" x2="{x1 - 4:.0f}" y2="{y1 + bh / 2}" '
                       f'stroke="{LINE}" stroke-width="2" marker-end="url(#a)"/>')
        else:
            out.append(f'<path d="M{x0 + bw / 2:.0f},{y0 + bh + 2} V{y0 + bh + 18} H{x1 + bw / 2:.0f} V{y1 - 4}" '
                       f'fill="none" stroke="{LINE}" stroke-width="2" marker-end="url(#a)"/>')
    if notes:
        y = top + rows * bh + (rows - 1) * 36 + 30
        nw = (W - 40 - gap * (len(notes) - 1)) / len(notes)
        for j, n in enumerate(notes):
            x = 20 + j * (nw + gap)
            out.append(f'<rect x="{x:.0f}" y="{y}" width="{nw:.0f}" height="{bh}" rx="8" fill="{HI}" '
                       f'stroke="{LINE}" stroke-dasharray="6 4"/>')
            out.append(text(x + nw / 2, y + 28, n[0], 16, "600"))
            for k, line in enumerate(n[1:]):
                out.append(text(x + nw / 2, y + 54 + k * 21, line, 14, fill=SUB))
    return svg(W, int(h), title, out)


def legend(title, rows, note=None):
    """rows: (colour, name, meaning). A colour swatch, the part name (monospace), what it holds."""
    h = 56 + len(rows) * 34 + (30 if note else 0)
    out = [text(20, 32, title, 18, "600", anchor="start")]
    for i, (col, name, meaning) in enumerate(rows):
        y = 50 + i * 34
        out.append(f'<rect x="20" y="{y}" width="22" height="22" rx="4" fill="{col}" stroke="#55606e"/>')
        out.append(f'<text x="54" y="{y + 17}" font-family="{MONO}" font-size="15" fill="{INK}">{html.escape(name)}</text>')
        out.append(text(330, y + 17, meaning, 15, fill=SUB, anchor="start"))
    if note:
        out.append(text(20, h - 16, note, 14, fill=SUB, anchor="start"))
    return svg(W, h, title, out)


def run(diagrams, root):
    """diagrams: {file name: function returning SVG text}. Writes English, or --lang <code>."""
    global _strings
    lang = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else None
    out = os.path.join(root, "docs", "assets", "img")
    if lang:
        with open(os.path.join(root, "docs", "assets", "i18n", f"{lang}.json"), encoding="utf-8") as f:
            _strings = json.load(f)
        out = os.path.join(out, lang)
    os.makedirs(out, exist_ok=True)
    for name, make in diagrams.items():
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(make())
        print("wrote", os.path.join(out, name))
    if "--strings" in sys.argv:
        i18n = os.path.join(root, "docs", "assets", "i18n")
        os.makedirs(i18n, exist_ok=True)
        with open(os.path.join(i18n, "en.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({s: s for s in _seen}, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print("wrote", os.path.join(i18n, "en.json"), len(_seen), "labels")


def grid(title, headings, rows, colours=None):
    """A table of boxes: `headings` over the columns, each row a chain left to right.
    A cell is (heading, line, ...) or None. `colours` gives a fill per column."""
    n = len(headings)
    gap, bh, top = 40, 70, 84
    bw = (W - 40 - gap * (n - 1)) / n
    h = top + len(rows) * (bh + 14) + 10
    out = [ARROW, text(20, 32, title, 18, "600", anchor="start")]
    for c, head in enumerate(headings):
        out.append(text(20 + c * (bw + gap) + bw / 2, 68, head, 15, "600", fill=SUB))
    for r, row in enumerate(rows):
        y = top + r * (bh + 14)
        prev = None
        for c, cell in enumerate(row):
            if cell is None:
                continue
            x = 20 + c * (bw + gap)
            fill = (colours or [BOX] * n)[c]
            out.append(f'<rect x="{x:.0f}" y="{y}" width="{bw:.0f}" height="{bh}" rx="8" fill="{fill}" stroke="{LINE}"/>')
            lines = [cell] if isinstance(cell, str) else list(cell)
            y0 = y + bh / 2 - (len(lines) - 1) * 10.5 + 5
            for k, line in enumerate(lines):
                out.append(text(x + bw / 2, y0 + k * 21, line, 16 if k == 0 else 14, "600" if k == 0 else "400",
                                fill=INK if k == 0 else SUB))
            if prev is not None:
                px = 20 + prev * (bw + gap) + bw
                out.append(f'<line x1="{px + 4:.0f}" y1="{y + bh / 2}" x2="{x - 4:.0f}" y2="{y + bh / 2}" '
                           f'stroke="{LINE}" stroke-width="2" marker-end="url(#a)"/>')
            prev = c
    return svg(W, int(h), title, out)


# --- this repository's diagrams -------------------------------------------------------------

IN, CMD, OUT = "#e8f0fe", "#fff4e0", "#e6f4ea"


def overview():
    return grid("What goes in, which command, what comes out", ("You have", "You run", "You get"), [
        (("Racing game telemetry", "network / shared memory / mod"), ("telemetry",), ("<lap>.lap.json", "3DHeat: Race tab")),
        (("A Forza lap", "driven once, for the route"), ("route",), ("route .npz + .json", "GameFiles: course")),
        (("FH Companion lap library", "laps already driven"), ("laps",), ("route + samples .csv", "GameFiles: course")),
        (("The screen while you play", "Windows screen capture"), ("scan window",), ("level .glb", "3DHeat: Level panel")),
        (("A recording (video)", "after the session"), ("reconstruct",), ("level .glb", "3DHeat: Level panel")),
        (("A recording (video)", "after the match"), ("hud", "locate (experimental)"), ("own track .parquet", "3DHeat: Heatmap tab")),
    ], colours=[IN, CMD, OUT])


def locate_pipeline():
    return steps("locate: from a level and a recording to your own positions", [
        ("level .glb", "from GameFiles", "or a scan"),
        ("locate build", "renders the level", "and indexes them"),
        ("locate frames", "matches each frame", "against the renders"),
        ("<out>.parquet", "one row per frame", "+ summary, check pictures"),
        ("locate eval", "optional: compare", "with known poses"),
    ], per_row=3, notes=[
        ("locate train", "optional: a per-map", "model for build"),
        ("hud, or refmap + minimap", "a prior and the lives", "for frames"),
    ])


def hud_outputs():
    return steps("hud: what one recording gives", [
        ("recording", "your own video", "after the match"),
        ("hud", "--game bf6", "needs ffmpeg"),
        ("four files", "written next to", "the -o path"),
    ], per_row=3, notes=[
        ("<out>.parquet", "track and", "your own events"),
        ("<out>.events.jsonl", "actions and", "the kill feed"),
        ("<out>.summary.json", "kills, deaths,", "lives"),
        ("<out>.map.png", "+ .map.json:", "minimap mosaic"),
    ])


def lap_splitting():
    return steps("A recording becomes one file per lap", [
        ("Packets", "one per frame", "from the game"),
        ("Splitter", "lap counter, start line", "or end of stage"),
        ("lap n .lap.json", "one per lap", "complete: true"),
    ], per_row=3, notes=[
        ("partial lap", "stopped mid-lap:", "complete: false"),
        ("raw sidecar", "every packet,", "kept whole"),
    ])


def reconstruct_stages():
    return steps("reconstruct: the stages it prints, in order", [
        ("masking", "learns what never", "moves (HUD, cockpit)"),
        ("planning", "picks frames", "by motion"),
        ("solving", "camera path in", "VGGT windows"),
        ("fusing", "depth along", "the path"),
        ("exporting", "one .glb", "for the viewer"),
    ], per_row=3)


if __name__ == "__main__":
    run({
        "overview.svg": overview,
        "locate-pipeline.svg": locate_pipeline,
        "hud-outputs.svg": hud_outputs,
        "lap-splitting.svg": lap_splitting,
        "reconstruct-stages.svg": reconstruct_stages,
    }, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
