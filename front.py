from dataclasses import dataclass
from typing import Optional

import pygame
import pygame.freetype
from pygame import Vector2

from back import Sphere, RotatorSphere, Burst, PlayerSphere, GameStage, color_names, Team, GameStateFront

def draw_sphere(surface: pygame.Surface, sphere: Sphere, game_size: tuple[int, int], force_color=None):
    if force_color is None:
        force_color = sphere.color
    rect = sphere.get_rect()
    new_rect = tuple(map(lambda i : i * min(game_size), rect))
    pygame.draw.ellipse(surface, color=force_color, rect=new_rect)

def draw_player_triangle(surface: pygame.Surface, sphere: Sphere, game_size: tuple[int, int]):
    center = sphere.center
    scaled_center = center * min(game_size)
    vel = sphere.velocity.copy()
    vel.scale_to_length(0.01)
    vel = vel * min(game_size)
    little_forward = scaled_center + vel
    to_the_right = vel.rotate(90)
    back_right = scaled_center - vel + to_the_right
    back_left = scaled_center - vel - to_the_right
    pygame.draw.polygon(surface, (255,255,255), [little_forward, back_right, back_left])

def draw_rotator(surface, rotator: RotatorSphere, game_size):
    draw_sphere(surface, rotator, game_size)
    draw_sphere(surface, rotator.middle_sphere, game_size)

def draw_burst(surface, burst: Burst, game_size):
    draw_sphere(surface, burst, game_size)
    draw_sphere(surface, burst.middle_sphere, game_size)

def draw_player(surface, sphere: PlayerSphere, game_size):
    if not sphere.alive: return
    for i in sphere.trail:
        draw_sphere(surface, i, game_size)
    for i in sphere.queue_to_trail:
        draw_sphere(surface, i, game_size)
    for i in sphere.attacking_spheres:
        draw_sphere(surface, i, game_size)
    if sphere.is_dodging():
        draw_sphere(surface, sphere, game_size, force_color=pygame.Color(255,255,255).lerp(sphere.color, 0.7))
    else:
        draw_sphere(surface, sphere, game_size)
    draw_player_triangle(surface, sphere, game_size)

font = pygame.freetype.SysFont('arial', 25)

def calculate_players_leaderboard_positions(game_size, i):
    width = game_size[0] / 5
    height = game_size[1] / 8
    return (width*(2*i//len(Team) + 1), height * (i%(len(Team)//2) + 1))

def draw_player_leaderboard(surface, pos, text, color):
    size = surface.get_rect().size
    circle_size = size[1]/9
    pygame.draw.ellipse(surface, color, (pos, (circle_size, circle_size)))
    font.render_to(surface, (pos[0]+2*circle_size, pos[1]), text, color, size=circle_size*1.5)

def draw_game(surface, state: GameStateFront, game_size):
    for i in state.rotators:
        draw_rotator(surface, i, game_size)
    for i in state.active_spheres:
        draw_sphere(surface, i, game_size)
    for i in state.inactive_spheres:
        draw_sphere(surface, i, game_size)
    for i in state.bursts:
        draw_burst(surface, i, game_size)
    for i in state.player_spheres:
        draw_player(surface, i, game_size)
    if state.stage == GameStage.ROTATING_AROUND_CENTER:
        time = int(state.timer)
        text = str(3 - time)
        size = 50
        font.render_to(surface, (game_size[0]//2-size//3, game_size[1]//2-size//2, 0, 0), text, (255, 255, 255), size=size)
    if state.stage == GameStage.SHOWING_RESULTS:
        num_players = len(state.player_spheres)
        font.render_to(surface, (30, 30), state.how_to_win_text, (255,255,255))
        if 0 < state.timer <= 1.5:
            for player_score in state.player_scores:
                pos = calculate_players_leaderboard_positions(game_size, player_score.old_position)
                draw_player_leaderboard(surface, pos, str(player_score.old_score), player_score.color)
        if 1.5 < state.timer <= 2:
            for player_score in state.player_scores:
                pos = calculate_players_leaderboard_positions(game_size, player_score.old_position)
                draw_player_leaderboard(surface, pos, str(player_score.new_score), player_score.color)
        elif 2 < state.timer <= 4:
            t = (state.timer - 2) / (4 - 2)
            for player_score in state.player_scores:
                old_pos = calculate_players_leaderboard_positions(game_size, player_score.old_position)
                new_pos = calculate_players_leaderboard_positions(game_size, player_score.new_position)
                pos = Vector2(old_pos).lerp(new_pos, t)
                draw_player_leaderboard(surface, pos, str(player_score.new_score), player_score.color)
        elif 4 < state.timer <= 5:
            for player_score in state.player_scores:
                pos = calculate_players_leaderboard_positions(game_size, player_score.new_position)
                draw_player_leaderboard(surface, pos, str(player_score.new_score), player_score.color)
    if state.stage == GameStage.END_SCREEN:
        color = state.someone_won
        font.render_to(surface, (30, 30, 100, 25), f'{color_names[color]} won', color)
        time = int(state.timer)
        text = str(30 - time)
        font.render_to(surface, (game_size[0]/2-15, game_size[1] - 50), text, color)

        for player_score in state.player_scores:
            pos = calculate_players_leaderboard_positions(game_size, player_score.new_position)
            draw_player_leaderboard(surface, pos, str(player_score.new_score), player_score.color)
