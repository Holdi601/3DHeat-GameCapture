"""
Reading a game's HUD out of a recording of it, after the match.

Everything here works on a video file the player recorded of their own game
(ShadowPlay, Instant Replay, OBS): the kill feed as timed events, and the
player's own track from the minimap. Nothing touches the running game, its
memory or its network, and nothing is derived about anyone else's position -
only what the screen showed the player, read back afterwards. That is the same
information the player saw, so reading it from the video is not an advantage
over anyone, and it cannot be one, because the match is over by then.

A game is a profile (`profiles.py`): where its HUD elements sit on a
1920x1080 reference screen, and what they look like. The machinery - decoding,
registering a rotating minimap into a growing mosaic, reading a kill feed - is
shared, so a second game is a second profile rather than a second tool.

    python -m heat3d_capture hud recording.mp4 --game bf6 --player NAME -o out

See docs/hud-video.md.
"""
