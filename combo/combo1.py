import pygame
import sys
import time
import random

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
GRID_INTERVAL = 50
PLAYER_SIZE = 32
JUMP_FACTOR = 15
GROUND_HEIGHT = 200
BALL_RADIUS = 10
RECT_WIDTH = 30
RECT_HEIGHT = 20
SPEED = 5
GRAVITY = 0.3
JUMP_VELOCITY = -5

# Colors
GRAY = (232, 230, 223)
WHITE = (255, 255, 255)
ORANGE = (255, 143, 51)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

# Load Player Images
player_images = {
    "B_Idle": pygame.image.load("B_Idle.png"),
    "B_Bump": pygame.image.load("B_Bump.png"),
    "B_KneesBent": pygame.image.load("B_KneesBent.png"),
    "B_LeftBlock": pygame.image.load("B_LeftBlock.png"),
    "B_RightBlock": pygame.image.load("B_RightBlock.png"),
    "B_MiddleBlock": pygame.image.load("B_MiddleBlock.png"),
    "B_SplitBlock": pygame.image.load("B_SplitBlock.png"),
}

opponent_images = {
    "S_Idle" : pygame.image.load("S_Idle.png"),
    "S_Bump" : pygame.image.load("S_Bump.png"),
    "S_KneesBent" : pygame.image.load("S_KneesBent.png"),
    "S_LeftPrimed" : pygame.image.load("S_LeftPrimed.png"),
    "S_LeftSpike" : pygame.image.load("S_LeftSpike.png"),
    "S_RightPrimed" : pygame.image.load("S_RightPrimed.png"),
    "S_RightSpike" : pygame.image.load("S_RightSpike.png"),
}

volleyball_bg_images = {
    "Net" : pygame.image.load("VB_BG_Net.png"),
    "Floor" : pygame.image.load("VB_BG_Floor.png"),
}

# Increase scale of background images
new_VB_BG_images = {key: pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT)) for key, img in volleyball_bg_images.items()}

# Scale player images to 32x32
player_images = {key: pygame.transform.scale(img, (PLAYER_SIZE, PLAYER_SIZE)) for key, img in player_images.items()}

# scale opponent images up by a factor of 5
opponent_images = {key: pygame.transform.scale(img, (PLAYER_SIZE * 5, PLAYER_SIZE * 5)) for key, img in opponent_images.items()}
player_images = {key: pygame.transform.scale(img, (PLAYER_SIZE * 5, PLAYER_SIZE * 5)) for key, img in player_images.items()}

# Player Class
class Player:
    def __init__(self):
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - PLAYER_SIZE // 2, SCREEN_HEIGHT - GROUND_HEIGHT, PLAYER_SIZE, PLAYER_SIZE)
        self.image = player_images["B_Idle"]
        self.velocity_y = 0
        self.is_jumping = False
        self.BLOCKTYPE = "None"
        self.BLOCKBOX = pygame.Rect(self.rect.x - PLAYER_SIZE, self.rect.y - PLAYER_SIZE, PLAYER_SIZE * 3, PLAYER_SIZE * 3)

    def move(self, dx):
        self.rect.x += dx
        self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - PLAYER_SIZE))

    def jump_by_factor(self, factor):
        if not self.is_jumping:
            self.velocity_y = -factor
            self.is_jumping = True

    def update(self):
        # Apply gravity
        self.velocity_y += 0.5
        self.rect.y += self.velocity_y

        # Check ground collision
        if self.rect.y >= SCREEN_HEIGHT - GROUND_HEIGHT:
            self.rect.y = SCREEN_HEIGHT - GROUND_HEIGHT
            self.is_jumping = False
            self.velocity_y = 0

        # Update block box
        if self.BLOCKTYPE == "Left":
            self.BLOCKBOX = pygame.Rect(self.rect.x - PLAYER_SIZE - 30, self.rect.y - PLAYER_SIZE - 50, PLAYER_SIZE * 3, PLAYER_SIZE * 5)
        elif self.BLOCKTYPE == "Right":
            self.BLOCKBOX = pygame.Rect(self.rect.x - PLAYER_SIZE + 40, self.rect.y - PLAYER_SIZE - 50, PLAYER_SIZE * 3, PLAYER_SIZE * 5)
        elif self.BLOCKTYPE == "Middle":
            self.BLOCKBOX = pygame.Rect(self.rect.x - PLAYER_SIZE + 5, self.rect.y - PLAYER_SIZE - 50, PLAYER_SIZE * 3, PLAYER_SIZE * 5)
        elif self.BLOCKTYPE == "Split":
            self.BLOCKBOX = pygame.Rect(self.rect.x - PLAYER_SIZE - 30, self.rect.y - PLAYER_SIZE - 20, PLAYER_SIZE * 5, PLAYER_SIZE * 4)

    def set_pose(self, pose):
        self.image = player_images.get(pose, player_images["B_Idle"])

    def draw(self, surface):
        surface.blit(pygame.transform.scale(self.image, (PLAYER_SIZE * 5, PLAYER_SIZE * 5)), (self.rect.x - PLAYER_SIZE * 2, self.rect.y - PLAYER_SIZE * 2))
    
    def draw_blockbox(self, surface):
        pygame.draw.rect(surface, WHITE, self.BLOCKBOX, 2)

