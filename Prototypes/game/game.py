import pygame
import cv2
import numpy as np
from Jump_BlockX import PoseTracker

class VolleyballPlayer(pygame.sprite.Sprite):
    def __init__(self, pose_tracker, camera_index=0, screen_width=800):
        """Initialize player with pose tracking."""
        super().__init__()
        
        # Camera and pose tracking
        self.pose_tracker = pose_tracker
        self.camera = cv2.VideoCapture(camera_index)
        
        # Player attributes
        self.screen_width = screen_width
        self.jumping = False
        self.jump_height = 100
        self.jump_velocity = 10
        self.arm_position = "beside_body"
        
        # Sprite setup
        self.image = pygame.Surface((50, 100))
        self.image.fill((0, 120, 255))  # Blue player
        self.rect = self.image.get_rect()
        self.rect.bottom = pygame.display.get_surface().get_height()
        self.rect.centerx = screen_width // 2

    def update(self):
        """Update player position and state based on camera input."""
        success, frame = self.camera.read()
        if not success:
            return

        # Flip frame horizontally
        frame = cv2.flip(frame, 1)

        landmarks = self.pose_tracker.process_frame(frame)
        if not landmarks:
            return

        # Jump detection
        if self.pose_tracker.detect_jump(landmarks):
            self.jump()

        # Arm position
        self.arm_position = self.pose_tracker.get_arm_position(landmarks)

        # Horizontal movement
        nose_x = self.pose_tracker.get_horizontal_position(landmarks)
        self.rect.centerx = int((1 - nose_x) * self.screen_width)

        # Jump physics
        if self.jumping:
            self.jump_velocity -= 1
            self.rect.y -= self.jump_velocity
            
            # Reset when landing
            if self.rect.bottom >= pygame.display.get_surface().get_height():
                self.rect.bottom = pygame.display.get_surface().get_height()
                self.jumping = False
                self.jump_velocity = 10

    def jump(self):
        """Initiate jump if not already jumping."""
        if not self.jumping:
            self.jumping = True
            self.jump_velocity = 15

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Pose-Controlled Volleyball")
    clock = pygame.time.Clock()

    pose_tracker = PoseTracker()
    player = VolleyballPlayer(pose_tracker)
    all_sprites = pygame.sprite.Group(player)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update
        all_sprites.update()

        # Draw
        screen.fill((255, 255, 255))  # White background
        all_sprites.draw(screen)
        
        # Display arm position
        font = pygame.font.Font(None, 36)
        arm_text = font.render(f"Arm: {player.arm_position}", True, (0, 0, 0))
        screen.blit(arm_text, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()