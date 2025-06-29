from typing import Any

import pygame
import pygame.freetype
pygame.freetype.init()
import pygame_gui
from pygame_gui.elements import UIButton, UIDropDownMenu

from back import Game, Team, BotKeys, PlayerSphere
from front import draw_game, calculate_players_leaderboard_positions, draw_player_leaderboard
from bots import bots

font = pygame.freetype.SysFont('arial', 25)

class Screen:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.window_size = self.surface.get_rect().size
        self.background = pygame.Surface(self.window_size)
        self.background_color = '#101010'
        self.background.fill(pygame.Color(self.background_color))
        self.return_value = None
        self.force_quit = False
        self.manager = pygame_gui.UIManager(self.window_size)
        self.framerate = 60

    def clean_up(self):
        return
    def process_events(self, event):
        return
    def update(self, time_delta):
        return
    def on_window_size_changed(self, size):
        self.window_size = size
        self.manager.set_window_resolution(size)
        self.background = pygame.Surface(size)
        self.background.fill(pygame.Color(self.background_color))

    def main(self):
        clock = pygame.time.Clock()
        self.is_running = True
        while self.is_running:
            time_delta = clock.tick(self.framerate)/1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.force_quit = True
                    self.is_running = False
                elif event.type == pygame.WINDOWSIZECHANGED:
                    if event.window is None:
                        self.on_window_size_changed((event.x, event.y))
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.force_quit = True
                        self.is_running = False
                self.process_events(event)
                self.manager.process_events(event)
            self.surface.blit(self.background, (0, 0))
            self.manager.update(time_delta)
            self.update(time_delta)
            self.manager.draw_ui(self.surface)
            pygame.display.set_caption(f'Orbits clone | {clock.get_fps():.1f}')
            pygame.display.update()
        self.clean_up()
        return self.return_value


def inscribed_rectangle_dimensions(w, h):
    vertical_side = min(w, h / 2)
    horizontal_side = min(w / 2, h)
    if horizontal_side > vertical_side:
        return 2 * horizontal_side, horizontal_side
    else:
        return vertical_side, 2 * vertical_side

class GameScreen(Screen):
    def __init__(self, surface: pygame.Surface, colors, seed=None):
        super().__init__(surface)
        self.colors = colors
        self.window_size = self.surface.get_rect().size
        self.visual_debug = False
        self.game_size = inscribed_rectangle_dimensions(*self.window_size)
        borderx = (self.window_size[0] - self.game_size[0]) / 2
        bordery = (self.window_size[1] - self.game_size[1]) / 2
        self.game_surface_margin = borderx, bordery
        # self.game = None
        self.game = Game(colors, seed)
        self.game_surface = pygame.Surface(self.game_size)
        self.draw_debug = False
        self.is_paused = False
        self.by_step = False
        self.restart = False
        self.actions = []

    def on_window_size_changed(self, size):
        super().on_window_size_changed(size)
        self.game_size = inscribed_rectangle_dimensions(*self.window_size)
        self.game_surface = pygame.Surface(self.game_size)
        borderx = (self.window_size[0] - self.game_size[0]) / 2
        bordery = (self.window_size[1] - self.game_size[1]) / 2
        self.game_surface_margin = borderx, bordery

    def process_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and pygame.key.get_mods() & pygame.KMOD_ALT:
                self.visual_debug = not self.visual_debug
                self.manager.set_visual_debug_mode(self.visual_debug)
            if event.key in self.colors.keys():
                self.actions.append(event.key)
            elif event.key == pygame.K_F1:
                self.draw_debug = not self.draw_debug
            elif event.key == pygame.K_F2:
                self.is_paused = not self.is_paused
            elif event.key == pygame.K_F3:
                self.by_step = True
                self.is_paused = True
            elif event.key == pygame.K_F5:
                self.restart = True
            elif event.key == pygame.K_F6:
                self.framerate *= 1.2
            elif event.key == pygame.K_F7:
                self.framerate /= 1.2

    def update(self, time_delta):
            self.game_surface.fill(pygame.Color('#000000'))
            if self.game is not None:
                if self.restart:
                    self.game.restart_round()
                    self.restart = False
                if not self.is_paused or self.by_step:
                    self.game.process_actions(self.actions)
                    self.game.update(1/60)
                    self.actions = []
                    self.by_step = False

                state = self.game.get_front_state()
                draw_game(self.game_surface, state, self.game_size)
                if self.draw_debug:
                    self.game.draw_debug(self.game_surface)
            self.surface.blit(self.game_surface, self.game_surface_margin)
    # finally:
    #     if game is not None:
    #         game.exit()


