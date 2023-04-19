"""
    No tutorials on creating a Tetris game were used to create this program.
    First python project after learning the basics of python and pygame module.
    A heavier use of comments were used to explain the thinking and logic used for project portfolio purpose.
"""

import pygame
import sys

from game import Game


class GameState:
    def __init__(self):
        self.state = 'main_menu'
        self.game = Game(window)
        self.lost_count = 0

    def main_menu(self):
        # pygame.event.wait() will allow the operating system to put the program to sleep when no events are needed
        # to be handled.  This allows the program to free up CPU resources while it is asleep.
        event = pygame.event.wait()
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.state = 'main_game'

            # Start the USEREVENT before the game starts. This is so it doesn't send unnecessary events for the event
            # handler to process and cause the program to not be put to sleep.
            pygame.time.set_timer(self.game.move_down_event, 1000)

        window.fill(BG_COLOR)

        title_font = pygame.font.SysFont("comicsans", int(HEIGHT * 0.06))
        title_label = title_font.render("Tetris Project", True, (255, 255, 255))
        start_font = pygame.font.SysFont("comicsans", int(HEIGHT * 0.06))
        start_label = start_font.render("Press a mouse button to begin...", True, (255, 255, 255))

        window.blit(title_label, (WIDTH / 2 - title_label.get_width() / 2,
                                  (HEIGHT / 2) / 2 - title_label.get_height() / 2))
        window.blit(start_label, (WIDTH / 2 - start_label.get_width() / 2,
                                  HEIGHT / 2 - start_label.get_height() / 2))
        pygame.display.update()

    def main_game(self):
        if self.game.lost:
            self.state = 'lost'

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == self.game.move_down_event:
                self.game.move_down_active_tetromino()

        self.game.run()
        pygame.display.update()

    def game_over(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        window.fill(BG_COLOR)
        lost_font = pygame.font.SysFont("comicsans", int(HEIGHT * 0.06))
        lost_label = lost_font.render("Game Over!!", True, (255, 255, 255))
        window.blit(lost_label, (WIDTH / 2 - lost_label.get_width() / 2, HEIGHT / 2 - lost_label.get_height() / 2))
        pygame.display.update()

        # Wait three seconds in the lost state before going back to the main menu.
        if self.lost_count > FPS * 3:
            # Reset the game by creating a new Game object.
            self.game = Game(window)
            self.state = 'main_menu'
        else:
            self.lost_count += 1

    def state_manager(self):
        match self.state:
            case 'main_menu':
                self.main_menu()
            case 'main_game':
                self.main_game()
            case 'lost':
                self.game_over()


# Only run the program from this python file directly and not when imported as a module.
if __name__ == "__main__":
    # General setup
    pygame.init()
    clock = pygame.time.Clock()

    # Screen setup
    BG_COLOR = (0, 0, 0)
    WIDTH, HEIGHT = 800, 600
    # WIDTH, HEIGHT = 1920, 1080
    FPS = 60
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tetris Project")
    game_state = GameState()

    # Game loop
    while True:
        game_state.state_manager()
        # Limit the frames per second
        clock.tick(FPS)
