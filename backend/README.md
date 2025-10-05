# Blink Counter

A real-time eye blink detection and counter using OpenCV and MediaPipe.

## Features

- Real-time face and eye detection
- Accurate blink counting using Eye Aspect Ratio (EAR) algorithm
- Visual feedback with eye landmarks displayed
- FPS counter for performance monitoring
- Reset functionality
- Mirror mode for natural viewing

## How It Works

The blink detection uses the Eye Aspect Ratio (EAR) algorithm:

1. **Face Detection**: MediaPipe Face Mesh detects facial landmarks
2. **Eye Landmarks**: Extracts specific eye landmarks (6 points per eye)
3. **EAR Calculation**: Computes the Eye Aspect Ratio using the formula:
   ```
   EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
   ```
4. **Blink Detection**: When EAR drops below threshold for consecutive frames, a blink is counted

## Installation

1. Install Python 3.8 or higher

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script:
```bash
python blink_counter.py
```

### Controls

- **q**: Quit the application
- **r**: Reset the blink counter

### Display Information

The program displays:
- **Blinks**: Total number of blinks detected (red text)
- **EAR**: Current Eye Aspect Ratio value (green text)
- **Threshold**: EAR threshold for blink detection (blue text)
- **FPS**: Current frames per second (yellow text)
- Green dots mark the detected eye landmarks

## Configuration

You can adjust the blink detection sensitivity by modifying the `BlinkDetector` parameters in `main()`:

```python
detector = BlinkDetector(
    ear_threshold=0.25,  # Lower = more sensitive (default: 0.25)
    consec_frames=2      # Number of consecutive frames (default: 2)
)
```

- **ear_threshold**: EAR value below which eye is considered closed (typical range: 0.2 - 0.3)
- **consec_frames**: Number of consecutive frames eye must be closed to count as blink (reduces false positives)

## Troubleshooting

- **Camera not found**: Make sure your webcam is connected and not being used by another application
- **Low FPS**: Try reducing the camera resolution or using a more powerful computer
- **Blinks not detected**: Adjust the `ear_threshold` value (try lowering it to 0.23)
- **Too many false positives**: Increase `consec_frames` to 3 or adjust `ear_threshold` higher

## Requirements

- Python 3.8+
- Webcam
- Operating System: Windows, macOS, or Linux

## Credits

Based on the Eye Aspect Ratio (EAR) algorithm from the paper:
"Real-Time Eye Blink Detection using Facial Landmarks" by Soukupová and Čech
