import pygame
import sys
import cv2
import mediapipe as mp
import numpy as np
import time

# Initialize Pygame and MediaPipe
pygame.init()
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

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

# Pose Tracking Globals
baseline_height = 1.0
pose_dictionary = {
    "HeadLowered": [],
    "KneesBent": [],
    "HandsBelowKnees": [],
    "HandsBelowHips": [],
    "HandsBelowShoulders": [],
}
update_interval = 0.2  # 200 ms
last_update_time = time.time()
jump_threshold = 0.5
jump_cooldown = 2
last_jump_time = 0

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Volleyball Blocking")

# Load Player Images (same as before)
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

# Pose Tracking Functions
def UpdateBaselineHeight(landmarks):
    global baseline_height
    baseline_height = GetStandingHeight(landmarks)
    print("Baseline height updated:", baseline_height)

def GetStandingHeight(landmarks):
    nose_y = landmarks[mp_pose.PoseLandmark.NOSE].y
    feet_y = (landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].y + landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].y) / 2
    height = nose_y - feet_y
    return height if height else 1.0

def CloseEnough(point1, point2, threshold=0.1):
    distance = np.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)
    return distance < threshold

def HeadLowered(landmarks):
    global baseline_height
    current_height = GetStandingHeight(landmarks)
    return current_height < baseline_height * 0.7

def KneesBent(landmarks):
    left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
    right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
    return CloseEnough(left_knee, left_hip, 0.08) and CloseEnough(right_knee, right_hip, 0.08)

def LastSecondPoseStorage(landmarks):
    global pose_dictionary
    pose_dictionary["HeadLowered"].append(HeadLowered(landmarks))
    pose_dictionary["KneesBent"].append(KneesBent(landmarks))
    
    # Maintain a list size of 5 (1 second at 0.2s intervals)
    for key in pose_dictionary:
        if len(pose_dictionary[key]) > 5:
            pose_dictionary[key].pop(0)

def DetectJump():
    global pose_dictionary, last_jump_time

    current_time = time.time()

    # Check cooldown
    if current_time - last_jump_time < jump_cooldown:
        return False

    # Check for jump by comparing recent pose data
    if len(pose_dictionary["HeadLowered"]) >= 2:
        current_nose_y = pose_dictionary["HeadLowered"][-1]
        past_nose_y = pose_dictionary["HeadLowered"][-2]
        if past_nose_y - current_nose_y > jump_threshold:
            # check if abs(current height - baseline height) > jump_threshold
            if abs(current_nose_y - baseline_height) < 0.5:
                last_jump_time = current_time
                return True

    return False

def JumpPower():
    jump_score = sum(any(pose_dictionary[key]) for key in pose_dictionary)
    jump_factor = 0
    if jump_score == 2:  # Adjusted for simplified tracking
        jump_factor = 16
    elif jump_score >= 1:
        jump_factor = 15
    else:
        jump_factor = 14 
    return jump_factor

def MapXPosition(nose_x, screen_width):
    # Map nose x-coordinate to screen width
    # Assuming nose_x is between 0 and 1
    
    # return int(nose_x * screen_width)
    # consider that the screen is backwards horizontally
    return int((1 - nose_x) * screen_width)

# Player Class (same as before)
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
        surface.blit(pygame.transform.scale(self.image, (PLAYER_SIZE * 5, PLAYER_SIZE * 5)), 
                     (self.rect.x - PLAYER_SIZE * 2, self.rect.y - PLAYER_SIZE * 2))

# Draw grid (same as before)
def draw_grid():
    for x in range(0, SCREEN_WIDTH, GRID_INTERVAL):
        pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, GRID_INTERVAL):
        pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))

# Main game loop with pose tracking
def main():
    global baseline_height, last_update_time

    # Initialize player and camera
    player = Player()
    cap = cv2.VideoCapture(0)
    clock = pygame.time.Clock()

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while True:
            # Pygame event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    cap.release()
                    cv2.destroyAllWindows()
                    sys.exit()
                # if mouse click, update baseline height
                if event.type == pygame.MOUSEBUTTONDOWN:
                    _, image = cap.read()
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    results = pose.process(image_rgb)
                    if results.pose_landmarks:
                        landmarks = results.pose_landmarks.landmark
                        UpdateBaselineHeight(landmarks)

            # Capture frame from camera
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            # Process image
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = pose.process(image_rgb)

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                nose = landmarks[mp_pose.PoseLandmark.NOSE]

                # Update pose states every 0.2 seconds
                if time.time() - last_update_time >= update_interval:
                    LastSecondPoseStorage(landmarks)
                    last_update_time = time.time()

                # Map nose x-position to player x-position
                player.rect.x = MapXPosition(nose.x, SCREEN_WIDTH)

                # Detect and perform jump
                jump_detected = DetectJump()
                if jump_detected:
                    jump_power = JumpPower()
                    player.jump_by_factor(jump_power)

            # Draw everything
            screen.fill(ORANGE)
            draw_grid()
            screen.blit(new_VB_BG_images["Floor"], (0, 0))
            screen.blit(new_VB_BG_images["Net"], (0, 0))
            player.update()
            player.draw(screen)
            pygame.display.flip()

            clock.tick(60)

if __name__ == "__main__":
    main()