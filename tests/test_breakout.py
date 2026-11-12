"""Offline tests for Breakout's game logic."""

import unittest
import math
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


class TestBrickLayoutBounds(BreakoutTestCase):
    def test_generated_bricks_fit_column_slots_inside_margins(self):
        game = self.make_game()
        with mock.patch.object(breakout.random, "uniform", return_value=0.75):
            bricks = game.create_bricks()

        self.assertTrue(bricks)
        for brick in bricks:
            self.assertGreaterEqual(brick.x, game.margin)
            self.assertLessEqual(brick.x + brick.width, game.screen_width - game.margin + 1e-9)
            column = round((brick.x - game.margin) / (game.brick_width + game.gap))
            self.assertGreaterEqual(column, 0)
            self.assertLess(column, game.brick_columns)


class TestPaddleMovement(BreakoutTestCase):
    def test_paddle_stays_within_left_and_right_edges(self):
        paddle = breakout.Paddle(550, 100, 12, 800)
        paddle.x = 0
        paddle.move("left", 800)
        self.assertEqual(paddle.x, 0)
        paddle.x = 700
        paddle.move("right", 800)
        self.assertEqual(paddle.x, 700)


class TestBallLaunch(BreakoutTestCase):
    def test_launch_uses_forty_five_degree_limit_and_preserves_speed(self):
        paddle = breakout.Paddle(550, 100, 12, 800)
        ball = breakout.Ball(paddle, 8, 6, 800, 600)
        with mock.patch.object(breakout.random, "uniform", return_value=math.pi / 4) as uniform:
            ball.launch()

        uniform.assert_called_once_with(-math.pi / 4, math.pi / 4)
        angle = math.atan2(ball.dx, -ball.dy)
        self.assertFalse(ball.attached)
        self.assertAlmostEqual(angle, math.pi / 4)
        self.assertLessEqual(abs(angle), math.pi / 4)
        self.assertAlmostEqual(math.hypot(ball.dx, ball.dy), ball.speed)


class TestWallCollision(BreakoutTestCase):
    def test_left_wall_corrects_position_and_reverses_horizontal_motion(self):
        game = self.make_game()
        ball = breakout.Ball(game.paddle, 5, 6, 800, 600, x=1, y=300)
        ball.dx, ball.dy = -3, -4
        with mock.patch.object(breakout.random, "uniform", return_value=0):
            ball.check_collision(game.paddle, [], game)

        self.assertEqual(ball.x, ball.radius)
        self.assertGreater(ball.dx, 0)
        self.assertAlmostEqual(math.hypot(ball.dx, ball.dy), ball.speed)


class TestTopWallCollision(BreakoutTestCase):
    def test_top_wall_corrects_position_and_reverses_vertical_motion(self):
        game = self.make_game()
        ball = breakout.Ball(game.paddle, 5, 6, 800, 600, x=300, y=1)
        ball.dx, ball.dy = 3, -4
        with mock.patch.object(breakout.random, "uniform", return_value=0):
            ball.check_collision(game.paddle, [], game)

        self.assertEqual(ball.y, ball.radius)
        self.assertGreater(ball.dy, 0)
        self.assertAlmostEqual(math.hypot(ball.dx, ball.dy), ball.speed)


class TestPaddleBounce(BreakoutTestCase):
    def test_aim_ranges_from_center_to_forty_five_degrees(self):
        game = self.make_game()
        paddle = game.paddle
        cases = ((paddle.x + paddle.width / 2, 0), (paddle.x, -math.pi / 4))
        for x, expected_angle in cases:
            ball = breakout.Ball(paddle, 8, game.ball_radius, 800, 600,
                                 x=x, y=paddle.y + 1)
            ball.dx, ball.dy = 0, 8
            ball.check_collision(paddle, [], game)
            self.assertAlmostEqual(math.atan2(ball.dx, -ball.dy), expected_angle)
            self.assertLessEqual(abs(math.atan2(ball.dx, -ball.dy)), math.pi / 4)

    def test_expansion_expires_after_configured_paddle_hits(self):
        game = self.make_game()
        paddle = game.paddle
        paddle.width = paddle.increased_width
        paddle.is_expanded = True
        paddle.expand_hits = 1
        ball = breakout.Ball(paddle, 8, game.ball_radius, 800, 600,
                             x=paddle.x + paddle.width / 2, y=paddle.y + 1)

        ball.check_collision(paddle, [], game)

        self.assertEqual(paddle.expand_hits, 0)
        self.assertFalse(paddle.is_expanded)
        self.assertEqual(paddle.width, paddle.default_width)
