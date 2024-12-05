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
            print("Jump detected!")
            return True

        return False

    def get_arm_position(self, landmarks):
        """Determine arm position based on hand landmarks."""
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE]
        left_hand = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST]
        right_hand = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]

        # Determine arm position
        if left_hand.y < nose.y and right_hand.y < nose.y:
            return "above_head"
        elif left_hand.x < nose.x and left_hand.y < left_shoulder.y:
            return "left_side"
        elif right_hand.x > nose.x and right_hand.y < right_shoulder.y:
            return "right_side"
        return "beside_body"

    def get_horizontal_position(self, landmarks):
        """Get horizontal position of the player."""
        nose_x = landmarks[self.mp_pose.PoseLandmark.NOSE].x
        return nose_x