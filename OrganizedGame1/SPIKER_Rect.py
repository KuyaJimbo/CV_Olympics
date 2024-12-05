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

    def move(self, ball, upper_rect):
        """Move the SPIKER_RECT to follow the ball horizontally and handle jumping."""
        if not self.stunned:
            # Keep the SPIKER_RECT in line with the ball, but not lower than its original position
            if self.rect.centerx + self.speed < ball.rect.centerx:
                self.rect.centerx += self.speed
            elif self.rect.centerx - self.speed > ball.rect.centerx:
                self.rect.centerx -= self.speed
            else:
                self.rect.centerx = ball.rect.centerx
            
            # If the SPIKER_RECT is directly under the ball, make it jump when ball is falling
            if (abs(self.rect.centerx - ball.rect.centerx) < 10 and 
                not self.is_jumping and 
                ball.y_velocity > 5 and  # Only jump when ball is falling down
                ball.sideinfo == 'upper'):
                AimOptions = ['left', 'right']
                self.aiming = random.choice(AimOptions)
                self.canSpike = True
                self.stunned = True
                self.is_jumping = True
                self.jump_velocity = -10  # Initial upward velocity
                self.original_position = self.rect.center
            else:
                self.canSpike = False

            # Handle jumping with gravity
            if self.is_jumping:
                self.rect.centery += self.jump_velocity
                self.jump_velocity += self.jump_gravity

                # Check if jump is complete (return to original position)
                if self.rect.centery >= self.original_position[1]:
                    self.rect.centery = self.original_position[1]
                    self.is_jumping = False
                    self.jump_velocity = 0
        else:
            # Check if the stun duration has passed
            if time.time() - self.stun_start_time >= self.stuntime:
                self.stunned = False
            # allow the spike to fall back to their original position
            if self.rect.centery < self.original_position[1]:
                self.rect.centery += 5