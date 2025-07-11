from abc import ABC, abstractmethod

import pygame

from back.core import GameState, PlayerSphere

class Bot(ABC):
    @abstractmethod
    def get_action(self, state: GameState, time_delta: float) -> bool:
        return False

    def __init__(self, player_sphere: PlayerSphere):
        self.player_sphere = player_sphere

    # methods from player_sphere that can be called by the bots
    def is_dodging(self):
        return self.player_sphere.is_dodging()
    def is_dodge_cooldown(self):
        return self.player_sphere.is_dodge_cooldown()
    def can_dodge(self):
        return self.player_sphere.can_dodge()

    def is_in_rotator(self, rotators):
        return self.player_sphere.is_in_rotator(rotators)
    
    def draw_debug(self, debug_surface: pygame.Surface):
        self.player_sphere.draw_debug(debug_surface)
