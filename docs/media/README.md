# Media

`gameplay.gif` is 10 seconds of real gameplay recorded headlessly from the
actual `Game` class. Nothing is drawn by hand. The paddle is driven by a
small autopilot in `tools/capture_demo.py` that calls the same
`Paddle.move()` the arrow keys use.

To regenerate it:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
SDL_VIDEODRIVER=dummy .venv/bin/python tools/capture_demo.py \
    --out /tmp/breakout-frames --seed 6 --level 2 --warmup 1600 --frames 600 --every 2
ffmpeg -framerate 30 -i /tmp/breakout-frames/frame-%04d.png \
    -vf "scale=720:-1:flags=neighbor,split[a][b];[a]palettegen=max_colors=32:stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle" \
    docs/media/gameplay.gif
```

`--seed` makes the brick layout, drops, and bounces repeatable, so seed 6
gives the same run (level 2, two extra-ball pickups and several bombs) every
time. The window is 1280x720.
