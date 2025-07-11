from dataclasses import dataclass
from enum import Enum, auto
from typing import Union, Optional
from collections import deque
import math

import pygame
from pygame import Vector2

import typing
if typing.TYPE_CHECKING:
    from bots import Bot

# reference from picture in pixels
REFERENCE_SCREEN_SIZE = 885
REFERENCE_ROTATOR_SIZE = 285
REFERENCE_ROTATOR_INNER_SIZE = 26
REFERENCE_PLAYER_SIZE = 45
REFERENCE_PLAYER_SPHERE_DISTANCE = 63.15
REFERENCE_SPHERE_SIZE = 33
REFERENCE_BURST_OUTER_SIZE = 59
REFERENCE_BURST_INNER_SIZE = 41

# part of screen
ROTATOR_SIZE = REFERENCE_ROTATOR_SIZE / REFERENCE_SCREEN_SIZE / 2
ROTATOR_INNER_SIZE = REFERENCE_ROTATOR_INNER_SIZE / REFERENCE_SCREEN_SIZE / 2
PLAYER_SIZE = REFERENCE_PLAYER_SIZE / REFERENCE_SCREEN_SIZE / 2
SPHERE_SIZE = REFERENCE_SPHERE_SIZE / REFERENCE_SCREEN_SIZE / 2
BURST_SIZE = REFERENCE_BURST_OUTER_SIZE / REFERENCE_SCREEN_SIZE / 2
BURST_INNER_RATIO = REFERENCE_BURST_INNER_SIZE / REFERENCE_BURST_OUTER_SIZE

DEFAULT_SPEED = 2 / 400

class Team(Enum):
    RED = (255, 90, 40)
    GREEN = (40, 255, 40)
    BLUE = (63, 80, 255)
    DARKRED = (190, 0, 0)
    DARKGREEN = (25, 93, 42)

    YELLOW = (255, 255, 40)
    PINK = (255, 40, 255)
    SKY = (40, 255, 255)
    PURPLE = (142, 70, 172)

    ORANGE = (255, 130, 1)
    BROWN = (128, 64, 64)
    INDIGO = (70, 0, 148)

color_names = {
    team.value: name for team, name in zip(Team, [
        'Red', 'Green', 'Blue', 'Dark red', 'Dark green', 'Yellow', 'Pink', 'Sky', 'Purple', 'Orange', 'Brown', 'Indigo'
    ])
}

@dataclass
class VerticalLine:
    x: float
@dataclass
class HorizontalLine:
    y: float


@dataclass
class Sphere:
    center: Vector2
    velocity: Vector2
    radius: float
    color: tuple[int, int, int] = (255, 255, 255)
    mass: float = 1
    damping_factor: float = 1

    def get_rect(self):
        return self.center.x-self.radius, self.center.y-self.radius, self.radius*2, self.radius*2

    def intersects(self, other: 'Sphere'):
        return self.center.distance_squared_to(other.center) <= (self.radius + other.radius) ** 2
    def intersects_vertical_line(self, other: VerticalLine):
            return other.x - self.radius < self.center.x < other.x + self.radius
    def intersects_horizontal_line(self, other: HorizontalLine):
        return other.y - self.radius < self.center.y < other.y + self.radius

    def check_center_inside(self, other: 'Sphere'):
        return self.center.distance_squared_to(other.center) <= other.radius ** 2

    def collide_with(self, other: 'Sphere'):
            # pushout
            dist = self.center.distance_to(other.center)
            overlap = -(dist - self.radius - other.radius) * 0.5
            self.center += overlap * (self.center - other.center).normalize() * 1.003
            other.center -= overlap * (self.center - other.center).normalize() * 1.003

            # elastic collision
            n = (other.center - self.center).normalize()
            k = self.velocity - other.velocity
            p = 2 * (n * k) / (self.mass + other.mass)
            self.velocity -= p * other.mass * n
            other.velocity += p * self.mass * n

    def update(self):
        self.center += self.velocity
        self.velocity *= self.damping_factor

class RotatorSphere(Sphere):
    def __init__(self, center, radius):
        super().__init__(center, Vector2(0,0), radius, (51, 51, 51))
        self.middle_sphere = Sphere(center, Vector2(0, 0), radius/20, (100, 100, 100))

class Burst(Sphere):
    def __init__(self, center, radius):
        super().__init__(center, Vector2(0,0), radius, (255, 255, 255))
        self.middle_sphere = Sphere(center, Vector2(0, 0), radius * BURST_INNER_RATIO, (100, 100, 100))
        self.grow_rate = radius / 5
        self.alive = True
        self.active = False
        self.active_player: Optional[PlayerSphere] = None
        self.frames_from_burst = 0
        self.frames_from_spawn = 0

    def activate(self, active_player):
        self.active = True
        self.active_player = active_player

    def update(self):
        if self.active:
            if self.frames_from_burst < 40:
                self.radius += self.grow_rate
                self.middle_sphere.radius += self.grow_rate
            else:
                self.alive = False
            self.frames_from_burst += 1
        elif self.frames_from_spawn > 1200:
            self.alive = False
        self.frames_from_spawn += 1


