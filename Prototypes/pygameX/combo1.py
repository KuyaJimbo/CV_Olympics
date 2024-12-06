import pygame
import math
import cv2
import mediapipe as mp
import numpy as np
import time

class PoseTracker:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        """Initialize MediaPipe Pose Tracker with configurable confidence levels."""
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=min_detection_confidence, 
            min_tracking_confidence=min_tracking_confidence
        )
        
        # Tracking parameters
        self.baseline_height = 1.0
        self.jump_threshold = 0.15
        self.jump_cooldown = 2
        self.last_jump_time = 0
        self.current_pose = "idle"

    def process_frame(self, image):
        """Process a single video frame for pose detection."""
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image_rgb)
        return results.pose_landmarks.landmark if results.pose_landmarks else None

    def detect_jump(self, landmarks):
        """Determine if a jump occurred by comparing nose positions."""
        current_time = time.time()

        # Check cooldown
        if current_time - self.last_jump_time < self.jump_cooldown:
            return False

        nose_y = landmarks[self.mp_pose.PoseLandmark.NOSE].y
        hip_y = (landmarks[self.mp_pose.PoseLandmark.LEFT_HIP].y + 
                 landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP].y) / 2
        
        # Jump detection based on significant vertical distance
        if nose_y < hip_y - 0.1:
            self.last_jump_time = current_time
            return True

        return False

    def get_blocking_pose(self, landmarks):
        """Determine blocking pose based on hand positions."""
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE]
        left_hand = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST]
        right_hand = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]

        # Determine blocking pose
        if left_hand.y < nose.y and right_hand.y < nose.y:
            return "middle_block"
        elif left_hand.x < nose.x and left_hand.y < left_shoulder.y:
            return "left_block"
        elif right_hand.x > nose.x and right_hand.y < right_shoulder.y:
            return "right_block"
        return "idle"

    def get_horizontal_position(self, landmarks, screen_width):
        """Map horizontal position to screen width."""
        nose_x = landmarks[self.mp_pose.PoseLandmark.NOSE].x
        # Invert x and map to screen width
        return int((1 - nose_x) * screen_width)

def draw_grid(screen, width, height, grid_interval):
    """Draw a grid on the screen."""
    gray = (200, 200, 200)
    for x in range(0, width, grid_interval):
        pygame.draw.line(screen, gray, (x, 0), (x, height))
    for y in range(0, height, grid_interval):
        pygame.draw.line(screen, gray, (0, y), (width, y))

def draw_arm_rotated(screen, x, y, angle, arm_length, arm_width, color):
    """Draws an arm extending from (x, y) at a given angle in radians."""
    end_x = x + arm_length * math.cos(angle)
    end_y = y - arm_length * math.sin(angle)
    pygame.draw.line(screen, color, (x, y), (end_x, end_y), arm_width)

def draw_player(screen, x, y, pose, player_width, player_height, 
                leg_width, leg_height, head_radius, color):
    """Draw the player with different poses."""
    # Legs
    left_leg_x = x
    right_leg_x = x + player_width - leg_width
    leg_y = y + player_height
    # Arms
    shoulder_x = x + player_width // 2
    shoulder_y = y

    if pose == "knees_bent":
        pygame.draw.rect(screen, color, (left_leg_x, leg_y+20, leg_width, leg_height - 20))
        pygame.draw.rect(screen, color, (right_leg_x, leg_y+20, leg_width, leg_height - 20))
        pygame.draw.circle(screen, color, (x + player_width // 2, y - head_radius + 40), head_radius)
        pygame.draw.rect(screen, color, (x, y+40, player_width, player_height-20))
        draw_arm_rotated(screen, shoulder_x, shoulder_y+20, math.radians(290), 80, 8, color)
        draw_arm_rotated(screen, shoulder_x, shoulder_y+20, math.radians(250), 80, 8, color)
    else:
        pygame.draw.rect(screen, color, (left_leg_x, leg_y, leg_width, leg_height))
        pygame.draw.rect(screen, color, (right_leg_x, leg_y, leg_width, leg_height))
        pygame.draw.circle(screen, color, (x + player_width // 2, y - head_radius), head_radius)
        pygame.draw.rect(screen, color, (x, y, player_width, player_height))

        # Blocking poses
        if pose == "left_block":
            draw_arm_rotated(screen, shoulder_x, shoulder_y, math.radians(135), 80, 8, color)
            draw_arm_rotated(screen, shoulder_x, shoulder_y, math.radians(150), 80, 8, color)
        elif pose == "right_block":
            draw_arm_rotated(screen, shoulder_x, shoulder_y, math.radians(45), 80, 8, color)
            draw_arm_rotated(screen, shoulder_x, shoulder_y, math.radians(30), 80, 8, color)
        elif pose == "middle_block":
            draw_arm_rotated(screen, shoulder_x, shoulder_y, math.radians(70), 80, 8, color)
            draw_arm_rotated(screen, shoulder_x, shoulder_y, math.radians(110), 80, 8, color)

def main():
    # Initialize Pygame
    pygame.init()

    # Screen dimensions and grid interval
    WIDTH, HEIGHT = 800, 600
    GRID_INTERVAL = 40

    # Colors
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)

    # Screen setup
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Volleyball Blocking with Pose Tracking")

    # Clock for controlling frame rate
    clock = pygame.time.Clock()

    # Player attributes
    player_width = 20
    player_height = 100
    leg_width = 8
    leg_height = 40
    head_radius = 15
    player_y = HEIGHT - 300

    # Pose tracking setup
    pose_tracker = PoseTracker()
    cap = cv2.VideoCapture(0)  # Open webcam

    # Jump and pose variables
    is_jumping = False
    jump_count = 10
    current_pose = "idle"

    # Main game loop
    running = True
    while running:
        screen.fill(WHITE)
        draw_grid(screen, WIDTH, HEIGHT, GRID_INTERVAL)

        # Capture frame from webcam
        ret, frame = cap.read()
        if not ret:
            break

        # Process the frame and get landmarks
        landmarks = pose_tracker.process_frame(frame)
        
        if landmarks:
            # Update player x-position based on horizontal movement
            player_x = pose_tracker.get_horizontal_position(landmarks, WIDTH)

            # Jump detection
            if pose_tracker.detect_jump(landmarks):
                is_jumping = True

            # Blocking pose detection
            current_pose = pose_tracker.get_blocking_pose(landmarks)

        # Jumping mechanics
        if is_jumping:
            if jump_count >= -10:
                neg = 1 if jump_count > 0 else -1
                player_y -= (jump_count ** 2) * 0.5 * neg
                jump_count -= 1
            else:
                jump_count = 10
                is_jumping = False

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Draw player
        draw_player(screen, player_x, player_y, current_pose, 
                    player_width, player_height, leg_width, leg_height, 
                    head_radius, RED)

        pygame.display.flip()
        clock.tick(30)

    # Cleanup
    cap.release()
    pygame.quit()

if __name__ == "__main__":
    main()