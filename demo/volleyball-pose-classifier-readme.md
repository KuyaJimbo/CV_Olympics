# Volleyball Pose Classifier and KILLBLOCK Game

## Project Overview

This project implements a computer vision-based volleyball pose classifier that allows users to control a player in a volleyball game using body movements and poses.

## Dependencies

The project requires the following Python libraries:

- pygame
- opencv-python (cv2)
- mediapipe
- numpy

### Installation

You can install the dependencies using pip:

```bash
pip install pygame opencv-python mediapipe numpy
```

#### Recommended: Virtual Environment

It's recommended to use a virtual environment to manage dependencies:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install pygame opencv-python mediapipe numpy
```

## Prerequisites

- Python 3.7+ recommended
- Webcam (recommended)
- Pip package manager

[... rest of the previous README content remains the same ...]

## Project Structure

- `classifier.py`: Main classifier using webcam input
- `video_test.py`: Allows testing with video file input
- `game.py`: The KILLBLOCK volleyball game
- `test.mp4`: Sample video for testing

## Testing the Volleyball Pose Classifier (Without Webcam)

### Steps:

1. Extract the `demo.zip` file
2. Open terminal and navigate to the extracted folder
3. Run the video test script:
   ```
   python video_test.py
   ```
4. When prompted, enter the video file path
   - A `test.mp4` is provided for your convenience

## Using the Volleyball Pose Classifier (With Webcam)

### Setup and Requirements:

- Ensure a webcam is connected and active
- Provide sufficient space for movement

### Steps:

1. Extract the `demo.zip` file
2. Open terminal and navigate to the extracted folder
3. Run the classifier:
   ```
   python classifier.py
   ```
4. Position yourself:
   - Step back to ensure full body visibility
   - Hands should remain in-frame during movements
5. Right-click the application to recalculate baselines
   - Visualizations will show floor and knee levels

### Pose Recognition:

- Top-left corner indicates pose recognition status
- Jump detection occurs when feet level exceeds baseline knee level

## Playing KILLBLOCK

### Steps:

1. Extract the `demo.zip` file
2. Open terminal and navigate to the extracted folder
3. Launch the game:
   ```
   python game.py
   ```
4. Position yourself similar to the classifier setup
5. Right-click to recalculate baselines
6. Move and Jump to control the player
7. Lift your arms above your head to block (and have fun!)

## Gameplay Tips

### Jump Mechanics:

- Jumps trigger when feet rise above baseline knee level
- Maximize jump height by:
  - Lowering head
  - Bending knees
  - Moving hands below knee level

### Blocking Strategies:

- Keep arms extended upwards after jumping to maintain block (even after you yourself touch the ground)
- KillBlock is possible when:
  1. Spiker hits the ball downward
  2. Blocking hit box (white outline) intersects the ball

## Troubleshooting

- If experiencing lag, maintain extended arm position after jumping
- Run `classifier.py` first to understand optimal positioning

## Additional Notes

- Ensure consistent lighting and background for best results
- Calibrate baseline by right-clicking the application
