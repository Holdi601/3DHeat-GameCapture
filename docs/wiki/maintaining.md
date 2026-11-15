# Maintaining these docs

The checklist for every release, so the code, the English pages and their translations stay in
step. Do the steps in order.

1. **Regenerate the generated pages.**
   - `python tools/gen_docs_reference.py` rewrites [Command reference](cli-reference) from
     `--help` and the column lists in the code. `--check` exits 1 when the page is stale: run it
     before every release.
   - `python tools/docs_diagrams.py` redraws the diagrams in `docs/assets/img/`;
     `--strings` also refreshes `docs/assets/i18n/en.json`, the labels to translate.
   - `python tools/sync_wiki.py` regenerates the GitHub wiki's copy in `docs/wiki/`.
2. **List what changed since the last release.** `git log --oneline v$(cat VERSION)..` (the last
   tag is `v` + the version in `VERSION`). For every new or changed command, option, output
   column or behaviour: update its page, and add a row to the *Docs* table in `CHANGELOG.md`.
3. **Independent review.** Someone who did not write the change reads the changed pages and
   diagrams as three readers: a **beginner** (never used a command line: can they install and run
   it?), an **8-year-old** (does the page say in plain words what it is and why?), and a **pro**
   (do the options, defaults and columns match the code?). Check that no page names real levels,
   maps, players or recordings: examples are synthetic, verification claims give the method and
   the tolerance only.
4. **Fix the findings.**
5. **Translate.** Each translated page records the hash of the English page it was made from.
   Re-translate the pages whose English source hash changed, and the diagram labels that changed;
   then review each language: clear for the three readers, diagram labels right, words matching
   the viewer's localised interface.
6. **Push only after the owner's go-ahead.** Then tag the release `v<VERSION>`.

New to running these commands? [Before you start](before-you-start) covers Python and the
terminal.
