import pygame
import sys
from pose_detection_module import PoseDetector
import cv2
import threading

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
GRID_INTERVAL = 50
PLAYER_SIZE = 32
GROUND_HEIGHT = 200

# Colors
GRAY = (200, 200, 200)
WHITE = (255, 255, 255)
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

# Scale background images
new_VB_BG_images = {key: pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT)) for key, img in volleyball_bg_images.items()}

# Scale player images to 32x32
player_images = {key: pygame.transform.scale(img, (PLAYER_SIZE, PLAYER_SIZE)) for key, img in player_images.items()}

# Pose Detection Setup
pose_detector = PoseDetector()
current_jump_factor = 15  # Default jump factor
current_block_type = None
pose_detection_active = True

def pose_detection_thread():
    global current_jump_factor, current_block_type, pose_detection_active
    cap = cv2.VideoCapture(0)

    with pose_detector.pose as pose:
        while pose_detection_active:
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            # Process image
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = pose.process(image_rgb)

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark

                # Detect jump and block type
                jump_detected, jump_power = pose_detector.detect_jump(landmarks)
                block_type = pose_detector.block_type(landmarks)

                # Update global variables
                if jump_detected:
                    current_jump_factor = jump_power
                current_block_type = block_type

            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

    cap.release()

# Player Class
class Player:
    def __init__(self):
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - PLAYER_SIZE // 2, SCREEN_HEIGHT - GROUND_HEIGHT, PLAYER_SIZE, PLAYER_SIZE)
        self.image = player_images["B_Idle"]
        self.velocity_y = 0
        self.is_jumping = False
        self.current_pose = "B_Idle"

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
        self.current_pose = pose
        self.image = player_images.get(pose, player_images["B_Idle"])

    def draw(self, surface):
        # Increase the scale of the player by a factor of 5
        scaled_image = pygame.transform.scale(self.image, (PLAYER_SIZE * 5, PLAYER_SIZE * 5))
        surface.blit(scaled_image, (self.rect.x - PLAYER_SIZE * 2, self.rect.y - PLAYER_SIZE * 2))

# Draw grid
def draw_grid():
    for x in range(0, SCREEN_WIDTH, GRID_INTERVAL):
        pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, GRID_INTERVAL):
        pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))

# Main game function
def main():
    global pose_detection_active, current_jump_factor, current_block_type

    # Start pose detection in a separate thread
    pose_thread = threading.Thread(target=pose_detection_thread)
    pose_thread.start()

    # Main game setup
    player = Player()
    clock = pygame.time.Clock()

    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise SystemExit

            keys = pygame.key.get_pressed()

            # Movement
            if keys[pygame.K_a]:
                player.move(-5)
            if keys[pygame.K_d]:
                player.move(5)

            # Jumping - now using computer vision jump factor
            if keys[pygame.K_SPACE]:
                player.jump_by_factor(current_jump_factor)

            # Blocking Poses - now can be controlled by computer vision
            if current_block_type:
                if current_block_type == "Left Block":
                    player.set_pose("B_LeftBlock")
                elif current_block_type == "Right Block":
                    player.set_pose("B_RightBlock")
                elif current_block_type == "Middle Block":
                    player.set_pose("B_MiddleBlock")
                elif current_block_type == "Split Block":
                    player.set_pose("B_SplitBlock")
            else:
                # Keyboard fallback for blocking poses
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
            screen.blit(new_VB_BG_images["Floor"], (0, 0))
            screen.blit(new_VB_BG_images["Net"], (0, 0))
            player.draw(screen)
            
            # Display current jump factor
            font = pygame.font.Font(None, 36)
            jump_text = font.render(f"Jump Factor: {current_jump_factor}", True, WHITE)
            screen.blit(jump_text, (10, 10))

            pygame.display.flip()
            clock.tick(60)

    except SystemExit:
        # Cleanup
        pose_detection_active = False
        pose_thread.join()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()