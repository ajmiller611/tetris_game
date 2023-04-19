from queue import Queue
from random import choice

import os
import pygame

from tetromino import Tetromino
from play_area import PlayArea


class Game:
    def __init__(self, window):
        self.window = window
        self.play_area = PlayArea(self.window.get_width(), self.window.get_height())

        # Create a two-dimensional array that represents the grid of the play area.  A cell will contain a zero
        # to represent an empty cell or a Block object to represent an occupied cell.
        self.play_grid = []
        for row in range(self.play_area.rows):
            self.play_grid.append([])
            for column in range(self.play_area.columns):
                self.play_grid[row].append(0)

        # Tetromino setup
        self.start_x = self.play_area.rect.x + self.play_area.rect.width // 2 - self.play_area.cell_size
        self.start_y = int(self.window.get_height() * 0.2)
        self.active_tetromino = pygame.sprite.GroupSingle(Tetromino(choice(['I', 'J', 'L', 'O', 'S', 'T', 'Z']),
                                                                    self.start_x, self.start_y,
                                                                    self.play_area.cell_size))

        # Custom event creation for a timer to move the active tetromino down the playing area.
        self.move_down_event = pygame.USEREVENT

        # Set up a queue for the next three tetrominos to be played.
        self.tetromino_queue = Queue(maxsize=3)
        for index in range(3):
            self.tetromino_queue.put(Tetromino(choice(['I', 'J', 'L', 'O', 'S', 'T', 'Z']),
                                               self.start_x, self.start_y, self.play_area.cell_size))
        self.tetromino_on_board = pygame.sprite.Group()

        # Player input delay setup
        self.allowed_movement = True
        self.time_of_movement = 0
        self.movement_cooldown = 500

        # When the player is holding down a key, multiple pygame.KEYDOWN events are generated. To limit the amount of
        # unnecessary key events, set a delay on repeated key events so these events can't be generated during the
        # cooldown time period.
        pygame.key.set_repeat(self.movement_cooldown)

        # Score setup
        self.score = 0

        # Lost flag
        self.lost = False

    def player_input_handler(self):
        keys = pygame.key.get_pressed()

        if self.allowed_movement:
            # Left boundary check
            if keys[pygame.K_LEFT] and self.active_tetromino.sprite.rect.left > \
                    self.play_area.rect.left + self.play_area.margin:

                self.active_tetromino.sprite.move(-self.active_tetromino.sprite.block_size, 0)
                for tetromino in self.tetromino_on_board:
                    if self.collision_check(self.active_tetromino, tetromino):
                        self.active_tetromino.sprite.move(self.active_tetromino.sprite.block_size, 0)
                self.allowed_movement = False
                self.time_of_movement = pygame.time.get_ticks()

            # Right boundary check
            elif keys[pygame.K_RIGHT] and self.active_tetromino.sprite.rect.right < self.play_area.rect.right - \
                    self.play_area.margin:

                self.active_tetromino.sprite.move(self.active_tetromino.sprite.block_size, 0)

                for tetromino in self.tetromino_on_board:
                    if self.collision_check(self.active_tetromino, tetromino):
                        self.active_tetromino.sprite.move(-self.active_tetromino.sprite.block_size, 0)

                self.allowed_movement = False
                self.time_of_movement = pygame.time.get_ticks()

            elif keys[pygame.K_SPACE]:
                self.active_tetromino.sprite.rotate()

                # Rotate tetromino back if rotation causes the tetromino to leave the play area on the right or
                # bottom side.  The tetromino can't rotate outside the left side of the play area since the rotation
                # is always counterclockwise and the top left position stays the same before and after rotation.
                if self.active_tetromino.sprite.rect.right > self.play_area.rect.right or \
                        self.active_tetromino.sprite.rect.bottom > self.play_area.rect.bottom:
                    self.active_tetromino.sprite.rotate(False)

                # Rotate tetromino back if collision occurs.
                for tetromino in self.tetromino_on_board:
                    if self.collision_check(self.active_tetromino, tetromino):
                        self.active_tetromino.sprite.rotate(False)

                self.allowed_movement = False
                self.time_of_movement = pygame.time.get_ticks()

    def allow_movement_check(self):
        # Using the get_ticks() method in the pygame.time.Clock() class, a timer can be created to control how quickly a
        # tetromino can perform a movement command.  By tracking the time a movement command took place and comparing it
        # to the current time, an elapsed period of time can be established.
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
            if self.active_tetromino.sprite.rect.top < self.play_area.rect.y \
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
                                                   self.start_x, self.start_y, self.play_area.cell_size))

        # Check if the active tetromino reached the bottom of play area.
        if self.active_tetromino.sprite.rect.bottom > self.play_area.rect.bottom:
            self.active_tetromino.sprite.move(0, -self.active_tetromino.sprite.block_size)
            self.update_array_backed_play_grid()
            self.tetromino_on_board.add(self.active_tetromino.sprite)
            self.active_tetromino.add(self.tetromino_queue.get())
            self.tetromino_queue.put(Tetromino(choice(['I', 'J', 'L', 'O', 'S', 'T', 'Z']),
                                               self.start_x, self.start_y, self.play_area.cell_size))

    def update_array_backed_play_grid(self):
        # Calculate what row and column each block would be in to update the cell's status in the play grid.
        for block in self.active_tetromino.sprite.block_group:
            row_pos = (block.screen_y_pos - self.play_area.rect.y + self.play_area.margin) // \
                      self.play_area.cell_size
            column_pos = (block.screen_x_pos - self.play_area.rect.x) // self.play_area.cell_size
            self.play_grid[row_pos][column_pos] = block

    def full_row_handler(self):
        number_of_full_rows = 0
        last_full_row_grid_index = -1
        last_full_row_y_pos = None

        for row in range(self.play_area.rows):
            occupied_cell_count = 0
            for column in range(self.play_area.columns):
                # If a cell doesn't hold a zero then there is a block occupying that cell.
                if self.play_grid[row][column] != 0:
                    occupied_cell_count += 1

            # All columns with an occupied cell means a full row of blocks exists.
            if occupied_cell_count == self.play_area.columns:
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
        for index in range(self.play_area.columns):
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
            if index == self.play_area.columns - 1:
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

        for column in range(self.play_area.columns):
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
            bg_image = pygame.image.load(os.path.join('assets', 'abstract_pixel_rain_background.jpg')).convert_alpha()
            scaled_bg_image = pygame.transform.scale(bg_image, (self.window.get_width(), self.window.get_height()))
            bg = pygame.Surface((self.window.get_width(), self.window.get_height()))
            bg.blit(scaled_bg_image, (0, 0))
            return bg

        def score_surface():
            score_font = pygame.font.SysFont('comicsans', int(self.window.get_height() * 0.06))
            score_label = score_font.render(f"Score: {self.score}", True, (0, 255, 0))
            score_surf = pygame.Surface((score_label.get_width() + 10, score_label.get_height()))  # 10 pixel padding
            pygame.draw.rect(score_surf, (0, 255, 255), score_surf.get_rect(), 1)
            score_surf.blit(score_label, (5, -5))
            return score_surf

        def controls_surface():
            controls_label_font = pygame.font.SysFont('comicsans', int(self.window.get_height() * 0.03))
            left_arrow_label = controls_label_font.render('Left arrow = move left', True, (255, 255, 255))
            right_arrow_label = controls_label_font.render('Right arrow = move right', True, (255, 255, 255))
            spacebar_label = controls_label_font.render('Spacebar = rotate', True, (255, 255, 255))

            controls_label_list = (left_arrow_label, right_arrow_label, spacebar_label)
            greatest_label_width = 0
            for label in controls_label_list:
                if label.get_width() > greatest_label_width:
                    greatest_label_width = label.get_width()

            controls_surf = pygame.Surface((greatest_label_width + 10,  # 10 pixel padding
                                            (spacebar_label.get_height() * 3) + (self.window.get_height() * 0.03) + 10))
            pygame.draw.rect(controls_surf, (0, 255, 255), controls_surf.get_rect(), 1)

            controls_surf.blit(left_arrow_label, (5, 5))
            controls_surf.blit(right_arrow_label, (5, (self.window.get_height() * 0.01) + right_arrow_label.get_height() + 5))
            controls_surf.blit(spacebar_label, (5, (self.window.get_height() * 0.06) + spacebar_label.get_height() + 5))
            return controls_surf

        def tetromino_queue_surface(queued_tetromino):
            # Use 10 pixel for padding.
            queue_surf = pygame.Surface((self.play_area.cell_size * 3 + 10, self.play_area.cell_size * 4 + 10))
            pygame.draw.rect(queue_surf, (255, 0, 255), queue_surf.get_rect(), 1)

            queue_surf.blit(queued_tetromino.image,
                            ((queue_surf.get_width() // 2) - (queued_tetromino.rect.width // 2),
                             (queue_surf.get_height() // 2) - (queued_tetromino.rect.height // 2)))
            return queue_surf

        self.window.blit(game_bg(), (0, 0))
        self.window.blit(self.play_area.image, (self.play_area.rect.x, self.play_area.rect.y))

        self.window.blit(controls_surface(), (10, self.window.get_height() - controls_surface().get_height() - 10))
        self.window.blit(score_surface(), ((self.window.get_width() - score_surface().get_width() - 10), 10))

        for index, tetromino in enumerate(self.tetromino_queue.queue):
            height_offset = self.play_area.rect.top + ((self.play_area.cell_size * 4 + (self.window.get_height() * 0.0235)) * index)
            self.window.blit(tetromino_queue_surface(tetromino), (self.play_area.rect.right + 10, height_offset))

        # Draws a visual representation of the array-backed grid.
        # for row in range(1, self.play_area_rows):
        #     pygame.draw.line(self.play_area, 'red', (0, self.cell_size * row), (self.play_area_rect.width,
        #                                                                         (self.cell_size * row)))
        #     for column in range(1, self.play_area_columns):
        #         pygame.draw.line(self.play_area, 'red', (self.cell_size * column + 2, 0),
        #                          ((self.cell_size * column), self.play_area_rect.height))

    def run(self):
        self.allow_movement_check()
        self.player_input_handler()
        self.full_row_handler()

        # The order of the drawing on screen matters and the background is always first. The drawing of the background
        # every frame is a way to clear the screen of the previous frame.  This allows the imitation of movement on the
        # screen by drawing an object in a slightly new position compared to its previous position.  An example in this
        # game is the falling of a tetromino from the top to the bottom of the play area.
        self.draw_game_window()
        self.active_tetromino.draw(self.window)
        self.tetromino_on_board.draw(self.window)
