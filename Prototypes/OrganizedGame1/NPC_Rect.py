import pygame
import time

# NPC_Rect class
class NPC_Rect(pygame.sprite.Sprite):
    def __init__(self, y_position, sideinfo):
        super().__init__()
        self.image = pygame.Surface((30, 20)) # Change the size of the NPC rectangle
        self.image.fill((0, 0, 255))
        self.rect = self.image.get_rect()
        self.rect.center = (1000 // 2, y_position)
        self.stunned = False
        self.stun_start_time = 0
        self.sideinfo = sideinfo
        self.stuntime = 1
        self.speed = 5

    def move_x(self, ball):
        """Move the NPC rectangle to follow the ball horizontally if not stunned."""
        if not self.stunned:
            if self.rect.centerx + self.speed < ball.rect.centerx:
                self.rect.centerx += self.speed
            elif self.rect.centerx - self.speed > ball.rect.centerx:
                self.rect.centerx -= self.speed
            else:
                self.rect.centerx = ball.rect.centerx
        else:
            # Check if the stun duration has passed
            if time.time() - self.stun_start_time >= self.stuntime:
                self.stunned = False