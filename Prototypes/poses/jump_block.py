import cv2
import mediapipe as mp
import time
import numpy as np

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Globals for tracking
baseline_height = None
pose_history = []
JUMP_THRESHOLD = 0.02
UI_DISPLAY_TIME = 1  # seconds
last_jump_time = 0
jump_info = None
landmarks_for_baseline = None  # Stores landmarks for recalibration

# Functions

def GetStandingHeight(landmarks):
    """
    Tracks baseline height as the distance between the feet and the nose.
    """
    nose = landmarks[mp_pose.PoseLandmark.NOSE]
    left_foot = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
    right_foot = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
    foot_avg_y = (left_foot.y + right_foot.y) / 2
    return nose.y - foot_avg_y

def CloseEnough(point1, point2, threshold=0.1):
    """
    Determines if two points are close within a specified threshold.
    """
    distance = np.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)
    return distance < threshold

def LastSecondPoseStorage(landmarks):
    """
    Maintains a list of pose data for the last second.
    """
    global pose_history
    pose_history.append(landmarks)
    if len(pose_history) > 30:  # Assuming 30 FPS
        pose_history.pop(0)

def BlockType(nose, right_hand, left_hand, right_elbow, left_elbow, right_shoulder, left_shoulder):
    """
    Determines block type based on hand and elbow positions relative to the nose.
    """
    both_elbows_above_shoulders = (right_elbow.y < right_shoulder.y) and (left_elbow.y < left_shoulder.y)
    if not both_elbows_above_shoulders:
        return None

    if left_hand.x < nose.x and right_hand.x < nose.x:
        return "Left Block"
    elif left_hand.x > nose.x and right_hand.x > nose.x:
        return "Right Block"
    elif CloseEnough(left_hand, right_hand, 0.2):
        return "Middle Block"
    else:
        return "Split Block"

def DetectJump(landmarks):
    """
    Detects a jump by comparing the current nose height with the height 1 second ago.
    """
    global pose_history
    if len(pose_history) < 30:
        return False
    nose_now = landmarks[mp_pose.PoseLandmark.NOSE]
    nose_before = pose_history[0][mp_pose.PoseLandmark.NOSE]
    return nose_now.y < nose_before.y - JUMP_THRESHOLD

def WasHeadLowered(current_height):
    """
    Detects if the head height is significantly lower than the baseline.
    """
    global baseline_height
    if current_height < baseline_height * 0.8:
        return True
    return False

def WasKneesBent(landmarks):
    """
    Detects if knees are bent by checking if knees and hips are close.
    """
    left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
    right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
    return CloseEnough(left_knee, left_hip) and CloseEnough(right_knee, right_hip)

def JumpPower(landmarks):
    """
    Calculates jump power based on hand and knee positions.
    """
    left_hand = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
    right_hand = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
    left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
    right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
    left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
    right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]

    jump_power = 0

    if WasKneesBent(landmarks):
        jump_power += 1

    # was head lowered
    

    return jump_power

def UpdateUI(image, landmarks):
    """
    Displays jump and block information on the screen.
    """
    global last_jump_time, jump_info
    # constantly show block type
    block_type = BlockType(
        landmarks[mp_pose.PoseLandmark.NOSE],
        landmarks[mp_pose.PoseLandmark.RIGHT_WRIST],
        landmarks[mp_pose.PoseLandmark.LEFT_WRIST],
        landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW],
        landmarks[mp_pose.PoseLandmark.LEFT_ELBOW],
        landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER],
        landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
    )
    # if block_type is None, display "No Block", else display block_type
    block_type = block_type if block_type else "No Block"
    cv2.putText(image, block_type, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 5)
    # Detect jump
    if DetectJump(landmarks):
        jump_power = JumpPower(landmarks)
        jump_info = (f"Jump - Power: {jump_power}")
        last_jump_time = time.time()

    # Display jump info
    if time.time() - last_jump_time < UI_DISPLAY_TIME and jump_info:
        cv2.putText(image, jump_info, (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 5)



def mouse_click(event, x, y, flags, param):
    """
    Mouse callback to recalculate baseline height on left-click.
    """
    global baseline_height, landmarks_for_baseline
    if event == cv2.EVENT_LBUTTONDOWN and landmarks_for_baseline:
        baseline_height = GetStandingHeight(landmarks_for_baseline)
        print("Baseline height recalculated!")

# Main Loop
cap = cv2.VideoCapture(0)
cv2.namedWindow("Jump & Block Detection")
cv2.setMouseCallback("Jump & Block Detection", mouse_click)

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
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
            landmarks_for_baseline = landmarks  # Save landmarks for recalibration

            # Initialize baseline height
            if baseline_height is None:
                baseline_height = GetStandingHeight(landmarks)

            # Update pose history and UI
            LastSecondPoseStorage(results.pose_landmarks.landmark)
            UpdateUI(image, results.pose_landmarks.landmark)

            # Draw landmarks
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # Flip image then Display image
        image = cv2.flip(image, 1)
        cv2.imshow("Jump & Block Detection", image)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
