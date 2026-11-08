"""
What locating needs to know about a game: how high the eye is, how wide the
view, how fast a player moves, and which parts of the screen are not the
level.

The heights and speeds are in metres and are turned into the level's units
with the level's `unit_metres`, so one profile serves a level in metres and
one in inches alike. The HUD boxes are pixels of a 1920x1080 reference
screen, as in hud/profiles.py, scaled to the recording.

Everything here can be overridden on the command line (`--eye`, `--fov`,
`--mask`), and should be where a player changed the game's defaults: the
field of view above all, since a frame solved with the wrong one is solved
with the wrong focal length, and its position comes out wrong along the view.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace

import numpy as np

from .camera import hfov_from_vertical

REFERENCE = (1920, 1080)


@dataclass(frozen=True)
class GameProfile:
    name: str
    title: str
    #: Eye heights above the floor the database is rendered at (metres): standing first.
    eye_heights: tuple[float, ...]
    #: Horizontal field of view of a 16:9 frame, degrees.
    hfov: float
    #: The fastest a player moves on foot (metres a second): a located position
    #: further from its neighbours than this allows is an outlier.
    max_speed: float
    #: Screen boxes that are not the level: (x, y, w, h) on the reference screen.
    hud: tuple[tuple[int, int, int, int], ...] = ()
    #: Half the side of the square kept out round the screen's centre (the crosshair), reference pixels.
    crosshair: int = 24
    #: The lowest the eye gets above the floor (metres): prone, sliding. None: a little under the lowest eye height.
    lowest_eye: float | None = None
    #: How to tell on foot, vehicle and zoomed views apart (views.py); None: every frame is on foot.
    views: str | None = None
    #: Horizontal field of view of the vehicle cameras, 16:9; None: the same as on foot.
    vehicle_hfov: float | None = None
    #: Screen boxes the vehicle itself covers in its third-person view (reference pixels).
    vehicle_hud: tuple[tuple[int, int, int, int], ...] = ()
    #: The highest a vehicle's camera rides above the floor (metres).
    vehicle_height: float = 8.0
    #: The fastest a vehicle moves (metres a second), for the outlier vote.
    vehicle_speed: float = 30.0
    #: How high a vehicle's third-person camera rides over the ground (metres): the height the
    #: database's vehicle views are rendered at. None: no vehicle views.
    vehicle_camera: float | None = None
    #: Where the vehicle is seen from its third-person camera: (ahead, down) in metres, along the
    #: camera's horizontal view direction and straight down to the ground under its middle. The camera's solved position plus
    #: this is the vehicle's (track.py); `vehicle_offset_measured` says whether it was measured.
    vehicle_offset: tuple[float, float] = (0.0, 0.0)
    vehicle_offset_measured: bool = False
    #: The reprojection error (pixels at 960 wide) a right fix shows on this game's frames: about 1
    #: against renders, 2-3 against real frames, whose light and detail never quite match the level's.
    pixel_noise: float = 1.5
    #: The fastest each class of vehicle moves (metres a second): the step a position may take
    #: between frames where the screen shows no speed. Classes: "ground", "boat", "heli", "jet".
    class_speeds: tuple[tuple[str, float], ...] = ()
    #: Where the vehicle's own speed readout is, when the HUD shows one (reference pixels), and its
    #: unit's metres a second.
    speed_box: tuple[int, int, int, int] | None = None
    speed_unit: float = 1.0 / 3.6
    #: Where the deploy screen draws the whole map (x, y, w, h on 1920x1080), for `locate refmap`.
    deploy_map: tuple[int, int, int, int] | None = None
    notes: str = ""

    def with_overrides(self, **kwargs) -> "GameProfile":
        return replace(self, **{k: v for k, v in kwargs.items() if v is not None})

    def mask(self, width: int, height: int, view: str = "foot") -> np.ndarray:
        """True where a frame of this size shows the level; in a vehicle's view the vehicle is masked too."""
        keep = np.ones((height, width), bool)
        sx, sy = width / REFERENCE[0], height / REFERENCE[1]
        boxes = tuple(self.hud) + (tuple(self.vehicle_hud) if view == "vehicle" else ())
        for x, y, w, h in boxes:
            keep[int(y * sy) : int((y + h) * sy) + 1, int(x * sx) : int((x + w) * sx) + 1] = False
        if self.crosshair:
            cx, cy, r = width // 2, height // 2, int(self.crosshair * sx) + 1
            keep[cy - r : cy + r, cx - r : cx + r] = False
        return keep


