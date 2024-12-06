import cv2
import mediapipe as mp
import time

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Threshold for jump detection (tune based on use case)
JUMP_THRESHOLD = 0.1  # Difference in normalized coordinates

# Variables to track jump
baseline_ankle_y = None
last_jump_time = 0
JUMP_COOLDOWN = 1  # Seconds to prevent detecting the same jump repeatedly

# Start video capture
cap = cv2.VideoCapture(0)
with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue

        # Process image with MediaPipe Pose
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)

        # Annotate landmarks and detect jump
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            # Extract landmarks
            landmarks = results.pose_landmarks.landmark
            left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
            right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]

            # Calculate average ankle height
            avg_ankle_y = (left_ankle.y + right_ankle.y) / 2

            # Initialize baseline if not set
            if baseline_ankle_y is None:
                baseline_ankle_y = avg_ankle_y

            # Detect jump based on significant upward movement
            if avg_ankle_y < baseline_ankle_y - JUMP_THRESHOLD:
                current_time = time.time()
                if current_time - last_jump_time > JUMP_COOLDOWN:
                    cv2.putText(image, "Jump Detected!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    print("Jump detected!")
                    last_jump_time = current_time

            # Update baseline dynamically (optional, can add smoothing/filtering)
            baseline_ankle_y = min(baseline_ankle_y, avg_ankle_y)

        # Display image
        cv2.imshow('Jump Detection', image)

        # Exit on pressing 'q'
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
