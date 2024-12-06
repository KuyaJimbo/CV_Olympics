import pygame

# Ball class
from Ball import Ball
from NPC_Rect import NPC_Rect
from SPIKER_Rect import SPIKER_RECT

# Initialize Pygame
pygame.init()
# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0,255,0)
# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
# Main game loop
def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Ball and SPIKER RECT')

    # Create ball and SPIKER_RECT
    ball = Ball()
    npc_upper = NPC_Rect(SCREEN_HEIGHT // 4, 'upper')
    npc_lower = NPC_Rect(SCREEN_HEIGHT * 3 // 4, 'lower')
    spiker = SPIKER_RECT(SCREEN_HEIGHT // 2, 'spiker')
    
    npc_rects = [npc_upper, npc_lower, spiker]
    all_sprites = pygame.sprite.Group()
    all_sprites.add(ball, npc_upper, npc_lower, spiker)

    running = True
    clock = pygame.time.Clock()
    
    while running:
        print(ball.sideinfo)
        screen.fill(WHITE)
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Ball movement and collision
        ball.move_y()
        ball.collide(npc_rects)
        
        # NPC movement
        npc_upper.move_x(ball)
        npc_lower.move_x(ball)
        
        # SPIKER_RECT movement and collision
        spiker.move(ball, npc_upper)


        # Draw all sprites
        all_sprites.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
