# orbits-clone-public
Public version of 12 orbits clone.

## The game
![Gameplay](/media/gameplay.gif)

#### The rules
- You control a snake which flies around the field
- Your goal is to be the last snake standing
- You collect white spheres to grow your tail
- When you hit your opponents' tail, you lose
- There are rotators on the field (these gray circles)
- When you press your action button while inside the rotator, you start spinning around it
- When you press again, you release from the rotator and start flying straight again
- When you press your action button while outside the rotator, you dodge and gain invincibility for a short time
- Also, when dodging, if you have any tail left, you shoot a single sphere in front of you which can kill other snakes

#### The points
- N is the number of players
- The last snake receives N-1 points
- The second to last snake receives N-2 points
- So on and so forth
- The first snake receives, therefore, 0 points
- Winner of the game must simultaneously collect 5 * (N-1) points AND have at least a 2-point lead

## Install
#### Linux
```
python -m venv venv
venv/bin/activate
pip install -r requirements.txt
python main.py
```

#### Windows
```
python -m venv venv
venv\Sctipts\activate
pip install -r requirements.txt
python main.py
```

### Writing your own bot
- Add a file to the bots folder
- Create a class, inherit from bot_base.Bot
- Implement get_action(self, state: GameState, time_delta: float) -> bool
- Import your bot in the `__init__.py` file
- Add your bot to the list of bots in the `__init__.py` file
- Start the application `python main.py`
- Your bot should be in the list