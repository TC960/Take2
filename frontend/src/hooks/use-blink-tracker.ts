import { useEffect, useRef, useState, useCallback } from 'react';
import { FaceMesh } from '@mediapipe/face_mesh';
import { Camera } from '@mediapipe/camera_utils';

interface BlinkData {
  blinkCount: number;
  duration: number;
  blinkTimestamps: number[];
  earValues: number[];
  startTime: number;
}

// Eye landmark indices for MediaPipe Face Mesh (same as backend blink_counter.py)
const LEFT_EYE = [362, 385, 387, 263, 373, 380];
const RIGHT_EYE = [33, 160, 158, 133, 153, 144];

const EAR_THRESHOLD = 0.25;
const CONSEC_FRAMES = 2;

export function useBlinkTracker(isActive: boolean) {
  const [blinkCount, setBlinkCount] = useState(0);
  const [isTracking, setIsTracking] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const cameraRef = useRef<Camera | null>(null);
  const faceMeshRef = useRef<FaceMesh | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  
  // Blink detection state
  const blinkDataRef = useRef<BlinkData>({
    blinkCount: 0,
    duration: 0,
    blinkTimestamps: [],
    earValues: [],
    startTime: 0
  });
  
  const consecutiveClosedFramesRef = useRef(0);

  // Calculate euclidean distance between two points
  const euclideanDistance = useCallback((point1: any, point2: any) => {
    const dx = point1.x - point2.x;
    const dy = point1.y - point2.y;
    return Math.sqrt(dx * dx + dy * dy);
  }, []);

  // Calculate Eye Aspect Ratio (EAR) - same as backend
  const calculateEAR = useCallback((eyeLandmarks: any[]) => {
    if (!eyeLandmarks || eyeLandmarks.length < 6) return 1.0;
    
    try {
      // Compute the euclidean distances between the two sets of vertical eye landmarks
      const A = euclideanDistance(eyeLandmarks[1], eyeLandmarks[5]);
      const B = euclideanDistance(eyeLandmarks[2], eyeLandmarks[4]);
      
      // Compute the euclidean distance between the horizontal eye landmarks
      const C = euclideanDistance(eyeLandmarks[0], eyeLandmarks[3]);
      
      // Compute the eye aspect ratio
      const ear = (A + B) / (2.0 * C);
      
      return ear;
    } catch (e) {
      return 1.0;
    }
  }, [euclideanDistance]);

  // Extract eye landmarks from face mesh results
  const getEyeLandmarks = useCallback((landmarks: any[], eyeIndices: number[]) => {
    return eyeIndices.map(idx => landmarks[idx]);
  }, []);

  // Process face mesh results
  const onResults = useCallback((results: any) => {
    if (!isActive || !results.multiFaceLandmarks || results.multiFaceLandmarks.length === 0) {
      return;
    }

    const faceLandmarks = results.multiFaceLandmarks[0];
    
    // Extract left and right eye landmarks
    const leftEye = getEyeLandmarks(faceLandmarks, LEFT_EYE);
    const rightEye = getEyeLandmarks(faceLandmarks, RIGHT_EYE);
    
    // Calculate EAR for both eyes
    const leftEAR = calculateEAR(leftEye);
    const rightEAR = calculateEAR(rightEye);
    
    // Average EAR for both eyes
    const avgEAR = (leftEAR + rightEAR) / 2.0;
    
    // Store EAR value
    blinkDataRef.current.earValues.push(avgEAR);
    
    // Check if EAR is below threshold
    if (avgEAR < EAR_THRESHOLD) {
      consecutiveClosedFramesRef.current += 1;
    } else {
      // If eyes were closed for sufficient number of frames, count as blink
      if (consecutiveClosedFramesRef.current >= CONSEC_FRAMES) {
        const now = performance.now() / 1000;
        blinkDataRef.current.blinkCount += 1;
        blinkDataRef.current.blinkTimestamps.push(now);
        setBlinkCount(blinkDataRef.current.blinkCount);
        console.log(`[BlinkTracker] Blink detected! Total: ${blinkDataRef.current.blinkCount}, EAR: ${avgEAR.toFixed(3)}`);
      }
      consecutiveClosedFramesRef.current = 0;
    }
  }, [isActive, calculateEAR, getEyeLandmarks]);

  const startTracking = useCallback(async () => {
    try {
      console.log('[BlinkTracker] Initializing...');
      
      // Create video element
      const video = document.createElement('video');
      video.style.display = 'none';
      document.body.appendChild(video);
      videoRef.current = video;
      
      // Initialize MediaPipe Face Mesh
      const faceMesh = new FaceMesh({
        locateFile: (file) => {
          return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
        }
      });
      
      faceMesh.setOptions({
        maxNumFaces: 1,
        refineLandmarks: true,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
      });
      
      faceMesh.onResults(onResults);
      faceMeshRef.current = faceMesh;
      
      // Initialize camera
      const camera = new Camera(video, {
        onFrame: async () => {
          if (faceMeshRef.current && isActive) {
            await faceMeshRef.current.send({ image: video });
          }
        },
        width: 640,
        height: 480
      });
      
      cameraRef.current = camera;
      
      // Reset counters
      blinkDataRef.current = {
        blinkCount: 0,
        duration: 0,
        blinkTimestamps: [],
        earValues: [],
        startTime: performance.now() / 1000
      };
      consecutiveClosedFramesRef.current = 0;
      setBlinkCount(0);
      
      // Start camera
      await camera.start();
      
      setIsTracking(true);
      console.log('[BlinkTracker] Started successfully');
      
      return true;
    } catch (error) {
      console.error('[BlinkTracker] Failed to start:', error);
      return false;
    }
  }, [isActive, onResults]);

  const stopTracking = useCallback(async (): Promise<BlinkData | null> => {
    console.log('[BlinkTracker] Stopping...');
    
    // Stop camera
    if (cameraRef.current) {
      cameraRef.current.stop();
      cameraRef.current = null;
    }
    
    // Close face mesh
    if (faceMeshRef.current) {
      faceMeshRef.current.close();
      faceMeshRef.current = null;
    }
    
    // Remove video element
    if (videoRef.current) {
      videoRef.current.remove();
      videoRef.current = null;
    }
    
    setIsTracking(false);
    
    // Calculate final duration
    const endTime = performance.now() / 1000;
    blinkDataRef.current.duration = endTime - blinkDataRef.current.startTime;
    
    console.log(`[BlinkTracker] Stopped. Total blinks: ${blinkDataRef.current.blinkCount}, Duration: ${blinkDataRef.current.duration.toFixed(1)}s`);
    
    // Send to backend API
    try {
      const response = await fetch('http://localhost:8000/api/blink/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          blink_count: blinkDataRef.current.blinkCount,
          duration_seconds: blinkDataRef.current.duration,
          blink_timestamps: blinkDataRef.current.blinkTimestamps,
          ear_values: blinkDataRef.current.earValues
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('[BlinkTracker] Analysis result:', result);
        return {
          ...blinkDataRef.current,
          ...result
        };
      }
    } catch (error) {
      console.error('[BlinkTracker] Failed to send data to backend:', error);
    }
    
    return blinkDataRef.current;
  }, []);

  useEffect(() => {
    if (isActive && !isTracking) {
      startTracking();
    } else if (!isActive && isTracking) {
      stopTracking();
    }
    
    return () => {
      if (isTracking) {
        stopTracking();
      }
    };
  }, [isActive, isTracking, startTracking, stopTracking]);

  return {
    blinkCount,
    isTracking,
    stopTracking,
    getBlinkData: () => blinkDataRef.current
  };
}