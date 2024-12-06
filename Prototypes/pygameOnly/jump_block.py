import cv2
import mediapipe as mp
import time

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Globals
baseline_height = 1.0  # Default value
last_update_time = time.time()
jump_cooldown = 2  # Cooldown period in seconds
last_jump_time = 0  # Timestamp of the last detected jump
pose_dictionary = {
    "HeadLowered": [],
    "KneesBent": [],
    "HandsBelowKnees": [],
    "HandsBelowHips": [],
    "HandsBelowShoulders": [],
}

def DetectJump(landmarks):
    """
    Determine if a jump occurred and calculate the jump factor.
    """
    global baseline_height, last_jump_time

    current_time = time.time()
    if current_time - last_jump_time < jump_cooldown:
        return False, 0

    # Get the current height and neck length
    current_height = GetStandingHeight(landmarks)
    neck_length = GetNeckLength(landmarks)

    # Detect jump based on height exceeding baseline plus a threshold
    if current_height > baseline_height + neck_length * 0.9:
        jump_factor = current_height - (baseline_height + neck_length * 0.9)
        last_jump_time = current_time
        return True, jump_factor

    return False, 0

def UpdateBaselineHeight(landmarks):
    """
    Update the baseline height based on the current standing height.
    """
    global baseline_height
    baseline_height = GetStandingHeight(landmarks)
    print("Baseline height updated:", baseline_height)

def GetStandingHeight(landmarks):
    """
    Calculate the current standing height between feet and nose.
    """
    try:
        nose_y = landmarks[mp_pose.PoseLandmark.NOSE].y
        feet_y = (landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].y + landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].y) / 2
        return max(1.0, nose_y - feet_y)  # Avoid negative or zero heights
    except KeyError:
        return 1.0  # Default value if landmarks are incomplete

def GetNeckLength(landmarks):
    """
    Calculate the neck length as the distance between nose and shoulders.
    """
    try:
        nose_y = landmarks[mp_pose.PoseLandmark.NOSE].y
        shoulders_y = (
            landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y +
            landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y
        ) / 2
        return abs(nose_y - shoulders_y)
    except KeyError:
        return 0.1  # Default value if landmarks are incomplete

def TrackNoseX(landmarks):
    """
    Track the X position of the nose.
    """
    return landmarks[mp_pose.PoseLandmark.NOSE].x

# Main Loop
cap = cv2.VideoCapture(0)
with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue

        # Process image
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # update the baseline height when the left mouse button is clicked on the screen
            if cv2.waitKey(1) & 0xFF == ord('m'):
                UpdateBaselineHeight(landmarks)

            # Update baseline height periodically
            # if time.time() - last_update_time >= 0.2:  # 200ms interval
            #     UpdateBaselineHeight(landmarks)
            #     # last_update_time = time.time()

            # Detect jump and calculate jump factor
            jump_detected, jump_factor = DetectJump(landmarks)
            nose_x = TrackNoseX(landmarks)

            # Display results on the frame
            cv2.putText(frame, f"Nose X: {nose_x:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            if jump_detected:
                cv2.putText(frame, f"Jump Factor: {jump_factor:.2f}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Draw pose landmarks
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # Display the frame
        cv2.imshow('Jump Detector', frame)
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