class PlayerSphere(Sphere):
    '''
    These fields are available in PlayerSphere

    self.rotating_around : Optional[RotatorSphere]
        if player is not rotating around a rotator, it's None
        otherwise, its a Rotator which you rotate around

    self.dodge_initiated : bool
        whether you initiated a dodge this frame

    self.frames_from_dodge : int
        number of frames after initiating a dodge
        is_dodging: 0 < frames_from_dodge <= 30
        is_dodge_cooldown: 30 < frames_from_dodge < 60
        can_dodge: frames_from_dodge == 0


    self.path : deque[Vector2]
        list of last n coordinates,
        where n depends on the length of your trail

    self.queue_to_trail : list[Sphere]
        list of spheres to be added to your trail
        this is needed because when you kill another snake,
        their tail flies to you. This list acts as your spheres
        which cannot kill other snakes

    self.trail : list[Sphere]
        list of spheres in your trail which can kill other snakes

    self.attacking_spheres: list[Sphere]
        list of your attacking spheres. These fly straight after a dodge

    self.alive : bool
        whether you are alive or killed

    self.bot: Optional[Bot]
        None if human-controlled
        Bot if Bot-controlled
    '''
    max_dodge_duration = 30
    cooldown_duration = 30
    dodge_speed = 1.5
    path_size_per_trail_sphere=10
    def __init__(self, center, velocity, radius, color):
        super().__init__(center, velocity, radius, color)
        self.rotating_around : Optional[RotatorSphere] = None
        self.dodge_initiated = False
        self.frames_from_dodge = 0
        self.path : deque[Vector2] = deque(maxlen=self.path_size_per_trail_sphere)
        self.path.append(center)
        self.queue_to_trail : list[Sphere] = []
        self.trail : list[Sphere] = []
        self.attacking_spheres: list[Sphere] = []
        self.alive = True
        self.bot : Optional['Bot'] = None

    def is_dodging(self):
        return 0 < self.frames_from_dodge <= self.max_dodge_duration
    def is_dodge_cooldown(self):
        return self.max_dodge_duration < self.frames_from_dodge < self.max_dodge_duration + self.cooldown_duration
    def can_dodge(self):
        return self.frames_from_dodge == 0

    def is_in_rotator(self, rotators):
        for rotator in rotators:
            if self.check_center_inside(rotator):
                return True
        return False

    def add_bot(self, bot: Optional['Bot']):
        self.bot = bot

    def add_sphere_to_queue(self, sphere: Sphere):
        self.queue_to_trail.append(sphere)
        self.path = deque(self.path, maxlen=(len(self.trail)+len(self.queue_to_trail)+1) * self.path_size_per_trail_sphere) # type: ignore

    def add_sphere_to_trail(self, sphere: Sphere):
        self.trail.append(sphere)
        sphere.color = self.color

    def remove_sphere(self, index=0):
        sphere = self.trail.pop(index)
        self.path = deque(self.path, maxlen=(len(self.trail)+1) * self.path_size_per_trail_sphere) # type: ignore
        return sphere

    def get_sphere_position(self, i) -> Vector2:
        try:
            return self.path[self.path_size_per_trail_sphere * i - 1]
        except IndexError:
            return self.path[-1]

    def update(self):
        if not self.alive: return
        if self.rotating_around is None:
            if self.dodge_initiated:
                self.frames_from_dodge = 1
                self.dodge_initiated = False
            if self.is_dodging():
                self.center += self.velocity * self.dodge_speed
                self.frames_from_dodge += 1
            elif self.is_dodge_cooldown():
                self.frames_from_dodge += 1
                self.center += self.velocity
            else:
                self.frames_from_dodge = 0
                self.center += self.velocity
        else:
            me_rotator_vector = self.rotating_around.center - self.center
            angle = me_rotator_vector.angle_to(self.velocity)
            delta_angle = 360 * DEFAULT_SPEED / (2 * math.pi * me_rotator_vector.magnitude())
            while angle > 180: angle -= 360
            while angle < -180: angle += 360
            if angle < 0:
                velocity_rotate_angle = 90
            else:
                delta_angle *= -1
                velocity_rotate_angle = -90
            rotator_me_vector = -me_rotator_vector
            new_rotator_me_vector = rotator_me_vector.rotate(delta_angle)
            self.center = self.rotating_around.center + new_rotator_me_vector
            self.velocity = new_rotator_me_vector.rotate(velocity_rotate_angle)
            self.velocity.scale_to_length(DEFAULT_SPEED)
        for i, sphere in enumerate(self.trail, 1):
            sphere.center = sphere.center.move_towards(self.get_sphere_position(i), DEFAULT_SPEED*3)
        for i, sphere in enumerate(self.queue_to_trail, len(self.trail)):
            sphere.center = sphere.center.move_towards(self.get_sphere_position(i), DEFAULT_SPEED*3)
            if sphere.center == self.get_sphere_position(i):
                self.add_sphere_to_trail(sphere)
                self.queue_to_trail.remove(sphere)
        self.path.appendleft(Vector2(self.center))

    def draw_debug(self, debug_surface: pygame.Surface):
        size = debug_surface.get_rect().size

        import pygame.freetype
        pygame.freetype.init()
        font = pygame.freetype.SysFont('arial', 25)

        def mul(point, size):
            return point[0]*min(size), point[1]*min(size)
        
        font.render_to(debug_surface, mul([self.center[0]+0.025, self.center[1]], size), f'{self.bot.__class__.__name__}', self.color, size=10)
        pygame.draw.line(debug_surface, (255,255,255), mul(self.center, size), mul(self.center+self.velocity*20, size), width=3)
        pygame.draw.circle(debug_surface, (255, 255, 255), mul(self.path[0], size), 5)
        pygame.draw.circle(debug_surface, (255, 255, 255), mul(self.path[-1], size), 5)
        pygame.draw.circle(debug_surface, (0, 0, 0), mul(self.path[-1], size), 3)
        if self.rotating_around:
            pygame.draw.line(debug_surface, (255,0,0), mul(self.center, size), mul(self.rotating_around.center, size), width=3)
            me_rotator_vector = self.rotating_around.center - self.center
            angle = me_rotator_vector.angle_to(self.velocity)
            delta_angle = 360 * DEFAULT_SPEED / (2 * math.pi * me_rotator_vector.magnitude())
            while angle > 180: angle -= 360
            while angle < -180: angle += 360
            if angle < 0:
                velocity_rotate_angle = -90
            else:
                delta_angle *= -1
                velocity_rotate_angle = 90
            rotator_me_vector = -me_rotator_vector
            new_rotator_me_vector = rotator_me_vector.rotate(delta_angle)
            pygame.draw.line(debug_surface, (255,255,0), mul(self.rotating_around.center + new_rotator_me_vector, size), mul(self.rotating_around.center, size), width=3)

