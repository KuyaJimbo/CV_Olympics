import cv2
import mediapipe as mp
import numpy as np
import time

class PoseDetector:
    def __init__(self):
        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils

        # Globals
        self.baseline_height = 1.0  # Default value
        self.pose_dictionary = {
            "HeadLowered": [],
            "KneesBent": [],
            "HandsBelowKnees": [],
            "HandsBelowHips": [],
            "HandsBelowShoulders": [],
        }
        self.update_interval = 0.2  # 200 ms
        self.last_update_time = time.time()
        self.jump_threshold = 0.5  # Adjust based on sensitivity
        self.jump_cooldown = 2  # Cooldown period in seconds
        self.last_jump_time = 0  # Timestamp of the last detected jump

        # MediaPipe Pose setup
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    def detect_jump(self, landmarks):
        """
        Determine if a jump occurred by comparing the nose's current and past positions.
        Incorporates a cooldown to avoid multiple detections for the same jump.
        """
        current_time = time.time()

        # Check cooldown
        if current_time - self.last_jump_time < self.jump_cooldown:
            return False, 0

        # Update pose states
        self._last_second_pose_storage(landmarks)

        # Check for jump by comparing recent pose data
        if len(self.pose_dictionary["HeadLowered"]) >= 2:
            current_nose_y = self.pose_dictionary["HeadLowered"][-1]
            past_nose_y = self.pose_dictionary["HeadLowered"][-2]
            if past_nose_y - current_nose_y > self.jump_threshold:
                self.last_jump_time = current_time  # Update the last jump time
                jump_power = self.jump_power()
                return True, jump_power

        return False, 0

    def _get_standing_height(self, landmarks):
        """
        Calculate the current standing height between feet and nose.
        """
        nose_y = landmarks[self.mp_pose.PoseLandmark.NOSE].y
        feet_y = (landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE].y + 
                  landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE].y) / 2
        height = nose_y - feet_y
        return height if height else 1.0

    def update_baseline_height(self, landmarks):
        """
        Recalculate the baseline height based on the distance between feet and nose.
        """
        self.baseline_height = self._get_standing_height(landmarks)
        print("Baseline height updated:", self.baseline_height)

    def _close_enough(self, point1, point2, threshold=0.1):
        """
        Check if two points are within a certain distance threshold.
        """
        distance = np.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)
        return distance < threshold

    def _head_lowered(self, landmarks):
        """
        Determine if the head is lowered significantly compared to the baseline height.
        """
        current_height = self._get_standing_height(landmarks)
        return current_height < self.baseline_height * 0.7

    def _knees_bent(self, landmarks):
        """
        Check if the knees are bent by comparing the positions of hips and knees.
        """
        left_knee = landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE]
        right_knee = landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE]
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP]
        return self._close_enough(left_knee, left_hip, 0.08) and self._close_enough(right_knee, right_hip, 0.08)

    def _hands_below_knees(self, landmarks):
        """
        Check if both hands are below the knees.
        """
        left_hand = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST]
        right_hand = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST]
        left_knee = landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE]
        right_knee = landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE]
        return left_hand.y > left_knee.y and right_hand.y > right_knee.y

    def _hands_below_hips(self, landmarks):
        """
        Check if both hands are below the hips.
        """
        left_hand = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST]
        right_hand = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST]
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP]
        return left_hand.y > left_hip.y and right_hand.y > right_hip.y

    def _hands_below_shoulders(self, landmarks):
        """
        Check if both hands are below the shoulders.
        """
        left_hand = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST]
        right_hand = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
        return left_hand.y > left_shoulder.y and right_hand.y > right_shoulder.y

    def _last_second_pose_storage(self, landmarks):
        """
        Update the pose dictionary with the latest pose states.
        """
        self.pose_dictionary["HeadLowered"].append(self._head_lowered(landmarks))
        self.pose_dictionary["KneesBent"].append(self._knees_bent(landmarks))
        self.pose_dictionary["HandsBelowKnees"].append(self._hands_below_knees(landmarks))
        self.pose_dictionary["HandsBelowHips"].append(self._hands_below_hips(landmarks))
        self.pose_dictionary["HandsBelowShoulders"].append(self._hands_below_shoulders(landmarks))
        
        # Maintain a list size of 5 (1 second at 0.2s intervals)
        for key in self.pose_dictionary:
            if len(self.pose_dictionary[key]) > 5:
                self.pose_dictionary[key].pop(0)

    def block_type(self, landmarks):
        """
        Determine the block type based on hand and elbow positions.
        """
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE]
        left_hand = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST]
        right_hand = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST]
        left_elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW]
        right_elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]

        if left_elbow.y < left_shoulder.y and right_elbow.y < right_shoulder.y:
            if left_hand.x < nose.x and right_hand.x < nose.x:
                return "Left Block"
            elif left_hand.x > nose.x and right_hand.x > nose.x:
                return "Right Block"
            elif self._close_enough(left_hand, right_hand, 0.2):
                return "Middle Block"
            else:
                return "Split Block"
        return None

    def jump_power(self):
        """
        Calculate the jump power based on the states stored in the pose dictionary.
        """
        jump_score = sum(any(self.pose_dictionary[key]) for key in self.pose_dictionary)
        jump_factor = 0
        if jump_score == 5:
            jump_factor = 16
        elif jump_score >= 3:
            jump_factor = 15
        else:
            jump_factor = 14 
        return jump_factor

def start_pose_detection():
    """
    Start the pose detection camera feed.
    """
    # Initialize the detector
    detector = PoseDetector()
    cap = cv2.VideoCapture(0)
    cv2.namedWindow("Pose Detection")

    with detector.pose as pose:
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            # Process image
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = pose.process(image_rgb)

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark

                # Update baseline height on mouse click
                cv2.setMouseCallback("Pose Detection", 
                    lambda event, x, y, flags, param: detector.update_baseline_height(landmarks) 
                    if event == cv2.EVENT_LBUTTONDOWN else None)

                # Detect jump and block type
                jump_detected, jump_power = detector.detect_jump(landmarks)
                block_type = detector.block_type(landmarks)

                # Display information
                cv2.putText(image, f"Block: {block_type or 'None'}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(image, f"Jumping: {'Yes' if jump_detected else 'No'}", 
                            (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                # Draw pose landmarks
                detector.mp_drawing.draw_landmarks(
                    image, results.pose_landmarks, detector.mp_pose.POSE_CONNECTIONS)

            # Display image
            cv2.imshow("Pose Detection", image)
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_pose_detection()
# start_pose_detection()