import pygame


class Block(pygame.sprite.Sprite):
    def __init__(self, tetromino, size, color, x, y):
        super().__init__()
        self.tetromino = tetromino
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        # Create a black outline around the block.
        pygame.draw.rect(self.image, 'black', self.image.get_rect(), 1)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.screen_x_pos = x
        self.screen_y_pos = y
