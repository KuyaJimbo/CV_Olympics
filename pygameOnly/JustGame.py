import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
GRID_INTERVAL = 50
PLAYER_SIZE = 32
JUMP_FACTOR = 15
GROUND_HEIGHT = 200

# Colors
GRAY = (200, 200, 200)
WHITE = (255, 255, 255)
# 255, 143, 51 orange
ORANGE = (255, 143, 51)


# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Volleyball Blocking")

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

# increase factor of 5 for volleyball images
new_VB_BG_images = {key: pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT)) for key, img in volleyball_bg_images.items()}

# Scale player images to 32x32
player_images = {key: pygame.transform.scale(img, (PLAYER_SIZE, PLAYER_SIZE)) for key, img in player_images.items()}

# Player Class
class Player:
    def __init__(self):
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - PLAYER_SIZE // 2, SCREEN_HEIGHT - GROUND_HEIGHT, PLAYER_SIZE, PLAYER_SIZE)
        self.image = player_images["B_Idle"]
        self.velocity_y = 0
        self.is_jumping = False

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

    def set_pose(self, pose):
        self.image = player_images.get(pose, player_images["B_Idle"])

    def draw(self, surface):
        # increase the scale of the player by a factor of 5
        surface.blit(pygame.transform.scale(self.image, (PLAYER_SIZE * 5, PLAYER_SIZE * 5)), (self.rect.x - PLAYER_SIZE * 2, self.rect.y - PLAYER_SIZE * 2))
        # surface.blit(self.image, self.rect.topleft)

# Draw grid
def draw_grid():
    for x in range(0, SCREEN_WIDTH, GRID_INTERVAL):
        pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, GRID_INTERVAL):
        pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))

# Main loop
player = Player()
clock = pygame.time.Clock()

while True:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()

    # Movement
    if keys[pygame.K_a]:
        player.move(-5)
    if keys[pygame.K_d]:
        player.move(5)
    if keys[pygame.K_SPACE]:
        player.jump_by_factor(JUMP_FACTOR)

    # Blocking Poses
    if keys[pygame.K_LEFT] and keys[pygame.K_RIGHT]:
        player.set_pose("B_SplitBlock")
    elif keys[pygame.K_LEFT]:
        player.set_pose("B_LeftBlock")
    elif keys[pygame.K_RIGHT]:
        player.set_pose("B_RightBlock")
    elif keys[pygame.K_UP]:
        player.set_pose("B_MiddleBlock")
    elif keys[pygame.K_DOWN]:
        player.set_pose("B_KneesBent")
    elif keys[pygame.K_s]:
        player.set_pose("B_Bump")
    else:
        player.set_pose("B_Idle")

    # Update player
    player.update()

    # Draw everything
    screen.fill(ORANGE)
    draw_grid()
    # draw floor
    screen.blit(new_VB_BG_images["Floor"], (0, 0))
    # draw net
    screen.blit(new_VB_BG_images["Net"], (0, 0))
    player.draw(screen)
    pygame.display.flip()

    clock.tick(60)