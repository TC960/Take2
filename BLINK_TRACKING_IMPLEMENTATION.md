# Eye Blink Tracking Implementation

## Overview
Eye blink tracking has been integrated into both the Typing Test and Voice Test to provide multi-modal Parkinson's Disease screening analysis.

## Features Implemented

### 1. Reusable Blink Tracking Hook (`use-blink-tracker.ts`)
- **Location**: `frontend/src/hooks/use-blink-tracker.ts`
- **Features**:
  - Real-time eye blink detection using webcam
  - Tracks blink count, timestamps, and Eye Aspect Ratio (EAR) values
  - Automatically starts/stops based on test activity
  - Sends data to backend API endpoint `/api/blink/analyze`
  - Returns comprehensive blink statistics

### 2. Typing Test Integration
- **Location**: `frontend/src/components/TypingTest.tsx`
- **Changes**:
  - Added blink counter display in real-time
  - Eye icon shows current blink count during test
  - Automatically saves blink data to `sessionStorage` when test completes
  - Storage key: `blinkAnalysisTyping`

### 3. Voice Test Integration
- **Location**: `frontend/src/components/VoiceTest.tsx`
- **Changes**:
  - Blink tracking starts when recording begins
  - Shows live blink count during recording
  - "Analyze & View Results" button replaces "Complete Assessment"
  - Sends voice audio to backend for analysis
  - Automatically saves blink data to `sessionStorage`
  - Storage key: `blinkAnalysisVoice`
  - Navigates to results page after analysis

### 4. Results Page Enhancement
- **Location**: `frontend/src/pages/Results.tsx`
- **Changes**:
  - Displays eye blink statistics from both tests
  - Shows blink count, blink rate (per minute), and duration
  - Includes educational text about normal blink rates (15-20/min)
  - Integrates blink data into overall risk calculation
  - Weighted risk calculation:
    - Typing: 30%
    - Voice: 35%
    - Eye Blink: 35%

## How It Works

### During Tests:
1. **Camera Access**: Requests webcam access when test starts
2. **Real-time Detection**: Processes video frames to detect eye blinks
3. **Visual Feedback**: Shows live blink count to user
4. **Data Collection**: Stores timestamps and metrics

### After Tests:
1. **Data Transmission**: Sends blink data to backend API
2. **Storage**: Saves results in browser sessionStorage
3. **Analysis**: Backend calculates blink rate and risk indicators
4. **Display**: Results page shows comprehensive multi-modal analysis

## Technical Details

### Blink Detection Algorithm:
- Uses **MediaPipe Face Mesh** (same as backend `blink_counter.py`)
- Eye Aspect Ratio (EAR) calculation with facial landmarks
- Eye landmark indices:
  - LEFT_EYE: [362, 385, 387, 263, 373, 380]
  - RIGHT_EYE: [33, 160, 158, 133, 153, 144]
- Threshold: EAR < 0.25 indicates closed eye
- Requires 2 consecutive frames below threshold to count as blink
- Processes video at native frame rate for accuracy
- Formula: `EAR = (A + B) / (2.0 * C)` where A, B are vertical distances and C is horizontal

### API Integration:
- Endpoint: `POST /api/blink/analyze`
- Request body:
  ```json
  {
    "blink_count": number,
    "duration_seconds": number,
    "blink_timestamps": number[],
    "ear_values": number[]
  }
  ```
- Response includes blink_rate, variability, and risk_indicators

### Risk Assessment:
- Normal blink rate: 15-20 blinks/minute
- PD typically shows: 5-10 blinks/minute
- Risk score calculated as: `(20 - blink_rate) / 15`
- Clamped between 0.0 and 1.0

## User Experience

### Privacy:
- Camera access requested only during tests
- No video is recorded or transmitted
- Only statistical data (blink counts, timestamps) is stored
- Camera is automatically released after test

### Accessibility:
- Optional feature - tests work without camera
- Clear visual indicators when tracking is active
- Non-intrusive display of blink count
- Works in low-light conditions

## Future Enhancements

Potential improvements:
1. ✅ ~~Use MediaPipe Face Mesh for more accurate detection~~ (IMPLEMENTED)
2. Add blink pattern analysis (regularity, clustering)
3. Implement eyelid speed analysis
4. Add calibration phase for personalized thresholds
5. Compare blink rates between tests for consistency analysis
6. Add visual feedback showing detected eye landmarks
7. Implement adaptive threshold based on lighting conditions

## Dependencies

### Frontend:
- React hooks (useState, useEffect, useRef, useCallback)
- **@mediapipe/face_mesh** v0.4.x - Face landmark detection
- **@mediapipe/camera_utils** v0.3.x - Camera utilities
- Browser MediaDevices API (webcam access)

### Backend:
- FastAPI endpoint `/api/blink/analyze`
- NumPy for statistical calculations
- SciPy for advanced metrics (already in requirements.txt)

## Testing Checklist

- [x] Camera permission request works
- [x] Blink detection during typing test
- [x] Blink detection during voice test
- [x] Data saved to sessionStorage
- [x] Results display correctly
- [x] Risk calculation includes blink data
- [x] Camera released after tests
- [x] No linting errors
- [x] TypeScript types defined
- [x] Error handling implemented

## Browser Compatibility

Requires:
- Modern browser with MediaDevices API support
- Chrome 53+, Firefox 36+, Safari 11+, Edge 79+
- Webcam/camera device
- HTTPS (required for getUserMedia in production)

## Notes

- The implementation uses **MediaPipe Face Mesh**, the same proven algorithm as the backend
- Uses the exact same eye landmark indices and EAR calculation as `blink_counter.py`
- Camera quality and lighting conditions affect accuracy
- Users can decline camera access - tests will still work without blink tracking
- MediaPipe models are loaded from CDN (jsdelivr.net)
- Compatible with both Python and JavaScript implementations
