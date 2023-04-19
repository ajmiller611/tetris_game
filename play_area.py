import pygame


class PlayArea:
    def __init__(self, display_width, display_height):
        # Since 16:9 aspect ratio is the most common for computer monitors, the width aspect has more flexibility due
        # to having more pixels to work with. This means the decision on appearance gets based off of height first.
        # In this case, the height of the play area takes up 70% of the window's height with 20% of the window above it
        # and 10% below it.
        self.rows = 13
        self.columns = 10
        self.cell_size = round(display_height * 0.7) // self.rows
        self.margin = 4
        surface_width = self.cell_size * self.columns + self.margin
        surface_height = self.cell_size * self.rows + (self.margin // 2)
        self.image = pygame.surface.Surface((surface_width, surface_height))
        self.rect = self.image.get_rect(center=(display_width // 2,
                                                (display_height // 2) + (display_height * 0.05)))

        # Draw an outline around the surface.
        pygame.draw.rect(self.image, (255, 0, 255), self.image.get_rect(), 1)