# Ball class
class Ball(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((BALL_RADIUS * 2, BALL_RADIUS * 2))
        self.image.fill(GRAY)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.y_velocity = 0
        self.x_velocity = 0
        self.y_position = self.rect.centery
        self.sideinfo = 'lower'
        self.bouncing = False

    def move_y(self):
        if not self.bouncing:
            self.rect.centerx += self.x_velocity
            self.y_velocity += GRAVITY
            self.rect.centery += self.y_velocity

            # if the ball falls below the screen, reset its position and velocity
            if self.rect.bottom >= SCREEN_HEIGHT:
                self.rect.bottom = SCREEN_HEIGHT
                self.y_velocity = 0

        else:
            self.y_velocity = JUMP_VELOCITY
            self.rect.centery += self.y_velocity
            self.rect.centerx += self.x_velocity

            if self.rect.centery <= 100:
                self.bouncing = False

    def collide(self, npc_rects):
        """Check if the ball collides with the NPC rectangles."""
        for npc in npc_rects:
            if self.rect.colliderect(npc.rect) and not npc.stunned and self.y_velocity > 0:
                # if this rectangle is the upper npc and the ball side info is "spiker", continue
                if npc.sideinfo == 'upper' and self.sideinfo == 'spiker':
                    continue
                
                self.sideinfo = npc.sideinfo

                npc.stunned = True
                npc.stun_start_time = time.time()
                if npc.sideinfo == 'spiker':
                    if npc.aiming == 'left':
                        self.x_velocity = -5
                        npc.image = opponent_images["S_LeftSpike"]
                    else:
                        self.x_velocity = 5
                        npc.image = opponent_images["S_RightSpike"]
                    return True
                else:
                    self.bouncing = True  # Make the ball bounce upwards
                    # if ball is on left side, give it a random x velocity to the right (1-3)
                    if self.rect.centerx < SCREEN_WIDTH // 2:
                        self.x_velocity = random.randint(2, 4)
                    # if ball is on right side, give it a random x velocity to the left (-3 to -1)
                    else:
                        self.x_velocity = random.randint(-4, -2)
                    # Reverse the ball's Y velocity to bounce it upwards
                    return True
        return False
    
    def check_player_block(self, player):
        if player.BLOCKTYPE != "None" and self.rect.colliderect(player.BLOCKBOX):
            # check if the ball is above y = 200 and after the spike
            if self.rect.centery < 200 and self.sideinfo == 'spiker':
                return True
        return False

# SPIKER_RECT class
class SPIKER_RECT(pygame.sprite.Sprite):
    def __init__(self, y_position, sideinfo):
        super().__init__()
        self.image = opponent_images["S_Idle"]
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, y_position)
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

    def move(self, ball):
        """Move the SPIKER_RECT to follow the ball horizontally and handle jumping."""
        if not self.stunned:
            # Keep the SPIKER_RECT in line with the ball, but not lower than its original position
            if self.rect.centerx + SPEED < ball.rect.centerx:
                self.rect.centerx += SPEED
            elif self.rect.centerx - SPEED > ball.rect.centerx:
                self.rect.centerx -= SPEED
            else:
                self.rect.centerx = ball.rect.centerx
            
            # If the SPIKER_RECT is directly under the ball, make it jump when ball is falling
            if (abs(self.rect.centerx - ball.rect.centerx) < 10 and 
                not self.is_jumping and 
                ball.y_velocity > 5 and  # Only jump when ball is falling down
                ball.sideinfo == 'upper'):
                AimOptions = ['left', 'right']
                self.aiming = random.choice(AimOptions)

                # if aiming left, prime the left spike
                if self.aiming == 'left':
                    self.image = opponent_images["S_LeftPrimed"]
                else:
                    self.image = opponent_images["S_RightPrimed"]

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
                    self.image = opponent_images["S_Idle"]
                    self.jump_velocity = 0
        else:
            # Check if the stun duration has passed
            if time.time() - self.stun_start_time >= self.stuntime:
                self.stunned = False
            # allow the spike to fall back to their original position
            if self.rect.centery < self.original_position[1]:
                self.rect.centery += 5
            
