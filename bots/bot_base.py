from abc import ABC, abstractmethod

import pygame

from back.core import GameState, PlayerSphere

class Bot(ABC):
    def __init__(self, player_sphere: PlayerSphere):
        self.player_sphere = player_sphere

    @abstractmethod
    def get_action(self, state: GameState, time_delta: float) -> bool:
        return False

    def draw_debug(self, debug_surface: pygame.Surface):
        return