import cv2
import mediapipe as mp
import os
import time
import numpy as np

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
update_interval = 0.3  # 300 ms
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
    nose = landmarks[mp_pose.PoseLandmark.NOSE]
    return nose.y > Baseline_FloorY + (Baseline_Height * threshold)

def CheckKneesBent(landmarks, threshold=0.2):
    left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
    right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
    avg_knee_y = (left_knee.y + right_knee.y) / 2
    return avg_knee_y > Baseline_KneeLevel + (abs(Baseline_KneeLevel - Baseline_FloorY) * threshold)

def CheckHandsBelowKnees(landmarks):
    left_hand = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
    right_hand = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
    left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
    right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
    return left_hand.y > left_knee.y and right_hand.y > right_knee.y

def CheckHandsBelowHips(landmarks):
    left_hand = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
    right_hand = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
    return left_hand.y > left_hip.y and right_hand.y > right_hip.y

def CheckHandsBelowShoulders(landmarks):
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
    return jump_value

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

# Main Program
def main():
    video_path = input("Enter the file path of the video: ")

    if not os.path.exists(video_path):
        print(f"Error: The file '{video_path}' does not exist. Please check the path and try again.")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Unable to open the video file.")
        return

    print("Processing video with annotations...")
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        global last_update_time, last_jump_time, last_jump_details
        baseline_set = False

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("End of video or cannot read frame.")
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark

                if not baseline_set:
                    GetBaselines(landmarks)
                    baseline_set = True

                if time.time() - last_update_time >= update_interval:
                    UpdatePoseDict(landmarks)
                    last_update_time = time.time()

                jump_detected = CheckDetectJump(landmarks)

                if jump_detected:
                    last_jump_time = time.time()
                    last_jump_details = {
                        "jump_value": GetJumpPower(),
                        "block_type": GetBlockType(landmarks),
                        "time": time.time(),
                    }

                # Draw pose landmarks
                mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                # Draw baselines
                if baseline_set:
                    floor_line = int(frame.shape[0] * Baseline_FloorY)
                    knee_line = int(frame.shape[0] * Baseline_KneeLevel)

                    cv2.line(frame, (0, floor_line), (frame.shape[1], floor_line), (255, 0, 0), 2)  # Blue for floor
                    cv2.line(frame, (0, knee_line), (frame.shape[1], knee_line), (0, 255, 0), 2)  # Green for knee level

                # Display pose indicators
                y_offset = 30
                pose_indicators = [
                    ("Head Lowered", any(pose_dictionary["HeadLowered"])),
                    ("Knees Bent", any(pose_dictionary["KneesBent"])),
                    ("Hands Below Knees", any(pose_dictionary["HandsBelowKnees"])),
                    ("Hands Below Hips", any(pose_dictionary["HandsBelowHips"])),
                    ("Hands Below Shoulders", any(pose_dictionary["HandsBelowShoulders"])),
                ]

                for name, state in pose_indicators:
                    color = (0, 255, 0) if state else (0, 0, 255)
                    cv2.putText(frame, name, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    y_offset += 30

                # Display jump details if recently detected
                if (last_jump_details and 
                    time.time() - last_jump_details["time"] < jump_display_duration):
                    jump_y_offset = y_offset + 30
                    cv2.putText(
                        frame,
                        f"Jump Value: {last_jump_details['jump_value']}",
                        (10, jump_y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 255),
                        2,
                    )
                    jump_y_offset += 30
                    cv2.putText(
                        frame,
                        f"Block Type: {last_jump_details['block_type']}",
                        (10, jump_y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 255),
                        2,
                    )

            cv2.imshow("Annotated Video", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()