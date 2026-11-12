"""Offline tests for Breakout's game logic."""

import unittest

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
