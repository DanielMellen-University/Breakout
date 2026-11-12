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
        with mock.patch.object(breakout.random, "uniform", return_value=math.pi / 4):
            ball.launch()

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


class TestBrickCollision(BreakoutTestCase):
    def test_side_impact_returns_brick_and_reverses_horizontal_motion(self):
        game = self.make_game()
        brick = breakout.Brick(100, 100, 50, 20, 2)
        brick.power_up_type = None
        brick.hits = 2
        brick.max_hits = 2
        brick.color = brick.get_color()
        ball = breakout.Ball(game.paddle, 5, 6, 800, 600, x=95, y=110)
        ball.dx, ball.dy = 5, 0

        hit_bricks, particles = ball.check_collision(game.paddle, [brick], game)

        self.assertEqual(hit_bricks, [brick])
        self.assertEqual(len(particles), 8)
        self.assertLess(ball.dx, 0)
        self.assertEqual(brick.hits, 2)


class TestBrickScoring(BreakoutTestCase):
    def test_surviving_hit_scores_nothing_and_final_hit_scores_ten(self):
        game = self.make_game()
        brick = breakout.Brick(100, 100, 50, 20, 2)
        brick.power_up_type = None
        brick.hits = 2
        brick.max_hits = 2
        brick.color = brick.get_color()
        game.bricks = [brick]
        ball = breakout.Ball(game.paddle, 5, 6, 800, 600, x=95, y=110)
        ball.dx, ball.dy = 5, 0
        game.balls = [ball]

        with mock.patch.object(breakout.random, "random", return_value=0.5):
            game.update()
            self.assertEqual(brick.hits, 1)
            self.assertEqual(game.score, 0)
            game.update()

        self.assertTrue(brick.broken)
        self.assertEqual(game.score, 10)


class TestLifeLoss(BreakoutTestCase):
    def test_last_lost_ball_costs_life_and_creates_attached_replacement(self):
        game = self.make_game()
        lost_ball = breakout.Ball(game.paddle, 5, game.ball_radius, 800, 600,
                                  x=400, y=601)
        lost_ball.dx, lost_ball.dy = 0, 1
        game.balls = [lost_ball]

        game.update()

        self.assertEqual(game.lives, 2)
        self.assertEqual(len(game.balls), 1)
        self.assertIsNot(game.balls[0], lost_ball)
        self.assertTrue(game.balls[0].attached)


class TestLastLifeBall(BreakoutTestCase):
    def test_zero_lives_still_gets_one_ball_then_game_over(self):
        game = self.make_game()
        game.lives = 1
        first = breakout.Ball(game.paddle, 5, game.ball_radius, 800, 600,
                              x=400, y=601)
        first.dy = 1
        game.balls = [first]

        game.update()
        self.assertEqual(game.lives, 0)
        self.assertTrue(game.running)
        self.assertTrue(game.balls[0].attached)

        last = game.balls[0]
        last.attached = False
        last.x, last.y, last.dx, last.dy = 400, 601, 0, 1
        game.update()
        self.assertFalse(game.running)
        self.assertEqual(game.balls, [])


class TestLevelProgression(BreakoutTestCase):
    def test_clearing_field_advances_speed_and_resets_paddle(self):
        game = self.make_game(level=2)
        cleared_brick = breakout.Brick(10, 20, 40, 12, 1)
        cleared_brick.broken = True
        game.bricks = [cleared_brick]
        game.paddle.width = game.paddle.increased_width
        game.paddle.is_expanded = True
        game.paddle.expand_hits = 3
        old_ball = game.balls[0]

        with mock.patch.object(game, "create_bricks", return_value=[]):
            game.update()

        self.assertEqual(game.level, 3)
        self.assertAlmostEqual(game.speed_multiplier, 1.5 * (1.05 ** 2))
        self.assertEqual(len(game.balls), 1)
        self.assertIsNot(game.balls[0], old_ball)
        self.assertAlmostEqual(game.balls[0].speed, game.base_speed * game.speed_multiplier)
        self.assertTrue(game.balls[0].attached)
        self.assertEqual(game.paddle.width, game.paddle.default_width)
        self.assertFalse(game.paddle.is_expanded)
        self.assertEqual(game.paddle.expand_hits, 0)


