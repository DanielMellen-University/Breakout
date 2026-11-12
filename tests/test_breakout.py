"""Offline tests for Breakout's game logic."""

import unittest
from unittest import mock

import pygame

import breakout


class BreakoutTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def make_game(self, level=1, width=800, height=600):
        screen = pygame.Surface((width, height))
        return breakout.Game(screen, width, height, level)


class TestTestFixtures(BreakoutTestCase):
    def test_game_uses_supplied_dummy_surface(self):
        game = self.make_game()
        self.assertEqual(game.screen.get_size(), (800, 600))
        self.assertTrue(game.balls[0].attached)


if __name__ == "__main__":
    unittest.main()


class TestBrickDurability(BreakoutTestCase):
    def test_hits_change_color_then_break_brick(self):
        brick = breakout.Brick(10, 20, 40, 12, 3, power_up_type=None)
        brick.power_up_type = None
        brick.hits = 3
        brick.max_hits = 3
        brick.color = brick.get_color()

        self.assertEqual(brick.color, breakout.LIGHT_ORANGE)
        brick.hit()
        self.assertEqual(brick.hits, 2)
        self.assertEqual(brick.color, breakout.DARK_ORANGE)
        self.assertFalse(brick.broken)
        brick.hit()
        self.assertEqual(brick.color, breakout.RED)
        brick.hit()
        self.assertTrue(brick.broken)
        self.assertEqual(brick.hits, 0)


class TestPowerUpBrick(BreakoutTestCase):
    def test_power_up_brick_is_single_hit_and_uses_special_color(self):
        brick = breakout.Brick(10, 20, 40, 12, 4, power_up_type="extra_life")

        self.assertEqual(brick.hits, 1)
        self.assertEqual(brick.max_hits, 1)
        self.assertIsNone(brick.color)
        brick.hit()
        self.assertTrue(brick.broken)


class TestBrickHitDistribution(BreakoutTestCase):
    def test_difficulty_tiers_assign_expected_durability(self):
        cases = ((1, 0.84, 2), (2, 0.69, 2), (3, 0.79, 3), (4, 0.69, 3))
        for level, roll, expected_hits in cases:
            with self.subTest(level=level):
                game = self.make_game(level)
                with mock.patch.object(breakout.random, "uniform", return_value=0.75), \
                        mock.patch.object(breakout.random, "random", return_value=roll), \
                        mock.patch.object(breakout.random, "randint", return_value=2):
                    bricks = game.create_bricks()
                self.assertTrue(bricks)
                self.assertTrue(all(brick.hits == expected_hits for brick in bricks))


class TestBrickRowCaps(BreakoutTestCase):
    def test_rows_increase_by_two_until_capped_at_twenty_five(self):
        for level, expected_rows in ((1, 17), (2, 19), (4, 23), (5, 25), (12, 25)):
            with self.subTest(level=level):
                game = self.make_game(level)
                with mock.patch.object(breakout.random, "uniform", return_value=0.75):
                    bricks = game.create_bricks()
                occupied_rows = {round((brick.y - game.top_margin) / (game.brick_height + game.gap))
                                 for brick in bricks}
                self.assertEqual(len(occupied_rows), expected_rows)
