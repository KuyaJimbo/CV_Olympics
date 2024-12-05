import pygame
import math

# Initialize Pygame
pygame.init()

# Screen dimensions and grid interval
WIDTH, HEIGHT = 800, 600
GRID_INTERVAL = 40

# Colors
GRAY = (200, 200, 200)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Screen setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Volleyball Blocking")

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Player attributes
player_x = WIDTH // 2
player_y = HEIGHT - 300
player_width = 20
player_height = 100
leg_width = 8
leg_height = 40
arm_width = 8
arm_length = 80
head_radius = 15
velocity = 5
jump_height = 20
is_jumping = False
jump_count = 10
current_pose = "idle"

# Function to draw grid
def draw_grid():
    for x in range(0, WIDTH, GRID_INTERVAL):
        pygame.draw.line(screen, GRAY, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, GRID_INTERVAL):
        pygame.draw.line(screen, GRAY, (0, y), (WIDTH, y))

# Function to draw arms
def draw_arm_rotated(x, y, angle):
    """Draws an arm extending from (x, y) at a given angle in radians."""
    end_x = x + arm_length * math.cos(angle)
    end_y = y - arm_length * math.sin(angle)
    pygame.draw.line(screen, RED, (x, y), (end_x, end_y), arm_width)

# Function to raise arms
def draw_arms_up(x, y):
    pygame.draw.rect(screen, RED, (x - arm_width, y, arm_width * 2, arm_length))

# Function to draw the player
def draw_player(x, y, pose):
 

    # Legs
    left_leg_x = x
    right_leg_x = x + player_width - leg_width
    leg_y = y + player_height
    # Arms
    shoulder_x = x + player_width // 2
    shoulder_y = y

    if pose == "knees_bent":
        pygame.draw.rect(screen, RED, (left_leg_x, leg_y+20, leg_width, leg_height - 20))
        pygame.draw.rect(screen, RED, (right_leg_x, leg_y+20, leg_width, leg_height - 20))
        pygame.draw.circle(screen, RED, (x + player_width // 2, y - head_radius + 40), head_radius)
        pygame.draw.rect(screen, RED, (x, y+40, player_width, player_height-20))
        draw_arm_rotated(shoulder_x, shoulder_y+20, math.radians(290))
        draw_arm_rotated(shoulder_x, shoulder_y+20, math.radians(250))
    else:
        pygame.draw.rect(screen, RED, (left_leg_x, leg_y, leg_width, leg_height))
        pygame.draw.rect(screen, RED, (right_leg_x, leg_y, leg_width, leg_height))
        pygame.draw.circle(screen, RED, (x + player_width // 2, y - head_radius), head_radius)
        pygame.draw.rect(screen, RED, (x, y, player_width, player_height))



        if pose == "left_block":
            # arm_length = 100
            draw_arm_rotated(shoulder_x, shoulder_y, math.radians(135))  # Left upper direction
            draw_arm_rotated(shoulder_x, shoulder_y, math.radians(150))  # Further left upper
        elif pose == "right_block":
            # arm_length = 100
            draw_arm_rotated(shoulder_x, shoulder_y, math.radians(45))  # Right upper direction
            draw_arm_rotated(shoulder_x, shoulder_y, math.radians(30))  # Further right upper
        elif pose == "middle_block":
            draw_arm_rotated(shoulder_x, shoulder_y, math.radians(70))
            draw_arm_rotated(shoulder_x, shoulder_y, math.radians(110))
        elif pose == "split_block":
            draw_arm_rotated(shoulder_x, shoulder_y, math.radians(150))  # Left side
            draw_arm_rotated(shoulder_x, shoulder_y, math.radians(30))  # Right side

# Main game loop
running = True
while running:
    screen.fill(WHITE)
    draw_grid()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Key states
    keys = pygame.key.get_pressed()

    # Movement
    if keys[pygame.K_a]:
        player_x -= velocity
    if keys[pygame.K_d]:
        player_x += velocity

    # Jumping
    if not is_jumping:
        if keys[pygame.K_SPACE]:
            is_jumping = True
    else:
        if jump_count >= -10:
            neg = 1 if jump_count > 0 else -1
            player_y -= (jump_count ** 2) * 0.5 * neg
            jump_count -= 1
        else:
            jump_count = 10
            is_jumping = False

    # Blocking poses
    if keys[pygame.K_LEFT] and keys[pygame.K_RIGHT]:
        current_pose = "split_block"
    elif keys[pygame.K_LEFT]:
        current_pose = "left_block"
    elif keys[pygame.K_RIGHT]:
        current_pose = "right_block"
    elif keys[pygame.K_UP]:
        current_pose = "middle_block"
    elif keys[pygame.K_DOWN]:
        current_pose = "knees_bent"
    else:
        current_pose = "idle"

    # Draw player
    draw_player(player_x, player_y, current_pose)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