class TestSlowTimePowerUp(BreakoutTestCase):
    def test_slow_time_halves_speed_extends_and_restores(self):
        game = self.make_game()
        ball = game.balls[0]
        ball.attached = False
        ball.dx, ball.dy = 6, 8
        original_speed = ball.speed = math.hypot(ball.dx, ball.dy)
        pickup = breakout.PowerUp(10, 20, "slow_time", game.screen_height)

        pickup.apply_effect(game.paddle, game.balls, game)
        self.assertAlmostEqual(ball.speed, original_speed / 2)
        self.assertEqual(ball.slow_timer, 600)
        self.assertEqual(game.slow_time_active, 600)
        self.assertAlmostEqual(math.hypot(ball.dx, ball.dy), ball.speed)

        pickup.apply_effect(game.paddle, game.balls, game)
        self.assertAlmostEqual(ball.speed, original_speed / 2)
        self.assertEqual(ball.slow_timer, 1200)
        ball.slow_timer = 1
        ball.update()
        self.assertEqual(ball.slow_timer, 0)
        self.assertEqual(ball.speed, ball.default_speed)
        self.assertAlmostEqual(math.hypot(ball.dx, ball.dy), ball.default_speed)


class TestExtraBallDuringSlowTime(BreakoutTestCase):
    def test_extra_ball_matches_existing_slowed_speed(self):
        game = self.make_game()
        original = game.balls[0]
        original.attached = False
        original.dx, original.dy = original.speed, 0
        breakout.PowerUp(0, 0, "slow_time", game.screen_height).apply_effect(
            game.paddle, game.balls, game)
        slowed_speed = original.speed

        with mock.patch.object(breakout.random, "uniform", side_effect=(game.margin, math.pi / 2)):
            breakout.PowerUp(0, 0, "extra_ball", game.screen_height).apply_effect(
                game.paddle, game.balls, game)

        new_ball = game.balls[1]
        self.assertEqual(new_ball.slow_timer, original.slow_timer)
        self.assertAlmostEqual(new_ball.speed, slowed_speed)
        self.assertAlmostEqual(math.hypot(new_ball.dx, new_ball.dy), slowed_speed)
        new_ball.slow_timer = 1
        new_ball.update()
        self.assertEqual(new_ball.speed, original.default_speed)
        self.assertAlmostEqual(math.hypot(new_ball.dx, new_ball.dy), original.default_speed)


class TestExtraBallPowerUp(BreakoutTestCase):
    def test_extra_ball_enters_from_top_moving_downward(self):
        game = self.make_game()
        with mock.patch.object(breakout.random, "uniform", side_effect=(game.margin, math.pi / 2)):
            breakout.PowerUp(0, 0, "extra_ball", game.screen_height).apply_effect(
                game.paddle, game.balls, game)

        new_ball = game.balls[-1]
        self.assertEqual(new_ball.x, game.margin)
        self.assertEqual(new_ball.y, game.top_margin)
        self.assertAlmostEqual(new_ball.dx, 0)
        self.assertGreater(new_ball.dy, 0)
        self.assertAlmostEqual(math.hypot(new_ball.dx, new_ball.dy), new_ball.speed)


class TestExtraLifePowerUp(BreakoutTestCase):
    def test_extra_life_adds_life_and_feedback_message(self):
        game = self.make_game()
        starting_lives = game.lives
        breakout.PowerUp(30, 40, "extra_life", game.screen_height).apply_effect(
            game.paddle, game.balls, game)

        self.assertEqual(game.lives, starting_lives + 1)
        self.assertEqual(len(game.power_up_messages), 1)
        self.assertEqual(game.power_up_messages[0].text, "+life")


class TestExtendPaddlePowerUp(BreakoutTestCase):
    def test_pickups_stack_hits_without_widening_twice(self):
        game = self.make_game()
        pickup = breakout.PowerUp(10, 20, "extend_platform", game.screen_height)
        default_width = game.paddle.width
        pickup.apply_effect(game.paddle, game.balls, game)
        expanded_width = game.paddle.width
        pickup.apply_effect(game.paddle, game.balls, game)

        self.assertTrue(game.paddle.is_expanded)
        self.assertEqual(expanded_width, default_width * 1.5)
        self.assertEqual(game.paddle.width, expanded_width)
        self.assertEqual(game.paddle.expand_hits, 10)


