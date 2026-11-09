"""Record real gameplay frames headlessly for the README.

Runs the actual Game class from breakout.py with SDL's dummy video driver
and a simple autopilot that moves the paddle with the same Paddle.move()
the arrow keys use. Frames are saved as PNGs and can be turned into a GIF
with ffmpeg (see docs/media/README.md).

    SDL_VIDEODRIVER=dummy python tools/capture_demo.py --out /tmp/frames
"""

import argparse
import os
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame  # noqa: E402

import breakout  # noqa: E402


class SeededRandom(random.Random):
    """A Random whose seed(None) calls are ignored.

    Game.create_bricks() calls random.seed(None) on every level, which would
    make a seeded capture unrepeatable. Swapping this in as breakout.random
    keeps the game code untouched while making --seed cover the brick
    layout, drops and bounces.
    """

    def seed(self, a=None, version=2):
        if a is not None or not hasattr(self, "_seeded"):
            self._seeded = True
            super().seed(a, version)


def pick_target(game):
    """Return the x the paddle should center on this frame."""
    paddle = game.paddle
    falling = [b for b in game.balls if not b.attached and b.dy > 0]
    if falling:
        ball = max(falling, key=lambda b: b.y)
        # Hit slightly off center so the bounce angle varies.
        return ball.x + paddle.width * 0.15 * (1 if ball.dx < 0 else -1)
    if game.power_ups:
        return max(game.power_ups, key=lambda p: p.y).x
    return game.screen_width / 2


def drive(game):
    for ball in game.balls:
        if ball.attached:
            ball.launch()
    center = game.paddle.x + game.paddle.width / 2
    target = pick_target(game)
    if abs(target - center) > game.paddle.velocity:
        game.paddle.move("left" if target < center else "right", game.screen_width)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, help="directory for frame PNGs")
    parser.add_argument("--size", default="1280x720", help="window size WxH")
    parser.add_argument("--level", type=int, default=2, help="starting level")
    parser.add_argument("--warmup", type=int, default=0, help="frames to simulate before saving")
    parser.add_argument("--frames", type=int, default=600, help="frames to simulate while saving")
    parser.add_argument("--every", type=int, default=2, help="save every Nth frame")
    parser.add_argument("--seed", type=int, default=None, help="seed for the autopilot run")
    parser.add_argument("--snap", type=int, action="append", default=[],
                        help="also save this frame number as snap-N.png (repeatable)")
    args = parser.parse_args()

    width, height = (int(v) for v in args.size.lower().split("x"))
    os.makedirs(args.out, exist_ok=True)

    screen = pygame.display.set_mode((width, height))
    if args.seed is not None:
        breakout.random = SeededRandom(args.seed)
    game = breakout.Game(screen, width, height, args.level)

    saved = 0
    for frame in range(args.warmup + args.frames):
        pygame.event.pump()
        drive(game)
        game.update()
        game.draw()
        if not game.running:
            break
        if frame >= args.warmup and (frame - args.warmup) % args.every == 0:
            pygame.image.save(screen, os.path.join(args.out, f"frame-{saved:04d}.png"))
            saved += 1
        if frame in args.snap:
            pygame.image.save(screen, os.path.join(args.out, f"snap-{frame}.png"))

    print(f"saved {saved} frames to {args.out}; level {game.level}, score {game.score}, "
          f"lives {game.lives}, balls {len(game.balls)}")
    pygame.quit()


if __name__ == "__main__":
    main()
