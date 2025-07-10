import random

from back.core import GameState
from . import Bot


# Do not forget to add your bot to __init__ file.
# Import it there and add to the bots list
class RandomBot():
    def __init__(self, cutoff):
        self.cutoff = cutoff
        self.__name__ = f'RandomBot{cutoff}'

    def __call__(self, player):
        return RandomBotThing(self.cutoff, player)

class RandomBotThing(Bot):
    def __init__(self, cutoff, player):
        super().__init__(player)
        self.cutoff = cutoff
    def get_action(self, state: GameState, time_delta: float) -> bool:
        return random.random() < self.cutoff