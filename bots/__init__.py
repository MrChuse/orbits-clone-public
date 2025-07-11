from .bot_base import Bot
from .do_nothing_bot import DoNothingBot
from .random_bot import RandomBot

from back.core import PlayerSphere

bots = [DoNothingBot, RandomBot(0.15)]


# bots check
from pygame import Vector2
for bot in bots:
    try:
        # each bot must override the get_action function
        # and have its __init__ method have 4 args: center, velocity, radius, color
        # and have a __name__ attribute to show in the dropdown menu
        p = PlayerSphere(Vector2(0, 0), Vector2(1, 0), 10, (255, 255, 255))
        b = bot(p)
        bot.__name__
    except AttributeError as e:
        print(f'Bot {bot} has a problem: {e!r}')
        exit()
    except Exception as e:
        print(f'Bot {bot.__name__} has a problem: {e!r}')
        exit()
