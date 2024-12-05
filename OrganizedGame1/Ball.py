import pygame
import random
import time

# Ball class
class Ball(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((10 * 2, 10 * 2))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.center = (1000 // 2, 600 // 2)
        self.y_velocity = 0
        self.x_velocity = 0
        self.y_position = self.rect.centery
        self.sideinfo = 'lower'  # 'upper' or 'lower' or 'spiker'
        self.bouncing = False
        self.gravity = 0.3  # Gravity force for ball falling
        self.jump_velocity = -5  # Velocity for ball's jump upwards

    def move_y(self):
        """Move the ball vertically under the influence of gravity and upwards when bouncing."""
        if not self.bouncing:
            self.rect.centerx += self.x_velocity
            self.y_velocity += self.gravity
            self.rect.centery += self.y_velocity

            # Prevent the ball from falling below the screen
            if self.rect.bottom >= 600:
                self.rect.bottom = 600
                self.y_velocity = 0

        else:
            self.y_velocity = self.jump_velocity
            self.rect.centery += self.y_velocity
            self.rect.centerx += self.x_velocity

            # Bounce back down when reaching max height
            if self.rect.centery <= 100:  # Max height is 100 pixels from the top
                self.bouncing = False

    def collide(self, npc_rects):
        """Check if the ball collides with the NPC rectangles."""
        for npc in npc_rects:
            if self.rect.colliderect(npc.rect) and not npc.stunned and self.y_velocity > 0:
                
                self.sideinfo = npc.sideinfo

                npc.stunned = True
                npc.stun_start_time = time.time()
                if npc.sideinfo == 'spiker':
                    if npc.aiming == 'left':
                        self.x_velocity = -5
                    else:
                        self.x_velocity = 5
                    return True
                else:
                    self.bouncing = True  # Make the ball bounce upwards
                    # if ball is on left side, give it a random x velocity to the right (1-3)
                    if self.rect.centerx < 1000 // 2:
                        self.x_velocity = random.randint(2, 4)
                    # if ball is on right side, give it a random x velocity to the left (-3 to -1)
                    else:
                        self.x_velocity = random.randint(-4, -2)
                    # Reverse the ball's Y velocity to bounce it upwards
                    return True
        return False