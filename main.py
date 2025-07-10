from traceback import print_exc

import pygame

import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-15s %(levelname)-8s %(name)-8s %(filename)s:%(lineno)s %(message)s')

from screens import GameScreen, PickColorScreen

def main():
    pygame.init()
    pygame.display.set_caption('Orbits clone')
    settings = {'fullscreen': False,
                'language': 'en'}
    if settings['fullscreen']:
        window_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        window_surface = pygame.display.set_mode((1200, 600), pygame.RESIZABLE)

    pcs = PickColorScreen(window_surface)
    colors = pcs.main()
    if pcs.force_quit:
        return
    GameScreen(window_surface, colors).main()


if __name__ == '__main__':
    main()