PROFILES: dict[str, GameProfile] = {
    "bf6": GameProfile(
        name="bf6",
        title="Battlefield 6",
        # Standing and crouched. Not measured in the game yet: a first-person
        # camera of a 1.8 m soldier, as Frostbite has placed it before.
        eye_heights=(1.6, 1.05),
        # Prone.
        lowest_eye=0.3,
        # The game's FOV slider is vertical; 55 degrees vertical is about 86
        # horizontal at 16:9. Pass the player's own with --vfov or --fov.
        hfov=round(hfov_from_vertical(55.0, 16 / 9), 2),
        # On foot: the calibrated minimap's speed over 2 s on five clips: 90th percentile 7.2 m/s,
        # fastest 10.
        max_speed=11.0,
        views="bf6",
        # The game's vehicle field of view is its own slider, vertical too;
        # 53 degrees is about 83 horizontal. Read the player's own from their
        # settings file (`settings_fov`).
        vehicle_hfov=round(hfov_from_vertical(53.0, 16 / 9), 2),
        # The vehicle in its third-person view: the lower middle of the screen.
        vehicle_hud=((440, 420, 1040, 660),),
        vehicle_height=8.0,
        # Measured on the calibrated minimap. Ground vehicles: tanks showed at most 10.8 m/s on their
        # own readout (which agreed with the minimap to 0.4 m/s, median), a light vehicle 21 m/s. A
        # helicopter (one stretch, about 100 s): 27 m/s typically, 48 at most; no jet or boat flown
        # yet, so theirs stay guesses. A stretch over a ground vehicle's limit is flagged by the
        # track, not trusted, unless the minimap says it was an aircraft (it zooms out to about
        # 1.2 m a pixel, 0.68 on the ground: `AIR_ZOOM`).
        vehicle_speed=22.0,
        class_speeds=(("ground", 22.0), ("boat", 20.0), ("heli", 60.0), ("jet", 280.0)),
        # "<n> KPH" in a tank's own (first-person) view, right of the sight; the third-person view
        # shows no speed.
        speed_box=(1330, 380, 190, 50),
        # The deploy screen's map at its default zoom, left of the squad and loadout panels.
        deploy_map=(165, 210, 1365, 680),
        speed_unit=1.0 / 3.6,
        vehicle_camera=3.5,
        # The ground under a main battle tank's middle, from its chase camera: measured by eye on
        # eleven right fixes of real frames (the tank's middle marked on the frame, the ground there
        # read from the level rendered at the fix): 7.9-11.7 m ahead, median 9.6; 3.3-4.8 m down,
        # median 3.7. One vehicle type; others ride their camera differently.
        vehicle_offset=(9.6, 3.7),
        vehicle_offset_measured=True,
        # Right fixes of real frames (pseudo-labelled, a handful) showed 2-3 pixels. Provisional.
        pixel_noise=3.0,
        hud=(
            (24, 744, 560, 312),  # minimap and squad list, bottom left
            (1430, 8, 480, 210),  # kill feed, top right
            (600, 0, 720, 130),  # compass, score bar and objective flags, top centre
            (620, 200, 680, 90),  # the sight's compass (vehicles, scopes)
            (20, 160, 440, 270),  # chat, top left
            (1500, 900, 420, 180),  # ammunition and gadgets, bottom right
            (1040, 620, 880, 460),  # the player's own weapon, lower right
            (700, 920, 520, 160),  # prompts and points pop-ups, bottom centre
        ),
        notes="HUD boxes after the hud verb's Battlefield 6 profile, checked on 4K recordings with the default HUD layout.",
    ),
    "generic": GameProfile(
        name="generic",
        title="any first-person game (pass --eye, --fov and --mask)",
        eye_heights=(1.65, 1.1),
        hfov=90.0,
        max_speed=8.0,
        hud=(),
    ),
}


def profile(name: str) -> GameProfile:
    try:
        return PROFILES[name]
    except KeyError:
        raise ValueError(f"no game profile {name!r}; there are: {', '.join(PROFILES)}") from None


def settings_fov(path: str | None = None) -> dict[str, float]:
    """
    The player's own Battlefield 6 field of view, read (never written) from
    the game's settings file: `GstRender.FieldOfViewVertical` and
    `GstRender.FieldOfViewVerticalVehicle`, vertical degrees. Without a path,
    the newest `PROFSAVE*_profile` under Documents/Battlefield 6/settings.
    Empty when there is none.

    The file holds the settings as they are now, not as they were when an
    older recording was made.
    """
    from pathlib import Path

    if path is None:
        base = Path.home() / "Documents" / "Battlefield 6" / "settings"
        found = sorted(base.rglob("PROFSAVE*_profile"), key=lambda f: f.stat().st_mtime, reverse=True) if base.is_dir() else []
        if not found:
            return {}
        path = str(found[0])
    out: dict[str, float] = {"file": path}  # type: ignore[dict-item]
    text = Path(path).read_bytes().decode("latin-1")
    for key, name in (("GstRender.FieldOfViewVertical ", "vfov"), ("GstRender.FieldOfViewVerticalVehicle ", "vehicle_vfov")):
        m = re.search(re.escape(key) + r"([0-9.]+)", text)
        if m:
            out[name] = float(m.group(1))
    return out


def parse_box(text: str) -> tuple[int, int, int, int]:
    """`x,y,w,h` on the 1920x1080 reference screen."""
    parts = [int(round(float(p))) for p in text.replace(" ", "").split(",")]
    if len(parts) != 4 or parts[2] <= 0 or parts[3] <= 0:
        raise ValueError(f"a mask box is x,y,w,h on a 1920x1080 screen, not {text!r}")
    return parts[0], parts[1], parts[2], parts[3]