class PickColorScreen(Screen):
    MIN_PLAYERS = 1
    def __init__(self, surface: pygame.Surface, draw_bots_buttons=True):
        super().__init__(surface)
        self.key_map : dict[int, tuple[Team, str, Any]] = {}
        self.key_team_iter_map = {}
        self.unavailable_teams = []
        self.order = []
        self.captured_keys = []
        rect = pygame.Rect(0, 0, 100, 100)
        rect.right = -30
        self.add_bot_button = UIButton(rect, 'Add bot', self.manager, anchors={'right': 'right'}, visible=draw_bots_buttons)
        self.remove_bot_button = UIButton(rect, 'Remove bot', self.manager, anchors={'right': 'right', 'top_target': self.add_bot_button}, visible=draw_bots_buttons)
        options = [bot.__name__ for bot in bots]
        self.bots = {bot.__name__: bot for bot in bots}
        rect.height = 30
        self.pick_bot = UIDropDownMenu(options, options[0], rect, self.manager, anchors={'right': 'right', 'top_target': self.remove_bot_button}, visible=draw_bots_buttons)
        self.num_bots = 0

    def process_events(self, event):
        if event.type == pygame.KEYDOWN:
            self.captured_keys.append((event.key, pygame.key.name(event.key)))
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.add_bot_button:
                self.add_bot(self.bots[self.pick_bot.selected_option])
            elif event.ui_element == self.remove_bot_button:
                self.remove_bot()

    def find_available_team(self, key):
        if key not in self.key_team_iter_map:
            self.key_team_iter_map[key] = iter(Team)

        team = None
        if len(self.unavailable_teams) == len(Team):
            return None
        while True:
            try:
                team = next(self.key_team_iter_map[key])
                if team in self.unavailable_teams:
                    continue
                return team
            except StopIteration:
                self.key_team_iter_map[key] = iter(Team)

    def add_bot(self, BotClass):
        if self.num_bots == 12: return
        bot_enum = list(BotKeys)[self.num_bots]
        team = self.find_available_team(bot_enum)
        name = f'{BotClass.__name__} {self.num_bots+1}'
        self.add_player(bot_enum, team, name, BotClass)
        self.num_bots += 1

    def remove_bot(self):
        if self.num_bots == 0: return
        bot_enum = list(BotKeys)[self.num_bots-1]
        self.remove_player(bot_enum)
        self.num_bots -= 1

    def add_player(self, key, team, name, PlayerClass):
        self.key_map[key] = team, name, PlayerClass
        self.unavailable_teams.append(team)
        if key not in self.order:
            self.order.append(key)

    def remove_player(self, key):
        team, name, PlayerClass = self.key_map.pop(key)
        self.unavailable_teams.remove(team)

    def process_player_action(self, key, name):
        if key in self.key_map:
            self.remove_player(key)
        else:
            team = self.find_available_team(key)
            if team is not None:
                self.add_player(key, team, name, PlayerSphere)

    def update(self, time_delta):
        for key, name in self.captured_keys:
            if key == pygame.K_SPACE:
                if len(self.key_map) >= self.MIN_PLAYERS and self.is_running:
                    self.return_value = self.key_map
                    self.is_running = False
            else:
                self.process_player_action(key, name)
        self.captured_keys = []

        size = self.surface.get_rect().size
        surf1, textsize1 = font.render('PRESS BUTTONS', (255, 255, 255), size=32)
        surf2, textsize2 = font.render('then hit space', (255, 255, 255), size=32)
        self.surface.blit(surf1, (30, 30))
        self.surface.blit(surf2, (30, size[1] - 30 - textsize2[1]))
        for key, (team, name, PlayerClass) in self.key_map.items():
            i = self.order.index(key)
            pos = calculate_players_leaderboard_positions(size, i)
            draw_player_leaderboard(self.surface, pos, name, team.value)
