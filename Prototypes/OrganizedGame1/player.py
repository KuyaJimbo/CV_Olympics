import pygame
import time
import random

# SPIKER_RECT class
class SPIKER_RECT(pygame.sprite.Sprite):
    def __init__(self, y_position, sideinfo):
        super().__init__()
        self.image = pygame.Surface((30//4, 20*2))
        self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect()
        self.rect.center = (1000 // 2, y_position)
        self.stunned = False
        self.stun_start_time = 0
        self.original_position = self.rect.center
        self.is_jumping = False
        self.jump_velocity = 8  # Add a jump velocity
        self.jump_gravity = 0.5  # Gravity for the jump
        self.sideinfo = sideinfo
        self.stuntime = 1
        self.canSpike = False
        self.aiming = ""
        self.speed = 5

    def move(self, ball):
        