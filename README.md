# Breakout

A fullscreen Pygame version of Breakout with procedural brick layouts, multi-hit bricks, particle effects, level selection, and several power-ups that change how each round plays.

## Requirements

- Python 3
- Pygame

Install Pygame if it is not already available:

```bash
pip install pygame
```

## Running the Game

From this folder, run:

```bash
python3 breakout.py
```

The game opens in fullscreen at the primary monitor resolution detected by Pygame.

## Controls

| Action | Control |
| --- | --- |
| Move paddle left | Left arrow |
| Move paddle right | Right arrow |
| Launch ball | Space |
| Pause | `P` or `Esc` |
| Navigate menus | Up/down arrows or mouse |
| Select menu option | Enter or left mouse click |

## How It Works

The goal is to clear every brick on the screen by keeping the ball in play with the paddle. When the ball hits a brick, the brick either loses durability or breaks. Broken bricks add to the score and may drop a power-up. If every active ball falls below the screen, one life is lost and a new ball is attached to the paddle.

The game starts with three lives. Clearing all bricks advances to the next level, rebuilds the brick field, increases ball speed, and resets temporary paddle expansion effects.

## Menus

- **Title menu:** Start a new game, choose a starting level, or quit.
- **Level select:** Start from levels 1 through 4.
- **Pause menu:** Resume, restart the current level, return to level select, or quit.

When resuming from pause, the game shows a short countdown before play continues.

## Features

- **Procedural brick fields:** Each level generates a new brick layout using randomized noise.
- **Increasing difficulty:** Later levels create more rows, more durable bricks, and faster ball movement.
- **Multi-hit bricks:** Bricks can require one to four hits. Their color changes as durability drops.
- **Power-up bricks:** Flashing bricks indicate special effects or collectible drops.
- **Multiple balls:** Extra-ball power-ups add another active ball to the playfield.
- **Particle effects:** Wall hits, paddle hits, brick breaks, bombs, and slow-time effects produce visual feedback.
- **Fullscreen scaling:** Paddle, bricks, fonts, movement, and effects scale from the detected monitor size.

## Power-Ups

| Power-up | Color | Effect |
| --- | --- | --- |
| Slow time | Blue | Slows active balls and adds a screen distortion effect for about 10 seconds. |
| Extend platform | Purple | Widens the paddle for the next several ball hits. |
| Extra ball | Green | Adds another ball to the current level. |
| Extra life | Pink | Adds one life. |
| Bomb | Cyan | Explodes nearby regular bricks and creates a ripple effect. |

Power-up messages briefly float upward when collected or triggered.

## Scoring and Progression

- Breaking a brick awards 10 points.
- Bomb bricks also award points when triggered.
- The level number increases automatically after all bricks are cleared.
- Ball speed scales upward as levels increase.
