import cv2
import mediapipe as mp
import numpy as np
import time

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Globals
baseline_height = 1.0  # Default value
pose_dictionary = {
    "HeadLowered": [],
    "KneesBent": [],
    "HandsBelowKnees": [],
    "HandsBelowHips": [],
    "HandsBelowShoulders": [],
}
update_interval = 0.2  # 200 ms
last_update_time = time.time()
jump_threshold = 0.15  # Adjust based on sensitivity
jump_cooldown = 2  # Cooldown period in seconds
last_jump_time = 0  # Timestamp of the last detected jump

def DetectJump():
    """
    Determine if a jump occurred by comparing the nose's current and past positions.
    Incorporates a cooldown to avoid multiple detections for the same jump.
    """
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
            last_jump_time = current_time  # Update the last jump time
            return True

    return False

# Functions

def UpdateBaselineHeight(landmarks):
    """
    Recalculate the baseline height based on the distance between feet and nose.
    """
    global baseline_height
    baseline_height = GetStandingHeight(landmarks)
    print("Baseline height updated:", baseline_height)

def GetStandingHeight(landmarks):
    """
    Calculate the current standing height between feet and nose.
    """
    nose_y = landmarks[mp_pose.PoseLandmark.NOSE].y
    feet_y = (landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].y + landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].y) / 2
    height = nose_y - feet_y
    return height if height else 1.0

def CloseEnough(point1, point2, threshold=0.1):
    """
    Check if two points are within a certain distance threshold.
    """
    distance = np.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)
    return distance < threshold

def HeadLowered(landmarks):
    """
    Determine if the head is lowered significantly compared to the baseline height.
    """
    global baseline_height
    current_height = GetStandingHeight(landmarks)
    return current_height < baseline_height * 0.8

def KneesBent(landmarks):
    """
    Check if the knees are bent by comparing the positions of hips and knees.
    """
    left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
    right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
    return CloseEnough(left_knee, left_hip) and CloseEnough(right_knee, right_hip)

def HandsBelowKnees(landmarks):
    """
    Check if both hands are below the knees.
    """
    left_hand = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
    right_hand = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
    left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
    right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
    return left_hand.y > left_knee.y and right_hand.y > right_knee.y

def HandsBelowHips(landmarks):
    """
    Check if both hands are below the hips.
    """
    left_hand = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
    right_hand = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
    return left_hand.y > left_hip.y and right_hand.y > right_hip.y

def HandsBelowShoulders(landmarks):
    """
    Check if both hands are below the shoulders.
    """
    left_hand = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
    right_hand = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
    return left_hand.y > left_shoulder.y and right_hand.y > right_shoulder.y

def LastSecondPoseStorage(landmarks):
    """
    Update the pose dictionary with the latest pose states.
    """
    global pose_dictionary
    pose_dictionary["HeadLowered"].append(HeadLowered(landmarks))
    pose_dictionary["KneesBent"].append(KneesBent(landmarks))
    pose_dictionary["HandsBelowKnees"].append(HandsBelowKnees(landmarks))
    pose_dictionary["HandsBelowHips"].append(HandsBelowHips(landmarks))
    pose_dictionary["HandsBelowShoulders"].append(HandsBelowShoulders(landmarks))
    
    # Maintain a list size of 5 (1 second at 0.2s intervals)
    for key in pose_dictionary:
        if len(pose_dictionary[key]) > 5:
            pose_dictionary[key].pop(0)

def BlockType(landmarks):
    """
    Determine the block type based on hand and elbow positions.
    """
    nose = landmarks[mp_pose.PoseLandmark.NOSE]
    left_hand = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
    right_hand = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
    left_elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW]
    right_elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW]
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]

    if left_elbow.y < left_shoulder.y and right_elbow.y < right_shoulder.y:
        if left_hand.x < nose.x and right_hand.x < nose.x:
            return "Left Block"
        elif left_hand.x > nose.x and right_hand.x > nose.x:
            return "Right Block"
        elif CloseEnough(left_hand, right_hand, 0.2):
            return "Middle Block"
        else:
            return "Split Block"
    return None

def JumpPower():
    """
    Calculate the jump power based on the states stored in the pose dictionary.
    """
    jump_power = sum(any(pose_dictionary[key]) for key in pose_dictionary)
    return jump_power

# Main Loop
cap = cv2.VideoCapture(0)
cv2.namedWindow("Pose Detection")

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

            # Update baseline height on mouse click
            cv2.setMouseCallback("Pose Detection", lambda event, x, y, flags, param: UpdateBaselineHeight(landmarks) if event == cv2.EVENT_LBUTTONDOWN else None)

            # Update pose states every 0.2 seconds
            if time.time() - last_update_time >= update_interval:
                LastSecondPoseStorage(landmarks)
                last_update_time = time.time()

            # Display Block Type and Jump Status
            block_type = BlockType(landmarks)
            jump_detected = DetectJump()

            cv2.putText(image, f"Block: {block_type or 'None'}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(image, f"Jumping: {'Yes' if jump_detected else 'No'}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            # Print jump details to the terminal if a jump is detected
            if jump_detected:
                jump_power = JumpPower()
                print(f"Block Type: {block_type}, Jump Power: {jump_power}")

            # Draw pose landmarks
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # Display image
        cv2.imshow("Pose Detection", image)
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
