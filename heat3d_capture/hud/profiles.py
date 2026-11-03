"""
Where a game draws its HUD, and what the pieces look like.

Every box is in pixels of a 1920x1080 reference screen and is scaled to the
recording's own size, so a 4K clip and a 1080p clip use the same profile. A
recording at another aspect ratio (ultrawide) would put the corners elsewhere;
that is not handled, and `video.probe` refuses it rather than reading the
wrong part of the screen.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .points import Layout as PopupLayout

#: The screen every profile's boxes are measured on.
REFERENCE = (1920, 1080)


@dataclass(frozen=True)
class Box:
    """A rectangle on the reference screen: left, top, width, height."""

    x: float
    y: float
    w: float
    h: float

    def on(self, width: int, height: int) -> tuple[int, int, int, int]:
        """The same rectangle on a `width` x `height` frame, on even pixels (the decoder's chroma grid)."""
        sx = width / REFERENCE[0]
        sy = height / REFERENCE[1]
        x = int(round(self.x * sx / 2)) * 2
        y = int(round(self.y * sy / 2)) * 2
        w = int(round(self.w * sx / 2)) * 2
        h = int(round(self.h * sy / 2)) * 2
        return x, y, max(2, min(w, width - x)), max(2, min(h, height - y))


@dataclass(frozen=True)
class Region:
    """A box cut out of every sampled frame, delivered at `scale` times its reference size."""

    name: str
    box: Box
    scale: float

    @property
    def size(self) -> tuple[int, int]:
        """Width and height of the delivered crop: even, since the decoder works on 2x2 chroma blocks."""
        return (int(round(self.box.w * self.scale / 2)) * 2, int(round(self.box.h * self.scale / 2)) * 2)


@dataclass(frozen=True)
class Profile:
    """One game's HUD."""

    name: str
    title: str
    regions: tuple[Region, ...]
    #: The player's point on the minimap, as fractions of the minimap's width and height.
    player: tuple[float, float]
    #: The key-hint square drawn in a corner of the minimap while the player is in play,
    #: as fractions of the minimap: left, top, width, height. Its presence is the test
    #: for "in play"; None when the game has none.
    map_key: tuple[float, float, float, float] | None
    #: The kill feed's rows: their pitch and the height of a name, in reference pixels,
    #: and the x the victim column is right-aligned to (None when it is not aligned).
    feed_pitch: float
    feed_text: float
    feed_right: float | None
    #: Compass bearings printed as letters.
    compass_letters: dict[str, float] = field(default_factory=lambda: {"N": 0.0, "E": 90.0, "S": 180.0, "W": 270.0})
    #: Where the compass strip's heading mark is, in reference x.
    compass_mark: float = 960.0
    #: The rows of the points popup (region "points"); None when the game has none.
    popup: PopupLayout | None = None

    def region(self, name: str) -> Region:
        for r in self.regions:
            if r.name == name:
                return r
        raise KeyError(name)


# Battlefield 6. Measured on the game's default HUD at 16:9: the minimap in the
# bottom left (player-centred, rotating with the view, the view cone always
# pointing up), the kill feed in the top right growing upwards from its newest
# row, the compass top centre - at the top of the screen on foot and in third
# person, lower down while looking through a vehicle's sight. The points popup
# sits left of and below the crosshair, its total starting at x 760 and its
# tags right-aligned to x 750, in every view (on foot, in a vehicle, through a
# sight). The down screen's words are under the centre; the killer card's
# DAMAGE LOG / PLAYER CARD line and the deploy screen's DEPLOY button share the
# bottom right.
BF6 = Profile(
    name="bf6",
    title="Battlefield 6",
    regions=(
        Region("minimap", Box(32, 752, 296, 296), 1.5),
        Region("feed", Box(1440, 14, 456, 192), 2.0),
        Region("compass", Box(620, 10, 680, 48), 1.5),
        Region("compass_sight", Box(620, 204, 680, 46), 1.5),
        Region("squad", Box(336, 820, 240, 230), 1.0),
        Region("points", Box(240, 624, 680, 172), 1.5),
        Region("down", Box(600, 786, 720, 104), 1.0),
        Region("card", Box(1580, 996, 250, 56), 1.5),
    ),
    player=(0.5, 0.497),
    map_key=(14 / 296, 269 / 296, 20 / 296, 22 / 296),
    feed_pitch=30.0,
    feed_text=14.0,
    feed_right=1884.0,
    popup=PopupLayout(),
)

PROFILES = {p.name: p for p in (BF6,)}
