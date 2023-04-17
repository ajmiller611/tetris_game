"""
    No tutorials on creating a Tetris game were used to create this program.
    First python project after learning the basics of python and pygame module.
    A heavier use of comments were used to explain the thinking and logic used for project portfolio purpose.
"""
from queue import Queue
from random import choice

import os
import pygame

from tetromino import Tetromino


class Game:
    def __init__(self):
        # Custom event creation for a timer to move the active tetromino down the playing area.
        self.move_down_event = pygame.USEREVENT

        # Since 16:9 aspect ratio is the most common for computer monitors, the width aspect has more flexibility due
        # to having more pixels to work with. This means the decision on appearance gets based off of height first.
        # In this case, the height of the play area takes up 70% of the window's height with 20% of the window above it
        # and 10% below it.
        self.play_area_rows = 13
        self.play_area_columns = 10
        self.cell_size = round(HEIGHT * 0.7) // self.play_area_rows
        self.margin = 4
        surface_width = self.cell_size * self.play_area_columns + self.margin
        surface_height = self.cell_size * self.play_area_rows + (self.margin // 2)
        self.play_area = pygame.surface.Surface((surface_width, surface_height))
        self.play_area_rect = self.play_area.get_rect(center=(WIDTH // 2, (HEIGHT // 2) + (HEIGHT * 0.05)))
        pygame.draw.rect(self.play_area, (255, 0, 255), self.play_area.get_rect(), 1)

        # Create a two-dimensional array that represents the grid of the play area.  A cell will contain a zero
        # to represent an empty cell or a Block object to represent an occupied cell.
        self.play_grid = []
        for row in range(self.play_area_rows):
            self.play_grid.append([])
            for column in range(self.play_area_columns):
                self.play_grid[row].append(0)

        # Tetromino setup
        self.start_x = self.play_area_rect.x + self.play_area_rect.width // 2 - self.cell_size
        self.start_y = int(HEIGHT * 0.2)
        self.active_tetromino = pygame.sprite.GroupSingle(Tetromino(choice(['I', 'J', 'L', 'O', 'S', 'T', 'Z']),
                                                                    self.start_x, self.start_y, self.cell_size))

        # Set up a queue for the next three tetrominos to be played.
        self.tetromino_queue = Queue(maxsize=3)
        for index in range(3):
            self.tetromino_queue.put(Tetromino(choice(['I', 'J', 'L', 'O', 'S', 'T', 'Z']),
                                               self.start_x, self.start_y, self.cell_size))
        self.tetromino_on_board = pygame.sprite.Group()

        # Player input delay setup
        self.allowed_movement = True
        self.time_of_movement = 0
        self.movement_cooldown = 800

        # Score setup
        self.score = 0
        self.score_font = pygame.font.SysFont('comicsans', int(HEIGHT * 0.06))

        # Controls label setup
        self.controls_label_font = pygame.font.SysFont('comicsans', int(HEIGHT * 0.03))

        # Lost setup
        self.lost = False
        self.lost_count = 0

    def player_input_movement(self):
        keys = pygame.key.get_pressed()

        if self.allowed_movement:
            # Left boundary check
            if keys[pygame.K_LEFT] and self.active_tetromino.sprite.rect.left > self.play_area_rect.left + self.margin:

                self.active_tetromino.sprite.move(-self.active_tetromino.sprite.block_size, 0)
                for tetromino in self.tetromino_on_board:
                    if self.collision_check(self.active_tetromino, tetromino):
                        self.active_tetromino.sprite.move(+self.active_tetromino.sprite.block_size, 0)
                self.allowed_movement = False
                self.time_of_movement = pygame.time.get_ticks()

            # Right boundary check
            elif keys[pygame.K_RIGHT] and self.active_tetromino.sprite.rect.right < self.play_area_rect.right - \
                    self.margin:

                self.active_tetromino.sprite.move(self.active_tetromino.sprite.block_size, 0)

                for tetromino in self.tetromino_on_board:
                    if self.collision_check(self.active_tetromino, tetromino):
                        self.active_tetromino.sprite.set_rect_x(tetromino.rect.left -
                                                                self.active_tetromino.sprite.rect.width)

                self.allowed_movement = False
                self.time_of_movement = pygame.time.get_ticks()

            elif keys[pygame.K_SPACE]:
                self.active_tetromino.sprite.rotate()

                # Rotate tetromino back if rotation causes the tetromino to leave the play area on the right or
                # bottom side.  The tetromino can't rotate outside the left side of the play area since the rotation
                # is always counterclockwise and the top left position stays the same before and after rotation.
                if self.active_tetromino.sprite.rect.right > self.play_area_rect.right or \
                        self.active_tetromino.sprite.rect.bottom > self.play_area_rect.bottom:
                    self.active_tetromino.sprite.rotate(False)

                # Rotate tetromino back if collision occurs.
                for tetromino in self.tetromino_on_board:
                    if self.collision_check(self.active_tetromino, tetromino):
                        self.active_tetromino.sprite.rotate(False)

                self.allowed_movement = False
                self.time_of_movement = pygame.time.get_ticks()

    def delay_movement(self):
        # Using the get_ticks() method in the pygame.time.Clock() class, a timer can be created to ignore repeated input
        # by the user.  This allows control on how quickly a tetromino can perform a movement command.  By tracking the
        # time a movement command took place and comparing it to the current time, a period of time can be established.
        if not self.allowed_movement:
            current_time = pygame.time.get_ticks()
            if current_time - self.time_of_movement >= self.movement_cooldown:
                self.allowed_movement = True

    def collision_check(self, active_tetromino, tetromino):
        if self.tetromino_on_board:
            # Check for rect collision before checking mask collision to increase performance.  Due to mask collision
            # checking each pixel, this makes mask collision more performance heavy.  Only calling mask collision if a
            # rect collision is found will limit the usage of the more resource intensive mask collision method to
            # when it is only necessary.
            if pygame.sprite.spritecollide(tetromino, active_tetromino, False):
                return pygame.sprite.collide_mask(tetromino, active_tetromino.sprite) is not None

    def move_down_active_tetromino(self):
        self.active_tetromino.sprite.move(0, self.active_tetromino.sprite.block_size)

        for tetromino in self.tetromino_on_board:
            # Check for the lost condition of the active tetromino colliding with another tetromino on the play area,
            # and it also crosses the boundary of the top of the play area.
            if self.active_tetromino.sprite.rect.top - self.active_tetromino.sprite.block_size < self.play_area_rect.y \
                    and self.collision_check(self.active_tetromino, tetromino):
                # Move the tetromino back to its position before it moved since a collision was detected.
                self.active_tetromino.sprite.move(0, -self.active_tetromino.sprite.block_size)
                self.lost = True
                break

            elif self.collision_check(self.active_tetromino, tetromino):
                self.active_tetromino.sprite.move(0, -self.active_tetromino.sprite.block_size)
                self.update_array_backed_play_grid()
                self.tetromino_on_board.add(self.active_tetromino.sprite)

                # Because the active tetromino is in a GroupSingle group, adding a sprite also removes the old sprite.
                # The queue get() method removes the first element from the queue and then returns that object.
                self.active_tetromino.add(self.tetromino_queue.get())
                self.tetromino_queue.put(Tetromino(choice(['I', 'J', 'L', 'O', 'S', 'T', 'Z']),
                                                   self.start_x, self.start_y, self.cell_size))

        # Check if the active tetromino reached the bottom of play area.
        if self.active_tetromino.sprite.rect.bottom > self.play_area_rect.bottom:
            self.active_tetromino.sprite.move(0, -self.active_tetromino.sprite.block_size)
            self.update_array_backed_play_grid()
            self.tetromino_on_board.add(self.active_tetromino.sprite)
            self.active_tetromino.add(self.tetromino_queue.get())
            self.tetromino_queue.put(Tetromino(choice(['I', 'J', 'L', 'O', 'S', 'T', 'Z']),
                                               self.start_x, self.start_y, self.cell_size))

    def update_array_backed_play_grid(self):
        # Calculate what row and column each block would be in to update the cell's status in the play grid.
        for block in self.active_tetromino.sprite.block_group:
            row_pos = (block.screen_y_pos - self.play_area_rect.y + self.margin) // self.cell_size
            column_pos = (block.screen_x_pos - self.play_area_rect.x) // self.cell_size
            self.play_grid[row_pos][column_pos] = block

    def full_row_check(self):
        number_of_full_rows = 0
        last_full_row_grid_index = -1
        last_full_row_y_pos = None

        for row in range(self.play_area_rows):
            occupied_cell_count = 0
            for column in range(self.play_area_columns):
                # If a cell doesn't hold a zero then there is a block occupying that cell.
                if self.play_grid[row][column] != 0:
                    occupied_cell_count += 1

            # All columns with an occupied cell means a full row of blocks exists.
            if occupied_cell_count == self.play_area_columns:
                # Count the number of full rows found to determine how many rows to shift down the above tetrominos.
                number_of_full_rows += 1

                # Find the index of the last full row to know where the above tetrominos need to be shifted.
                if row > last_full_row_grid_index:
                    last_full_row_grid_index = row
                    # Save the y position of the row to translate all blocks down one cell.
                    last_full_row_y_pos = self.play_grid[row][0].screen_y_pos

                self.clear_full_row(row)

        if number_of_full_rows != 0:
            self.shift_tetrominos_down(number_of_full_rows, last_full_row_grid_index, last_full_row_y_pos)

    def clear_full_row(self, row):
        # Set a pointer to the first tetromino for determining when to condense/separate.
        last_referenced_tetromino = self.play_grid[row][0].tetromino

        # Loop through each cell in the row to destroy the block and condense/separate a tetromino as needed.
        for index in range(self.play_area_columns):
            # Draw over the block's image at its location on the screen.
            pygame.draw.rect(self.play_grid[row][index].tetromino.image, 'black',
                             self.play_grid[row][index].rect)

            # Kill method removes the block from the pygame.sprite.Group it is in.
            self.play_grid[row][index].kill()
            self.score += 10

            # Call the condense_or_separate method only when the last block of the tetromino is destroyed in the row.
            # Using the pointer, the last block will be detected when the pointer and the current tetromino differ.
            if self.play_grid[row][index].tetromino != last_referenced_tetromino:
                # Check that the last tetromino wasn't completely destroyed and is still on the play area.
                if last_referenced_tetromino.block_group:
                    new_tetromino = last_referenced_tetromino.condense_or_separate()
                    if new_tetromino is not None:
                        self.tetromino_on_board.add(new_tetromino)

                    # Move the pointer to the reference of the current tetromino.
                    last_referenced_tetromino = self.play_grid[row][index].tetromino
                else:
                    # Since the tetromino was completely destroyed, remove it from its pygame.sprite.Group.
                    last_referenced_tetromino.kill()
                    last_referenced_tetromino = self.play_grid[row][index].tetromino

            # Last block in the row gets condensed/separated.
            if index == self.play_area_columns - 1:
                if self.play_grid[row][index].tetromino.block_group:
                    new_tetromino = self.play_grid[row][index].tetromino.condense_or_separate()
                    if new_tetromino is not None:
                        self.tetromino_on_board.add(new_tetromino)

                else:
                    self.play_grid[row][index].tetromino.kill()

            # Change the cell to zero to represent it's in an empty state.
            self.play_grid[row][index] = 0

    def shift_tetrominos_down(self, number_of_rows, last_row_grid_index, last_row_y_pos):
        # Shift all tetrominos above the full row down.
        for tetromino in self.tetromino_on_board:
            if tetromino.rect.y < last_row_y_pos:
                tetromino.move(0, tetromino.block_size * number_of_rows)

        for column in range(self.play_area_columns):
            # Start at the row above the last full row and increment the references in the occupied cells by one.
            # To move down in the array-backed grid, increment its index.
            for row in range(last_row_grid_index - 1, -1, -1):
                if self.play_grid[row][column] != 0:
                    self.play_grid[row + number_of_rows][column] = self.play_grid[row][column]
                    self.play_grid[row][column] = 0

    def draw_game_window(self):
        # Separate parts of the GUI into inner functions for better organization.
        def game_bg():
            # Credit: Image by Freepik
            bg_image = pygame.image.load(os.path.join('data', 'abstract_pixel_rain_background.jpg')).convert_alpha()
            scaled_bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
            bg = pygame.Surface((WIDTH, HEIGHT))
            bg.blit(scaled_bg_image, (0, 0))
            return bg

        def score_surface():
            score_label = self.score_font.render(f"Score: {self.score}", True, (0, 255, 0))
            score_surf = pygame.Surface((score_label.get_width() + 10, score_label.get_height()))  # 10 pixel padding
            pygame.draw.rect(score_surf, (0, 255, 255), score_surf.get_rect(), 1)
            score_surf.blit(score_label, (5, -5))
            return score_surf

        def controls_surface():
            left_arrow_label = self.controls_label_font.render('Left arrow = move left', True, (255, 255, 255))
            right_arrow_label = self.controls_label_font.render('Right arrow = move right', True, (255, 255, 255))
            spacebar_label = self.controls_label_font.render('Spacebar = rotate', True, (255, 255, 255))

            controls_label_list = (left_arrow_label, right_arrow_label, spacebar_label)
            greatest_label_width = 0
            for label in controls_label_list:
                if label.get_width() > greatest_label_width:
                    greatest_label_width = label.get_width()

            controls_surf = pygame.Surface((greatest_label_width + 10,  # 10 pixel padding
                                            (spacebar_label.get_height() * 3) + (HEIGHT * 0.03) + 10))
            pygame.draw.rect(controls_surf, (0, 255, 255), controls_surf.get_rect(), 1)

            controls_surf.blit(left_arrow_label, (5, 5))
            controls_surf.blit(right_arrow_label, (5, (HEIGHT * 0.01) + right_arrow_label.get_height() + 5))
            controls_surf.blit(spacebar_label, (5, (HEIGHT * 0.06) + spacebar_label.get_height() + 5))
            return controls_surf

        def tetromino_queue_surface(queued_tetromino):
            queue_surf = pygame.Surface((self.cell_size * 3 + 10, self.cell_size * 4 + 10))  # 10 pixel padding
            pygame.draw.rect(queue_surf, (255, 0, 255), queue_surf.get_rect(), 1)

            queue_surf.blit(queued_tetromino.image,
                            ((queue_surf.get_width() // 2) - (queued_tetromino.rect.width // 2),
                             (queue_surf.get_height() // 2) - (queued_tetromino.rect.height // 2)))
            return queue_surf

        window.blit(game_bg(), (0, 0))
        window.blit(self.play_area, (self.play_area_rect.x, self.play_area_rect.y))

        window.blit(controls_surface(), (10, HEIGHT - controls_surface().get_height() - 10))
        window.blit(score_surface(), ((WIDTH - score_surface().get_width() - 10), 10))

        for index, tetromino in enumerate(self.tetromino_queue.queue):
            height_offset = self.play_area_rect.top + ((self.cell_size * 4 + (HEIGHT * 0.0235)) * index)
            window.blit(tetromino_queue_surface(tetromino), (self.play_area_rect.right + 10, height_offset))

        # Draws a visual representation of the array-backed grid.
        # for row in range(1, self.play_area_rows):
        #     pygame.draw.line(self.play_area, 'red', (0, self.cell_size * row), (self.play_area_rect.width,
        #                                                                         (self.cell_size * row)))
        #     for column in range(1, self.play_area_columns):
        #         pygame.draw.line(self.play_area, 'red', (self.cell_size * column + 2, 0),
        #                          ((self.cell_size * column), self.play_area_rect.height))

    def run(self):
        self.player_input_movement()
        self.delay_movement()
        self.full_row_check()

        # The order of the drawing on screen matters and the background is always first. The drawing of the background
        # every frame is a way to clear the screen of the previous frame.  This allows the imitation of movement on the
        # screen by drawing an object in a slightly new position compared to its previous position.  An example in this
        # game is the falling of a tetromino from the top to the bottom of the play area.
        self.draw_game_window()
        self.active_tetromino.draw(window)
        self.tetromino_on_board.draw(window)


class GameState:
    def __init__(self):
        self.state = 'main_menu'
        self.game = Game()

    def main_menu(self):
        # pygame.event.wait() will allow the operating system to put the program to sleep when no events are needed
        # to be handled.  This allows the program to free up CPU resources while it is asleep.
        event = pygame.event.wait()
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.state = 'main_game'

            # Start the USEREVENT before the game starts. This is so it doesn't send unnecessary events for the event
            # handler to process and cause the program to not be put to sleep.
            pygame.time.set_timer(self.game.move_down_event, 1000)

        window.fill(BG_COLOR)

        title_font = pygame.font.SysFont("comicsans", 60)
        title_label = title_font.render("Tetris Project", True, (255, 255, 255))
        start_font = pygame.font.SysFont("comicsans", 60)
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
                quit()
            elif event.type == self.game.move_down_event:
                self.game.move_down_active_tetromino()

        self.game.run()
        pygame.display.update()

    def game_over(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        window.fill(BG_COLOR)
        lost_font = pygame.font.SysFont("comicsans", 60)
        lost_label = lost_font.render("Game Over!!", True, (255, 255, 255))
        window.blit(lost_label, (WIDTH / 2 - lost_label.get_width() / 2, HEIGHT / 2 - lost_label.get_height() / 2))
        pygame.display.update()

        # Wait three seconds in the lost state before going back to the main menu.
        if self.game.lost_count > FPS * 3:
            # Reset the game by creating a new Game object.
            self.game = Game()
            self.state = 'main_menu'
        else:
            self.game.lost_count += 1

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
    # WIDTH, HEIGHT = 800, 600
    WIDTH, HEIGHT = 1280, 720
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
