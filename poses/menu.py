import pygame
import sys

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 400, 300
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pygame Menu")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (50, 150, 255)

# Font
FONT = pygame.font.Font(None, 40)

# Menu options
options = ["Option A", "Option B", "Option C"]
selected_index = 0

def draw_menu():
    screen.fill(WHITE)
    for i, option in enumerate(options):
        color = BLUE if i == selected_index else BLACK
        text = FONT.render(option, True, color)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 50))
        screen.blit(text, text_rect)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Mouse wheel for scrolling
        elif event.type == pygame.MOUSEWHEEL:
            selected_index -= event.y
            selected_index %= len(options)

        # Left mouse click for selection
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            print(f"{options[selected_index]} was selected")

    draw_menu()
    pygame.display.flip()

pygame.quit()
sys.exit()
