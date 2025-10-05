"""
Blink Detection and Counter using OpenCV and MediaPipe
This script detects face landmarks and counts eye blinks in real-time.
"""

import cv2
import mediapipe as mp
import time
from scipy.spatial import distance as dist


class BlinkDetector:
    def __init__(self, ear_threshold=0.25, consec_frames=2):
        """
        Initialize the blink detector.
        
        Args:
            ear_threshold: Eye Aspect Ratio threshold below which eye is considered closed
            consec_frames: Number of consecutive frames eye must be below threshold to count as blink
        """
        self.EAR_THRESHOLD = ear_threshold
        self.CONSEC_FRAMES = consec_frames
        
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Counter variables
        self.blink_counter = 0
        self.frame_counter = 0
        
        # Eye landmark indices for MediaPipe Face Mesh
        # Left eye indices
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]
        # Right eye indices  
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]
    
    def calculate_ear(self, eye_landmarks):
        """
        Calculate the Eye Aspect Ratio (EAR).
        
        Args:
            eye_landmarks: List of (x, y) coordinates for eye landmarks
            
        Returns:
            Eye Aspect Ratio value
        """
        # Compute the euclidean distances between the two sets of
        # vertical eye landmarks (x, y)-coordinates
        A = dist.euclidean(eye_landmarks[1], eye_landmarks[5])
        B = dist.euclidean(eye_landmarks[2], eye_landmarks[4])
        
        # Compute the euclidean distance between the horizontal
        # eye landmark (x, y)-coordinates
        C = dist.euclidean(eye_landmarks[0], eye_landmarks[3])
        
        # Compute the eye aspect ratio
        ear = (A + B) / (2.0 * C)
        
        return ear
    
    def get_eye_landmarks(self, landmarks, eye_indices, frame_width, frame_height):
        """
        Extract eye landmark coordinates.
        
        Args:
            landmarks: Face mesh landmarks
            eye_indices: Indices of eye landmarks
            frame_width: Width of the video frame
            frame_height: Height of the video frame
            
        Returns:
            List of (x, y) coordinates for the eye
        """
        eye_coords = []
        for idx in eye_indices:
            landmark = landmarks[idx]
            x = int(landmark.x * frame_width)
            y = int(landmark.y * frame_height)
            eye_coords.append((x, y))
        return eye_coords
    
    def process_frame(self, frame):
        """
        Process a single frame to detect blinks.
        
        Args:
            frame: Input video frame
            
        Returns:
            Processed frame with annotations
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_height, frame_width = frame.shape[:2]
        
        # Process the frame with MediaPipe
        results = self.face_mesh.process(rgb_frame)
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Get landmarks
                landmarks = face_landmarks.landmark
                
                # Extract left and right eye coordinates
                left_eye = self.get_eye_landmarks(
                    landmarks, self.LEFT_EYE, frame_width, frame_height
                )
                right_eye = self.get_eye_landmarks(
                    landmarks, self.RIGHT_EYE, frame_width, frame_height
                )
                
                # Calculate EAR for both eyes
                left_ear = self.calculate_ear(left_eye)
                right_ear = self.calculate_ear(right_eye)
                
                # Average EAR for both eyes
                avg_ear = (left_ear + right_ear) / 2.0
                
                # Draw eye contours
                for point in left_eye:
                    cv2.circle(frame, point, 2, (0, 255, 0), -1)
                for point in right_eye:
                    cv2.circle(frame, point, 2, (0, 255, 0), -1)
                
                # Check if EAR is below threshold
                if avg_ear < self.EAR_THRESHOLD:
                    self.frame_counter += 1
                else:
                    # If eyes were closed for sufficient number of frames, count as blink
                    if self.frame_counter >= self.CONSEC_FRAMES:
                        self.blink_counter += 1
                    self.frame_counter = 0
                
                # Display EAR value
                cv2.putText(
                    frame,
                    f"EAR: {avg_ear:.2f}",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )
        
        # Display blink counter
        cv2.putText(
            frame,
            f"Blinks: {self.blink_counter}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        )
        
        # Display threshold
        cv2.putText(
            frame,
            f"Threshold: {self.EAR_THRESHOLD}",
            (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 0, 0),
            2
        )
        
        return frame


def main():
    """Main function to run the blink detection."""
    # Initialize video capture (0 for default camera)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Initialize blink detector
    detector = BlinkDetector(ear_threshold=0.25, consec_frames=2)
    
    print("Starting blink detection...")
    print("Press 'q' to quit")
    print("Press 'r' to reset counter")
    
    fps_counter = 0
    fps_start_time = time.time()
    fps = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("Error: Failed to capture frame.")
            break
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Process frame
        frame = detector.process_frame(frame)
        
        # Calculate FPS
        fps_counter += 1
        if fps_counter >= 10:
            fps = fps_counter / (time.time() - fps_start_time)
            fps_counter = 0
            fps_start_time = time.time()
        
        # Display FPS
        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (10, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2
        )
        
        # Display instructions
        cv2.putText(
            frame,
            "Press 'q' to quit, 'r' to reset",
            (10, frame.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )
        
        # Show the frame
        cv2.imshow('Blink Counter', frame)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('r'):
            detector.blink_counter = 0
            print("Counter reset!")
    
    # Cleanup
    print(f"\nTotal blinks detected: {detector.blink_counter}")
    cap.release()
    cv2.destroyAllWindows()
    detector.face_mesh.close()


if __name__ == "__main__":
    main()