class TestFallingPowerUp(BreakoutTestCase):
    def test_pickup_falls_and_is_removed_below_screen(self):
        game = self.make_game()
        pickup = breakout.PowerUp(10, 20, "extra_life", game.screen_height)
        original_y = pickup.y
        pickup.move()
        self.assertEqual(pickup.y, original_y + pickup.velocity)

        pickup.y = game.screen_height + 1
        game.power_ups = [pickup]
        game.update()
        self.assertEqual(game.power_ups, [])


class TestPowerUpCollection(BreakoutTestCase):
    def test_paddle_collects_pickup_and_removes_it(self):
        game = self.make_game()
        pickup = breakout.PowerUp(game.paddle.x, game.paddle.y - 1,
                                  "extra_life", game.screen_height)
        game.power_ups = [pickup]
        original_lives = game.lives

        game.update()

        self.assertEqual(game.lives, original_lives + 1)
        self.assertEqual(game.power_ups, [])
        self.assertEqual(game.power_up_messages[-1].text, "+life")


class TestBombActivation(BreakoutTestCase):
    def test_bomb_contact_scores_and_creates_ripple_and_message(self):
        game = self.make_game()
        bomb = breakout.Brick(100, 100, 50, 20, 1, power_up_type="bomb")
        remote = breakout.Brick(600, 400, 50, 20, 1, power_up_type="extra_life")
        game.bricks = [bomb, remote]
        ball = breakout.Ball(game.paddle, 5, 6, 800, 600, x=95, y=110)
        ball.dx = 5
        game.balls = [ball]

        game.update()

        self.assertTrue(bomb.broken)
        self.assertEqual(game.score, 10)
        self.assertEqual(len(game.time_ripples), 1)
        self.assertEqual(game.power_up_messages[-1].text, "+bomb")


class TestBombBlast(BreakoutTestCase):
    def test_blast_breaks_regular_neighbors_without_blast_score(self):
        game = self.make_game()
        bomb = breakout.Brick(100, 100, 50, 20, 1, power_up_type="bomb")
        neighbor = breakout.Brick(160, 100, 50, 20, 2)
        neighbor.power_up_type = None
        neighbor.hits = 2
        neighbor.max_hits = 2
        remote = breakout.Brick(600, 400, 50, 20, 1, power_up_type="extra_life")
        game.bricks = [bomb, neighbor, remote]
        ball = breakout.Ball(game.paddle, 5, 6, 800, 600, x=95, y=110)
        ball.dx = 5
        game.balls = [ball]

        game.update()

        self.assertTrue(neighbor.broken)
        self.assertFalse(remote.broken)
        self.assertEqual(game.score, 10)


class TestBombPowerUpProtection(BreakoutTestCase):
    def test_blast_leaves_neighboring_power_up_brick_intact(self):
        game = self.make_game()
        bomb = breakout.Brick(100, 100, 50, 20, 1, power_up_type="bomb")
        protected = breakout.Brick(160, 100, 50, 20, 1, power_up_type="extra_life")
        game.bricks = [bomb, protected]
        ball = breakout.Ball(game.paddle, 5, 6, 800, 600, x=95, y=110)
        ball.dx = 5
        game.balls = [ball]

        game.update()

        self.assertTrue(bomb.broken)
        self.assertFalse(protected.broken)
        self.assertEqual(protected.hits, 1)


class TestPauseResume(BreakoutTestCase):
    def test_resume_shows_three_countdown_ticks_then_unpauses(self):
        game = self.make_game()
        game.paused = True

        def stop_after_resume():
            game.running = False

        with mock.patch.object(breakout.PauseMenu, "run", return_value="resume"), \
                mock.patch.object(game, "draw"), \
                mock.patch.object(game, "handle_events", side_effect=stop_after_resume), \
                mock.patch.object(game, "update"), \
                mock.patch.object(pygame.display, "flip"), \
                mock.patch.object(pygame.time, "wait") as wait:
            result = game.run()

        self.assertIsNone(result)
        self.assertFalse(game.paused)
        self.assertEqual([call.args[0] for call in wait.call_args_list], [1000, 1000, 1000])
