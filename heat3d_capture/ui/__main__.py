"""
`python -m heat3d_capture.ui` — the scan window.

Everything here runs *before* the application imports anything heavy, which is
the point: the dependency check cannot live inside a module that already needs
numpy to be importable in order to be read.
"""

import sys
from pathlib import Path

# A newer release of the tool: said, and offered, before the window opens (see
# heat3d_update in the repository's root).
_root = str(Path(__file__).resolve().parents[2])
if _root not in sys.path:
    sys.path.append(_root)
try:
    import heat3d_update

    heat3d_update.startup("heat3d_capture.ui")
except ImportError:
    pass

from ..runtime.preflight import SCANNER, ensure_graphical  # noqa: E402

if not ensure_graphical(SCANNER):
    raise SystemExit(
        "The scanner needs those packages to run. Nothing was installed and "
        "nothing was changed."
    )

from .app import main  # noqa: E402  - deliberately after the check

raise SystemExit(main())
