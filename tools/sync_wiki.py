"""Regenerate docs/wiki/ (the GitHub wiki's copy) from docs/*.md, so the two never disagree.

    python tools/sync_wiki.py

Front matter is dropped, `page.md` links become wiki links (`page`), pictures point at the files
in the repository, and docs/index.md becomes Home.md. _Sidebar.md lists the pages in menu order."""

import os
import re

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DOCS = os.path.join(ROOT, "docs")
WIKI = os.path.join(DOCS, "wiki")
RAW = "https://raw.githubusercontent.com/Holdi601/3DHeat-GameCapture/main/docs/"


def front(text):
    meta = {}
    if text.startswith("---\n"):
        end = text.index("\n---\n", 4)
        for line in text[4:end].splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
        text = text[end + 5:].lstrip("\n")
    return meta, text


def wikify(text):
    text = re.sub(r"\(index\.md(#[^)]*)?\)", lambda m: "(Home" + (m.group(1) or "") + ")", text)
    text = re.sub(r"\(([a-z0-9-]+)\.md(#[^)]*)?\)", lambda m: "(" + m.group(1) + (m.group(2) or "") + ")", text)
    return re.sub(r"\((assets/[^)\s]+)\)", lambda m: "(" + RAW + m.group(1) + ")", text)


def main():
    os.makedirs(WIKI, exist_ok=True)
    pages = []
    for name in sorted(os.listdir(DOCS)):
        if not name.endswith(".md"):
            continue
        meta, body = front(open(os.path.join(DOCS, name), encoding="utf-8").read())
        target = "Home.md" if name == "index.md" else name
        with open(os.path.join(WIKI, target), "w", encoding="utf-8", newline="\n") as f:
            f.write(wikify(body))
        pages.append((meta.get("parent", ""), float(meta.get("nav_order", 999)), meta.get("title", name), target[:-3]))
    top = sorted((p for p in pages if not p[0]), key=lambda p: p[1])
    side = ["**3DHeat GameCapture**", ""]
    for _, _, title, link in top:
        side.append(f"- [{title}]({link})")
        for _, _, sub, sublink in sorted((p for p in pages if p[0] == title), key=lambda p: p[1]):
            side.append(f"  - [{sub}]({sublink})")
    with open(os.path.join(WIKI, "_Sidebar.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(side) + "\n")
    print("wrote", len(pages), "pages to", WIKI)


if __name__ == "__main__":
    main()