@dataclass
class PlayerScore:
    old_score: int = -1
    old_position: int = -1
    new_score: int = -1
    new_position: int = -1
    color: Optional[tuple[int,int,int]] = None

class GameStage(Enum):
    ROTATING_AROUND_CENTER = 1
    GAMING = 2
    SHOWING_RESULTS = 3
    RESTART_ROUND = 4
    END_SCREEN = 5

@dataclass
class GameState:
    '''GameState represents a state of this Game

    player_spheres: list[PlayerSphere]
    list of PlayerSpheres, these are humans and bots

    active_spheres: list[Sphere]
    list of Spheres which will spawn new spheres after being collected

    inactive_spheres: list[Sphere]
    list of Spheres which will NOT spawn new spheres after being collected

    bursts: list[Burst]
    list of Bursts which will collect spheres nearby

    rotators: list[RotatorSphere]
    list of rotators on this map

    timer: float
    time from the start of round

    death_order: list[int]
    order in which players died. Needed to calculate victory points

    seed: int
    seed of this round

    total_uniforms: int
    number of times random.uniform() was called
    '''
    player_spheres: list[PlayerSphere]
    active_spheres: list[Sphere]
    inactive_spheres: list[Sphere]
    bursts: list[Burst]
    rotators: list[RotatorSphere]
    timer: float
    death_order: list[int]
    seed: int
    total_uniforms: int
    def update_to_front(self, player_scores: list[PlayerScore], how_to_win_text: str, stage: GameStage, someone_won: Optional[tuple[int, int, int]]):
        return GameStateFront(self.player_spheres,
                              self.active_spheres,
                              self.inactive_spheres,
                              self.bursts,
                              self.rotators,
                              self.timer,
                              self.death_order,
                              self.seed,
                              self.total_uniforms,
                              # self.random_,
                              player_scores, how_to_win_text, stage, someone_won)

@dataclass
class GameStateFront(GameState):
    player_scores: list[PlayerScore]
    how_to_win_text: str
    stage: GameStage
    someone_won: Optional[tuple[int, int, int]]

@dataclass
class Map:
    rotators_coords: list[tuple[float, float, float]]

class BotKeys(Enum):
    IS_BOT_1 = auto()
    IS_BOT_2 = auto()
    IS_BOT_3 = auto()
    IS_BOT_4 = auto()
    IS_BOT_5 = auto()
    IS_BOT_6 = auto()
    IS_BOT_7 = auto()
    IS_BOT_8 = auto()
    IS_BOT_9 = auto()
    IS_BOT_10 = auto()
    IS_BOT_11 = auto()
    IS_BOT_12 = auto()
