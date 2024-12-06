import cv2
import mediapipe as mp

# Initialize MediaPipe Pose and Drawing utilities
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Function to classify hand position relative to the head
def classify_hand_position(landmark, head_y, head_x):
    """
    Classifies the position of a hand landmark relative to the head.
    Args:
        landmark: The hand landmark to classify.
        head_y: The y-coordinate of the head landmark.
        head_x: The x-coordinate of the head landmark.
    Returns:
        A string indicating the position (above, at, below head and left/right/middle).
    """
    y_pos = "above head" if landmark.y < head_y else "below head" if landmark.y > head_y else "at head"
    x_pos = "left side" if landmark.x < head_x - 0.05 else "right side" if landmark.x > head_x + 0.05 else "middle"
    return f"{y_pos}, {x_pos}"

# Check hand proximity
def hands_close(left_hand, right_hand):
    """
    Determines if the hands are close together.
    Args:
        left_hand, right_hand: The landmarks for both hands.
    Returns:
        A string indicating whether the hands are "close" or "separated".
    """
    distance = ((left_hand.x - right_hand.x)**2 + (left_hand.y - right_hand.y)**2)**0.5
    return "close" if distance < 0.1 else "separated"

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

        # Annotate landmarks
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            # Extract landmarks
            landmarks = results.pose_landmarks.landmark
            head = landmarks[mp_pose.PoseLandmark.NOSE]
            left_hand = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
            right_hand = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]

            # Classify hand positions
            left_hand_position = classify_hand_position(left_hand, head.y, head.x)
            right_hand_position = classify_hand_position(right_hand, head.y, head.x)
            proximity = hands_close(left_hand, right_hand)

            # Display classification at the top of the screen
            status_text = f"Left hand: {left_hand_position}, Right hand: {right_hand_position}, {proximity}"
            left_status = "Left hand: " + left_hand_position
            right_status = "Right hand: " + right_hand_position
            proximity_status = proximity
            # cv2.putText(image, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            cv2.putText(image, left_status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            cv2.putText(image, right_status, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            cv2.putText(image, proximity_status, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

            # Label landmarks
            for idx, landmark in enumerate(landmarks):
                h, w, _ = image.shape
                x, y = int(landmark.x * w), int(landmark.y * h)
                cv2.putText(image, str(mp_pose.PoseLandmark(idx).name), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        # Display image
        cv2.imshow('Pose Detection', image)

        # Exit on pressing 'q'
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
