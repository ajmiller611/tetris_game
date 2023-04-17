import pygame
import block as bl


class Tetromino(pygame.sprite.Sprite):
    def __init__(self, shape, x, y, block_size):
        super().__init__()  # Initialize the Sprite parent class

        self.tetromino_dict = {
            'I': ['x',
                  'x',
                  'x',
                  'x'],
            'L': ['x ',
                  'x ',
                  'xx'],
            'J': [' x',
                  ' x',
                  'xx'],
            'O': ['xx',
                  'xx'],
            'S': [' xx',
                  'xx '],
            'T': ['xxx',
                  ' x '],
            'Z': ['xx ',
                  ' xx']}

        self.shape = shape
        self.color = self.get_color()
        self.block_size = block_size
        self.block_group = pygame.sprite.Group()
        self.image = self.create_tetromino(0, 0)
        self.rect = self.image.get_rect(topleft=(0, 0))
        # Tetromino position and the block's screen positional data needs to be updated together to avoid inconsistency.
        self.set_rect_x(x)
        # Starting y position will be on top of the play area.
        self.set_rect_y(y - self.rect.height)
        self.mask = pygame.mask.from_surface(self.image)

    def get_color(self):
        color_dict = {
            'I': (4, 252, 252),
            'L': (255, 128, 0),
            'J': (0, 0, 255),
            'O': (255, 255, 0),
            'S': (0, 255, 0),
            'T': (255, 0, 255),
            'Z': (255, 0, 0)}

        for key in color_dict:
            if key == self.shape:
                return color_dict[key]

    def create_tetromino(self, x_start, y_start):
        """
            Arranges 4 square blocks in the shape needed for the tetromino. Assigns them to a sprite group.
            Creates a surface with transparency and draws the arranged blocks onto the surface to create the
            tetromino.
        """
        for row_index, row in enumerate(self.tetromino_dict[self.shape]):
            for col_index, col in enumerate(row):
                if col == 'x':
                    x = x_start + col_index * self.block_size
                    y = y_start + row_index * self.block_size
                    block = bl.Block(self, self.block_size, self.color, x, y)
                    self.block_group.add(block)
                width = (col_index + 1) * self.block_size
                height = (row_index + 1) * self.block_size
        tetromino_surface = pygame.surface.Surface((width, height))
        tetromino_surface.fill((255, 255, 255))
        tetromino_surface.set_colorkey((255, 255, 255))
        self.block_group.draw(tetromino_surface)
        return tetromino_surface

    def condense_or_separate(self):
        def create_new_tetromino_surface(height):
            new_surface = pygame.surface.Surface((self.rect.width, height))
            new_surface.fill((255, 255, 255))
            new_surface.set_colorkey((255, 255, 255))
            return new_surface

        def create_partial_tetromino(bottom_block_group):
            # Find which blocks are in both groups to remove them from the original tetromino's block group.
            for blocks in self.block_group:
                for bottom_block in bottom_block_group:
                    if bottom_block.rect == blocks.rect:
                        self.block_group.remove(bottom_block)

            # An iteration through the block group is done to find the top block.  To avoid creating multiple loops,
            # the creation of the new tetromino object is with its x and y coordinates at zero.  The tetromino can then
            # get its x and y coordinates updated to the top block by the end of the iteration through the block group.
            new_partial_tetromino = Tetromino('I', 0, 0, self.block_size)

            # pygame.sprite.Group isn't subscriptable so get the list of sprites from the sprites() method to get the
            # first block in the group.
            top_positional_block = bottom_block_group.sprites()[0]
            for index, block in enumerate(bottom_block_group):
                # The smallest y coordinate will be the top block of the tetromino.
                if block.rect.y < top_positional_block.rect.y:
                    top_positional_block = block

                # The top block is not always in the top left corner of the tetromino.  The rect x of the old tetromino
                # object will also be the rect x of the new tetromino since the placing of graphical objects is drawn
                # from the top left.  The block's tetromino reference still contains the old tetromino so its rect x is
                # accessed through this reference.
                new_partial_tetromino.rect.x = top_positional_block.tetromino.rect.x

                # The block's tetromino reference can't be used for the y coordinate because it has been altered to
                # hold the positional data for the other separated part. The top block's screen y position will always
                # be the y position for the new tetromino since it becomes the top block in the new tetromino.
                new_partial_tetromino.rect.y = top_positional_block.screen_y_pos

                # For both cases of the middle block being destroyed of the 'I' tetromino, selecting the separated
                # one block for the new object keeps consistency.  The separated block's y coordinate to be used for the
                # drawing on the tetromino's surface now needs to start at zero.  Even if there were more than one block
                # to be added, multiplying the block size by the index of the enumerated block group would place each
                # block in the correct y position for the tetromino's surface.
                if block.tetromino.shape == 'I':
                    block.rect.y = new_partial_tetromino.block_size * index

                # Update the reference to which tetromino object this block belongs to.
                block.tetromino = new_partial_tetromino

            # Create a surface for the newly separated part that will always be the height of one block.  Since in all
            # cases of a tetromino being separated, there will be at least one part that is only one block high.
            new_partial_tetromino.image = create_new_tetromino_surface(self.block_size)

            # Update the rect to the rect of newly created surface.
            new_partial_tetromino.rect = new_partial_tetromino.image.get_rect(topleft=(new_partial_tetromino.rect.x,
                                                                                       new_partial_tetromino.rect.y))

            # Add the blocks that are to be a part of this separated tetromino object.
            new_partial_tetromino.block_group = pygame.sprite.Group(bottom_block_group)

            # Draw the blocks onto the new surface
            new_partial_tetromino.block_group.draw(new_partial_tetromino.image)

            # Set up a mask for collision detection
            new_partial_tetromino.mask = pygame.mask.from_surface(new_partial_tetromino.image)
            return new_partial_tetromino

        # Find the lowest and highest y values of the blocks that remain in the tetromino to use as a way to find the
        # placement of the destroyed block.  The place where the break happens determines the logic to condense or
        # separate the tetromino.
        lowest_y_value = self.rect.height
        highest_y_value = 0
        for block in self.block_group:
            if block.rect.y < lowest_y_value:
                lowest_y_value = block.rect.y
            if block.rect.y > highest_y_value:
                highest_y_value = block.rect.y

        if self.rect.height // self.block_size == 2:
            if highest_y_value == self.rect.height - self.block_size:  # Top destroyed
                # Create a new surface that's height is one block size smaller.
                self.image = create_new_tetromino_surface(self.rect.height - self.block_size)

                # Since the top is destroyed, the rect y coordinate needs to be moved down by a block size.
                self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y + self.block_size))

                # The block's y coordinate also needs to moved up on the tetromino surface since it is being condensed.
                for block in self.block_group:
                    block.rect.y -= self.block_size
                self.block_group.draw(self.image)
                self.mask = pygame.mask.from_surface(self.image)

            elif lowest_y_value == 0:  # Bottom destroyed
                # Create a new surface with a height is one block size smaller.
                self.image = create_new_tetromino_surface(self.rect.height - self.block_size)
                self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
                self.block_group.draw(self.image)
                self.mask = pygame.mask.from_surface(self.image)

        elif self.rect.height // self.block_size == 3 or self.rect.height // self.block_size == 4:
            if lowest_y_value == 0 and highest_y_value == self.rect.height - self.block_size:  # Middle block destroyed
                for block_outer_loop in self.block_group:
                    # If the second block's y coordinate exists in the block group then the third block from the top
                    # was destroyed in an 'I' tetromino. The second block's y coordinate would be the same as the block
                    # size.
                    if block_outer_loop.rect.y == self.block_size:
                        # The current tetromino object can be used for the separated top part's object.
                        # The highest y value will be the y value of the bottom block's top.  By subtracting the block
                        # size from the bottom block's top, the height of the remaining blocks is found for the new
                        # surface.
                        self.image = create_new_tetromino_surface(highest_y_value - self.block_size)

                        # The top part will have the same x and y as the original tetromino object.
                        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))

                        # Put the blocks that are to be a part of the separated bottom part into a temporary group.
                        temp_block_group = pygame.sprite.Group()
                        for block_inner_loop in self.block_group:
                            # The bottom block's y value is the highest y value and can be added to the temporary group.
                            if block_inner_loop.rect.y == highest_y_value:
                                temp_block_group.add(block_inner_loop)

                        # Create a new tetromino object for the separated bottom part.
                        partial_tetromino = create_partial_tetromino(temp_block_group)

                        # Clear the temporary group so the blocks will only belong to the tetromino block group.
                        temp_block_group.empty()
                        break

                    # If the third block's y coordinate exists in the block group then the second block from the top was
                    # destroyed.  This scenario happens for the three block high tetrominos and the 'I' tetromino.
                    elif block_outer_loop.rect.y == self.block_size * 2:

                        # Use the current tetromino object for the separated bottom part since it will be the part
                        # that has two blocks in the case of an 'I' tetromino.  By choosing the side with more blocks,
                        # the lesser amount of data would need to be updated therefore less chance of errors occurring.
                        # Since the other types of tetrominos that would trigger this condition are three blocks high,
                        # both separated parts are one block high.  There is no significant difference between the
                        # choice of sides in this case.
                        self.image = create_new_tetromino_surface(highest_y_value - self.block_size)

                        # The separated bottom part y coordinate starts at the third block from the top so adding two
                        # times the block size would get the y coordinate of the third block. This sets the rect
                        # y coordinate to the correct position for its top left corner.
                        self.rect = self.image.get_rect(topleft=(self.rect.x,
                                                                 self.rect.y + (self.block_size * 2)))

                        temp_block_group = pygame.sprite.Group()
                        for block_inner_loop in self.block_group:

                            # A block with the y coordinate of zero is the block at the top. This is the block to be
                            # separated and put into the new object since it is the part that contains one block.
                            if block_inner_loop.rect.y == 0:
                                temp_block_group.add(block_inner_loop)

                            # A block with a y coordinate of two times the size(the case for a three block high
                            # tetromino) or three times the size(the case of an 'I' tetromino) needs its y coordinate
                            # moved up on the tetromino's surface since the size of the surface has changed.
                            if block_inner_loop.rect.y == self.block_size * 2 or \
                                    block_inner_loop.rect.y == self.block_size * 3:
                                block_inner_loop.rect.y -= self.block_size * 2

                        # Create a new tetromino object for the separated top part.
                        partial_tetromino = create_partial_tetromino(temp_block_group)
                        temp_block_group.empty()
                        break

                # Draw the blocks remaining in the current tetromino's block group after the separating has occurred.
                self.block_group.draw(self.image)

                # Update the mask to the new image for collision detection.
                self.mask = pygame.mask.from_surface(self.image)

                # Return the new tetromino object to be added to the tetromino group that holds the tetrominos currently
                # on the play area.
                return partial_tetromino

            # When the highest y value in the remaining blocks is not the y value of the last block in the tetromino,
            # the bottom blocks were destroyed and the tetromino needs condensed.
            elif highest_y_value != self.rect.height - self.block_size:
                # Create a new surface that's height is one block size smaller.
                self.image = create_new_tetromino_surface(self.rect.height - self.block_size)
                self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
                self.block_group.draw(self.image)
                self.mask = pygame.mask.from_surface(self.image)

            # When the lowest y value is not zero, then the top blocks were destroyed and the tetromino needs condensed.
            elif lowest_y_value != 0:
                # Create a new surface that's height is one block size smaller.
                self.image = create_new_tetromino_surface(self.rect.height - self.block_size)

                # Since the top of the tetromino is destroyed, the y coordinate needs to be moved down the size of a
                # block.
                self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y + self.block_size))

                # The blocks y coordinate also needs to moved up on the tetromino surface.
                for block in self.block_group:
                    block.rect.y -= self.block_size

                self.block_group.draw(self.image)
                self.mask = pygame.mask.from_surface(self.image)

    def set_rect_x(self, x):
        """
            When setting the rect's x coordinate, the blocks' x coordinates needs to be updated as well.
            Since the blocks are drawn on their own surface, their rect.x attribute does not represent their x position
            on the display surface. Calculate the difference between the new and current x position to adjust the
            blocks' screen's x position attribute.
        """
        x_difference = x - self.rect.x
        self.rect.x = x
        for block in self.block_group:
            block.screen_x_pos += x_difference

    def set_rect_y(self, y):
        """
            When setting the rect's y coordinate, the blocks' y coordinates needs to be updated as well.
            Since the blocks are drawn on their own surface, their rect.x attribute does not represent their y position
            on the display surface. Calculate the difference between the new and current y position to adjust the
            blocks' screen's y position attribute.
        """
        y_difference = y - self.rect.y
        self.rect.y = y
        for block in self.block_group:
            block.screen_y_pos += y_difference

    def move(self, x_change, y_change):
        """
            Move the tetromino x and y coordinates by the passed value. The blocks' x and y position needs to be changed
            as well to keep their positional data accurate.
        """
        self.rect.x += x_change
        self.rect.y += y_change
        for block in self.block_group:
            block.screen_x_pos += x_change
            block.screen_y_pos += y_change

    def rotate(self, counterclockwise=True):
        if not self.shape == 'O':
            # Save the tetromino's current x and y position.
            original_x_pos = self.rect.x
            original_y_pos = self.rect.y

            # Rotate the tetromino surface by indicated direction.
            if counterclockwise:
                self.image = pygame.transform.rotate(self.image, 90)
            else:
                self.image = pygame.transform.rotate(self.image, -90)
            self.rect = self.image.get_rect(topleft=(original_x_pos, original_y_pos))
            self.mask = pygame.mask.from_surface(self.image)

            # Update the position of the blocks.
            for block in self.block_group:
                # Pivot around the tetromino top left corner.  The y coordinate is negative for the calculation to be
                # done in the Cartesian coordinate system.
                pivot_point = (self.rect.x, -self.rect.y)

                # The top right point of the block will become the top left point after rotation. That is the only point
                # that needs calculated since graphical objects are drawn from the top left corner.
                top_right_point = (block.screen_x_pos + block.rect.width, -block.screen_y_pos)

                # Translate the point to where it would be if the pivot point was the origin.
                top_right_point_translated = (top_right_point[0] - pivot_point[0],
                                              top_right_point[1] - pivot_point[1])

                if counterclockwise:
                    # 90-degree couterclockwise rotation rule is (x,y) becomes (-y,x).
                    top_right_point_rotated = (-top_right_point_translated[1],
                                               top_right_point_translated[0])
                else:
                    # 90-degree clockwise rotation rule is (x,y) becomes (y,-x).
                    top_right_point_rotated = (top_right_point_translated[1],
                                               -top_right_point_translated[0])

                # Translate the point back to the pivot point and the point is now the top left point of the block.
                now_top_left_point_translated_back = (top_right_point_rotated[0] + pivot_point[0],
                                                      top_right_point_rotated[1] + pivot_point[1])

                # Shift the blocks by the tetromino's height to put the tetromino back in its original height
                # position so the rotation appears to have happened in place.
                shifted_top_left_point = (now_top_left_point_translated_back[0],
                                          abs(now_top_left_point_translated_back[1] - self.rect.height))

                # Update the blocks coordinates on the main display surface.
                block.screen_x_pos = shifted_top_left_point[0]
                block.screen_y_pos = shifted_top_left_point[1]

                # The block's rect coordinates are in reference to the surface created in the Tetromino class that
                # contains all the drawn blocks.  The top left corner of that surface can be treated as the origin in
                # the Cartesian coordinate system.  A modified 90-degree counterclockwise rotation rule(using positive
                # y instead of negative) is applied to get the rotated coordinate of the block's top right coordinate.
                # After rotation, the top right coordinate becomes the top left coordinate.  A shift of the y coordinate
                # by the height of the tetromino puts the coordinate back in the place it would be on the tetromino's
                # surface.
                top_right_x = block.rect.x + block.rect.width
                block.rect.x = block.rect.y
                block.rect.y = abs(top_right_x - self.rect.height)