# NPC_Rect class
class NPC_Rect(pygame.sprite.Sprite):
    def __init__(self, y_position, sideinfo):
        super().__init__()
        if sideinfo == 'upper':
            self.image = opponent_images["S_Idle"]
        elif sideinfo == 'lower':
            self.image = player_images["B_Idle"]
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, y_position)
        self.stunned = False
        self.stun_start_time = 0
        self.sideinfo = sideinfo
        self.stuntime = 1

    def move_x(self, ball):
        """Move the NPC rectangle to follow the ball horizontally if not stunned."""
        if not self.stunned:
            if self.rect.centerx + SPEED < ball.rect.centerx:
                self.rect.centerx += SPEED
            elif self.rect.centerx - SPEED > ball.rect.centerx:
                self.rect.centerx -= SPEED
            else:
                self.rect.centerx = ball.rect.centerx
        else:
            # Check if the stun duration has passed
            if time.time() - self.stun_start_time >= self.stuntime:
                self.stunned = False

# Main Game Class
class VolleyballGame:
    def __init__(self):
        # Initialize screen
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Volleyball Blocking")

        # Game objects
        self.player = Player()
        self.ball = Ball()
        self.npc_upper = NPC_Rect(SCREEN_HEIGHT // 3 + 100, 'upper')
        self.npc_lower = NPC_Rect(SCREEN_HEIGHT * 2 // 3 + 100, 'lower')
        self.spiker = SPIKER_RECT(SCREEN_HEIGHT // 2 + 50, 'spiker')
        self.npc_rects = [self.npc_upper, self.npc_lower, self.spiker]
        self.clock = pygame.time.Clock()
        self.game_font = pygame.font.Font(None, 100)

        # Game state variables
        self.game_paused = False
        self.kill_block_active = False
        self.kill_block_start_time = 0

    def draw_grid(self):
        for x in range(0, SCREEN_WIDTH, GRID_INTERVAL):
            pygame.draw.line(self.screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, GRID_INTERVAL):
            pygame.draw.line(self.screen, GRAY, (0, y), (SCREEN_WIDTH, y))

    def draw_kill_block_text(self):
        # put a solid white rectangle on the screen with some transparency (50%)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(WHITE)
        self.screen.blit(overlay, (0, 0))
        kill_block_text = self.game_font.render("KILL BLOCK", True, BLACK)
        text_rect = kill_block_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(kill_block_text, text_rect)


    def reset_game(self):
        self.ball.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.ball.y_velocity = 0
        self.ball.x_velocity = 0
        self.game_paused = False
        self.kill_block_active = False
        self.player.BLOCKTYPE = "None"
        self.player.set_pose("B_Idle")

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if self.kill_block_active:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Right click
                        self.reset_game()

            if not self.game_paused:
                # Regular game controls
                keys = pygame.key.get_pressed()

                # Movement
                if keys[pygame.K_a]:
                    self.player.move(-5)
                if keys[pygame.K_d]:
                    self.player.move(5)
                if keys[pygame.K_SPACE]:
                    self.player.jump_by_factor(JUMP_FACTOR)

                # Blocking Poses
                if keys[pygame.K_LEFT] and keys[pygame.K_RIGHT]:
                    self.player.set_pose("B_SplitBlock")
                    self.player.BLOCKTYPE = "Split"
                elif keys[pygame.K_LEFT]:
                    self.player.set_pose("B_LeftBlock")
                    self.player.BLOCKTYPE = "Left"
                elif keys[pygame.K_RIGHT]:
                    self.player.set_pose("B_RightBlock")
                    self.player.BLOCKTYPE = "Right"
                elif keys[pygame.K_UP]:
                    self.player.set_pose("B_MiddleBlock")
                    self.player.BLOCKTYPE = "Middle"
                elif keys[pygame.K_DOWN]:
                    self.player.set_pose("B_KneesBent")
                elif keys[pygame.K_s]:
                    self.player.set_pose("B_Bump")
                else:
                    self.player.set_pose("B_Idle")

                # Update player
                self.player.update()

                # NPC movement
                self.npc_upper.move_x(self.ball)
                self.npc_lower.move_x(self.ball)
                self.spiker.move(self.ball)

                # Ball movement
                self.ball.move_y()
                self.ball.collide(self.npc_rects)

                # Check for kill block
                if self.ball.check_player_block(self.player):
                    self.game_paused = True
                    self.kill_block_active = True
                    self.ball.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                    self.kill_block_start_time = time.time()

            # Draw everything
            self.screen.fill(ORANGE)
            self.draw_grid()
            self.screen.blit(new_VB_BG_images["Floor"], (0, 0))

            # Draw sprites manually
            upper_sprites = pygame.sprite.Group(self.npc_upper, self.spiker)
            upper_sprites.draw(self.screen)
            # if ball is coming downwards and has side info of lower, draw the ball
            if self.ball.y_velocity > 0 and self.ball.sideinfo == 'lower':
                pygame.draw.circle(self.screen, GRAY, self.ball.rect.center, BALL_RADIUS)
                self.screen.blit(new_VB_BG_images["Net"], (0, 0))
                self.player.draw(self.screen)
            # if the ball is coming upwards and has side info of upper, draw the ball
            elif self.ball.y_velocity < 0 and self.ball.sideinfo == 'upper':
                pygame.draw.circle(self.screen, GRAY, self.ball.rect.center, BALL_RADIUS)
                self.screen.blit(new_VB_BG_images["Net"], (0, 0))
                self.player.draw(self.screen)
            else:
                self.screen.blit(new_VB_BG_images["Net"], (0, 0))
                # draw player
                self.player.draw(self.screen)
                pygame.draw.circle(self.screen, GRAY, self.ball.rect.center, BALL_RADIUS)


            
            lower_sprites = pygame.sprite.Group(self.npc_lower)
            lower_sprites.draw(self.screen)
            # self.npc_lower.draw(self.screen)
            

            # Draw block box if any block pose is active
            if self.player.image != player_images["B_Idle"]:
                self.player.draw_blockbox(self.screen)

            # Draw ball
            pygame.draw.circle(self.screen, GRAY, self.ball.rect.center, BALL_RADIUS)

            # Draw kill block text if active
            if self.kill_block_active:
                self.draw_kill_block_text()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

def main():
    game = VolleyballGame()
    game.run()

if __name__ == "__main__":
    main()