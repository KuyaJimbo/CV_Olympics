import cv2
import mediapipe as mp
import numpy as np
import time
import threading

class PoseController:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils

        # Baseline Parameters
        self.Baseline_FloorY = 0.1
        self.Baseline_Height = 0.1
        self.Baseline_KneeLevel = 0.1

        # Pose Dictionary
        self.pose_dictionary = {
            "HeadLowered": [],
            "KneesBent": [],
            "HandsBelowKnees": [],
            "HandsBelowHips": [],
            "HandsBelowShoulders": [],
        }

        # Parameters for jump and block detection
        self.update_interval = 0.1  # 100 ms # TOO SLOW, THE GAME WILL THINK YOUR ARE TELEPORTING!
        self.last_update_time = time.time()
        self.last_jump_time = 0
        
        # Camera and pose detection setup
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=min_detection_confidence, 
            min_tracking_confidence=min_tracking_confidence
        )
        
        # Threading for camera capture
        self.cap = None
        self.landmarks = None
        self.running = False
        self.baseline_set = False
        self.player_x_position = 0.5  # Normalized x position (0 to 1)
        
        # Jump and block detection
        self.is_jumping = False
        self.block_type = "None"
        self.jump_power = 0

    def start_camera(self):
        """Start camera capture in a separate thread."""
        self.cap = cv2.VideoCapture(0)
        self.running = True
        self.camera_thread = threading.Thread(target=self._camera_loop)
        self.camera_thread.daemon = True
        self.camera_thread.start()

    def stop_camera(self):
        """Stop camera capture."""
        self.running = False
        if self.cap:
            self.cap.release()
        if hasattr(self, 'camera_thread'):
            self.camera_thread.join()

    def _camera_loop(self):
        """Internal method to continuously process camera frames."""
        while self.running:
            success, image = self.cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            # Process image
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # flip image for mirror effect
            image_rgb = cv2.flip(image_rgb, 1)
            results = self.pose.process(image_rgb)

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark

                # Set baseline on first detection
                if not self.baseline_set:
                    self._get_baselines(landmarks)
                    self.baseline_set = True

                # Update pose states 
                if time.time() - self.last_update_time >= self.update_interval:
                    self._update_pose_dict(landmarks)
                    self._detect_jump_and_block(landmarks)
                    self._calculate_player_x(landmarks)
                    self.last_update_time = time.time()

                # Store landmarks for external access
                self.landmarks = landmarks

    def _get_baselines(self, landmarks):
        """Calculate baseline measurements from landmarks."""
        left_ankle = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE]
        right_ankle = landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE]
        self.Baseline_FloorY = (left_ankle.y + right_ankle.y) / 2

        # Calculate nose to feet height difference
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE]
        self.Baseline_Height = nose.y - self.Baseline_FloorY

        # Calculate knee level
        left_knee = landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE]
        right_knee = landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE]
        self.Baseline_KneeLevel = (left_knee.y + right_knee.y) / 2

    def _detect_jump_and_block(self, landmarks):
        """Detect jump and block type."""
        # Jump detection
        left_ankle = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE]
        right_ankle = landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE]
        avg_feet_y = (left_ankle.y + right_ankle.y) / 2
        self.is_jumping = avg_feet_y < self.Baseline_KneeLevel

        # Block type detection
        self.block_type = self._get_block_type(landmarks)

        # Jump power calculation
        jump_value = sum(any(self.pose_dictionary[key]) for key in self.pose_dictionary)
        if jump_value == 3:
            self.jump_power = 20
        elif jump_value >= 1:
            self.jump_power = 16
        else:
            self.jump_power = 12

    def _calculate_player_x(self, landmarks):
        """Calculate normalized X position of player."""
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
        
        # Normalize x position between 0 and 1
        self.player_x_position = (left_shoulder.x + right_shoulder.x) / 2

    def _get_block_type(self, landmarks):
        """Determine block type based on hand and nose positions."""
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE]
        left_hand = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST]
        right_hand = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST]
        left_elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW]
        right_elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]

        # Check elbow position relative to shoulders
        if left_elbow.y < left_shoulder.y and right_elbow.y < right_shoulder.y:
            if left_hand.x < nose.x and right_hand.x < nose.x:
                return "Left"
            elif left_hand.x > nose.x and right_hand.x > nose.x:
                return "Right"
            elif self._close_enough(left_hand, right_hand, 0.2):
                return "Middle"
            else:
                return "Split"
        return "None"

    def _close_enough(self, point1, point2, threshold=0.1):
        """Check if two points are within a certain distance threshold."""
        distance = np.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)
        return distance < threshold

    def _update_pose_dict(self, landmarks):
        """Update pose dictionary with current state checks."""
        # Similar to the original UpdatePoseDict function
        self.pose_dictionary["HeadLowered"].append(
            landmarks[self.mp_pose.PoseLandmark.NOSE].y > 
            self.Baseline_FloorY + (self.Baseline_Height * 0.5)
        )
        
        self.pose_dictionary["KneesBent"].append(
            (landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE].y + 
             landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE].y) / 2 >
            self.Baseline_FloorY + abs(self.Baseline_KneeLevel - self.Baseline_FloorY) * 0.2
        )

        self.pose_dictionary["HandsBelowKnees"].append(
            (landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST].y < 
             landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE].y) and
            (landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST].y < 
             landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE].y)
        )
        # TOO MANY POSES TO TRACK SLOWS DOWN THE GAME
        # self.pose_dictionary["HandsBelowHips"].append(
        #     (landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST].y < 
        #      landmarks[self.mp_pose.PoseLandmark.LEFT_HIP].y) and
        #     (landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST].y < 
        #      landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP].y)
        # )
        # self.pose_dictionary["HandsBelowShoulders"].append(
        #     (landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST].y < 
        #      landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y) and
        #     (landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST].y < 
        #      landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].y)
        # )

        # Add other pose checks as needed, maintaining a list of 5 recent states
        for key in self.pose_dictionary:
            if len(self.pose_dictionary[key]) > 6:  # Too many slows the game down!
                self.pose_dictionary[key].pop(0)

    def get_player_controls(self):
        """
        Return a dictionary of player controls based on pose detection.
        
        This method can be called by the game loop to determine 
        player movement and actions.
        """
        return {
            'move_x': self.player_x_position,  # Normalized x position
            'jump': self.is_jumping,
            'jump_power': self.jump_power,
            'block_type': self.block_type
        }