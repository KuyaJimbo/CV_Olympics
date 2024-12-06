import cv2
import mediapipe as mp
import numpy as np
import time

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Baseline Parameters
Baseline_FloorY = 0.1
Baseline_Height = 0.1
Baseline_KneeLevel = 0.1

# Pose Dictionary
pose_dictionary = {
    "HeadLowered": [],
    "KneesBent": [],
    "HandsBelowKnees": [],
    "HandsBelowHips": [],
    "HandsBelowShoulders": [],
}

# Parameters for jump detection
update_interval = 0.1  # 100 ms
jump_cooldown = 1  # Cooldown period in seconds
last_update_time = time.time()
last_jump_time = 0
jump_display_duration = 3  # seconds to display jump details
last_jump_details = None
jump_details_timer = 0


def CloseEnough(point1, point2, threshold=0.1):
    """
    Check if two points are within a certain distance threshold.
    """
    distance = np.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)
    return distance < threshold


def GetBaselines(landmarks):
    """
    Calculate baseline measurements from landmarks.
    """
    global Baseline_FloorY, Baseline_Height, Baseline_KneeLevel

    # Calculate average feet Y
    left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
    right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
    Baseline_FloorY = (left_ankle.y + right_ankle.y) / 2

    # Calculate nose to feet height difference
    nose = landmarks[mp_pose.PoseLandmark.NOSE]
    Baseline_Height = nose.y - Baseline_FloorY

    # Calculate knee level
    left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
    right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
    Baseline_KneeLevel = (left_knee.y + right_knee.y) / 2

    print(
        f"Baselines Updated! FloorY: {Baseline_FloorY}, Height: {Baseline_Height}, KneeLevel: {Baseline_KneeLevel}"
    )


def CheckDetectJump(landmarks):
    """
    Check if a jump has occurred by comparing current foot position to baseline knee level.
    """
    global Baseline_KneeLevel

    # Calculate average Y-coordinate of both feet
    left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
    right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
    avg_feet_y = (left_ankle.y + right_ankle.y) / 2

    # Return true if feet are above knee level
    return avg_feet_y < Baseline_KneeLevel


def CheckHeadLowered(landmarks, threshold=0.6):
    """
    Check if head is lowered below baseline.
    """
    nose = landmarks[mp_pose.PoseLandmark.NOSE]
    return nose.y > Baseline_FloorY + (Baseline_Height * threshold)


def CheckKneesBent(landmarks, threshold=0.7):
    """
    Check if knees are bent below baseline.
    """
    left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
    right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
    avg_knee_y = (left_knee.y + right_knee.y) / 2
    return avg_knee_y > Baseline_FloorY + (Baseline_KneeLevel * threshold)


def CheckHandsBelowKnees(landmarks):
    """
    Check if hands are below knees.
    """
    left_hand = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
    right_hand = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
    left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
    right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
    return left_hand.y > left_knee.y and right_hand.y > right_knee.y


def CheckHandsBelowHips(landmarks):
    """
    Check if hands are below hips.
    """
    left_hand = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
    right_hand = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
    return left_hand.y > left_hip.y and right_hand.y > right_hip.y


def CheckHandsBelowShoulders(landmarks):
    """
    Check if hands are below shoulders.
    """
    left_hand = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
    right_hand = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
    return left_hand.y > left_shoulder.y and right_hand.y > right_shoulder.y


def UpdatePoseDict(landmarks):
    """
    Update pose dictionary with current state checks.
    """
    global pose_dictionary

    pose_dictionary["HeadLowered"].append(CheckHeadLowered(landmarks))
    pose_dictionary["KneesBent"].append(CheckKneesBent(landmarks))
    pose_dictionary["HandsBelowKnees"].append(CheckHandsBelowKnees(landmarks))
    pose_dictionary["HandsBelowHips"].append(CheckHandsBelowHips(landmarks))
    pose_dictionary["HandsBelowShoulders"].append(CheckHandsBelowShoulders(landmarks))

    # Maintain a list size of 5
    for key in pose_dictionary:
        if len(pose_dictionary[key]) > 5:
            pose_dictionary[key].pop(0)


def GetJumpPower():
    """
    Calculate jump power based on pose checks.
    """
    jump_value = sum(any(pose_dictionary[key]) for key in pose_dictionary)

    if jump_value == 6:
        return 16
    elif jump_value >= 3:
        return 15
    else:
        return 14


def GetBlockType(landmarks):
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
    return "None"


# Callback for mouse events
def mouse_callback(event, x, y, flags, param):
    global baseline_set

    if event == cv2.EVENT_RBUTTONDOWN and param:
        # Recalculate baselines when right-clicked
        GetBaselines(param)
        baseline_set = True


# Main Loop
cap = cv2.VideoCapture(0)
cv2.namedWindow("Pose Detection")

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    baseline_set = False

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

            # Set baseline on first detection
            if not baseline_set:
                GetBaselines(landmarks)
                baseline_set = True

            # Set mouse callback with current landmarks
            cv2.setMouseCallback("Pose Detection", mouse_callback, landmarks)

            # Update pose states every 0.2 seconds
            if time.time() - last_update_time >= update_interval:
                UpdatePoseDict(landmarks)
                last_update_time = time.time()

            # Detect jump and block type
            jump_detected = CheckDetectJump(landmarks)

            if jump_detected:
                last_jump_time = time.time()
                last_jump_details = {
                    "jump_value": GetJumpPower(),
                    "block_type": GetBlockType(landmarks),
                    "time": time.time(),
                }
                jump_details_timer = time.time()

            # Visualize baselines
            if baseline_set:
                # Calculate pixel positions for baselines
                floor_line = int(image.shape[0] * Baseline_FloorY)
                knee_line = int(image.shape[0] * Baseline_KneeLevel)

                # Draw the lines
                cv2.line(
                    image, (0, floor_line), (image.shape[1], floor_line), (255, 0, 0), 2
                )  # Blue for floor
                cv2.line(
                    image, (0, knee_line), (image.shape[1], knee_line), (0, 255, 0), 2
                )  # Green for knee level

            # Prepare pose indicators list
            pose_indicators = [
                ("Head Lowered", any(pose_dictionary["HeadLowered"])),
                ("Knees Bent", any(pose_dictionary["KneesBent"])),
                ("Hands Below Knees", any(pose_dictionary["HandsBelowKnees"])),
                ("Hands Below Hips", any(pose_dictionary["HandsBelowHips"])),
                ("Hands Below Shoulders", any(pose_dictionary["HandsBelowShoulders"])),
            ]

            # Draw pose indicators
            y_offset = 30
            for name, state in pose_indicators:
                color = (0, 255, 0) if state else (0, 0, 255)
                cv2.putText(
                    image,
                    name,
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2,
                )
                y_offset += 30

            # Display jump details if recently detected
            if (
                last_jump_details
                and time.time() - last_jump_details["time"] < jump_display_duration
            ):
                jump_y_offset = y_offset + 30
                cv2.putText(
                    image,
                    f"Jump Value: {last_jump_details['jump_value']}",
                    (10, jump_y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                )
                jump_y_offset += 30
                cv2.putText(
                    image,
                    f"Block Type: {last_jump_details['block_type']}",
                    (10, jump_y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                )

            # Draw pose landmarks
            mp_drawing.draw_landmarks(
                image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
            )

        # Display image
        cv2.imshow("Pose Detection", image)
        if cv2.waitKey(5) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()

