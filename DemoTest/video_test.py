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
update_interval = 0.1  # 100 ms
jump_cooldown = 1  # Cooldown period in seconds
last_update_time = time.time()
last_jump_time = 0
jump_display_duration = 3  # seconds to display jump details
last_jump_details = None
jump_details_timer = 0

# Define helper functions (from classifier.py)
def CloseEnough(point1, point2, threshold=0.1):
    distance = np.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)
    return distance < threshold

def GetBaselines(landmarks):
    global Baseline_FloorY, Baseline_Height, Baseline_KneeLevel
    left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
    right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
    Baseline_FloorY = (left_ankle.y + right_ankle.y) / 2
    nose = landmarks[mp_pose.PoseLandmark.NOSE]
    Baseline_Height = nose.y - Baseline_FloorY
    left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
    right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
    Baseline_KneeLevel = (left_knee.y + right_knee.y) / 2

def CheckDetectJump(landmarks):
    left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
    right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
    avg_feet_y = (left_ankle.y + right_ankle.y) / 2
    return avg_feet_y < Baseline_KneeLevel

def UpdatePoseDict(landmarks):
    global pose_dictionary
    pose_dictionary["HeadLowered"].append(landmarks[mp_pose.PoseLandmark.NOSE].y > Baseline_FloorY + (Baseline_Height * 0.6))
    pose_dictionary["KneesBent"].append(landmarks[mp_pose.PoseLandmark.LEFT_KNEE].y > Baseline_FloorY + (Baseline_KneeLevel * 0.7))
    pose_dictionary["HandsBelowKnees"].append(
        landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y > landmarks[mp_pose.PoseLandmark.LEFT_KNEE].y and
        landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y > landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].y
    )
    pose_dictionary["HandsBelowHips"].append(
        landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y > landmarks[mp_pose.PoseLandmark.LEFT_HIP].y and
        landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y > landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y
    )
    pose_dictionary["HandsBelowShoulders"].append(
        landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y > landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y and
        landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y > landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y
    )
    for key in pose_dictionary:
        if len(pose_dictionary[key]) > 5:
            pose_dictionary[key].pop(0)

# Main Program
video_path = input("Enter the file path of the video: ")

if not os.path.exists(video_path):
    print(f"Error: The file '{video_path}' does not exist. Please check the path and try again.")
else:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Unable to open the video file.")
    else:
        print("Processing video with annotations...")
        with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
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
                            "time": time.time()
                        }

                    mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                    y_offset = 30
                    for name, state in pose_dictionary.items():
                        color = (0, 255, 0) if any(state) else (0, 0, 255)
                        cv2.putText(frame, name, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                        y_offset += 30

                cv2.imshow("Annotated Video", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        cap.release()
        cv2.destroyAllWindows()
