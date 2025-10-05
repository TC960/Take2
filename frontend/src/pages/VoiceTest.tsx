import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useNavigate } from "react-router-dom";
import { Mic, Square, Loader2 } from "lucide-react";

const VoiceTestPage = () => {
  const navigate = useNavigate();
  const [isRecording, setIsRecording] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [analysisResult, setAnalysisResult] = useState<any>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setAudioBlob(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => {
          if (prev >= 10) {
            stopRecording();
            return 10;
          }
          return prev + 1;
        });
      }, 1000);

    } catch (error) {
      console.error("Error accessing microphone:", error);
      alert("Could not access microphone. Please check permissions.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);

      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const analyzeVoice = async () => {
    if (!audioBlob) return;

    setIsAnalyzing(true);

    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.wav');

      const response = await fetch('http://localhost:8000/api/voice/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const result = await response.json();
      setAnalysisResult(result);

      // Store result in sessionStorage for results page
      sessionStorage.setItem('voiceAnalysis', JSON.stringify(result));

    } catch (error) {
      console.error("Voice analysis error:", error);
      alert("Voice analysis failed. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleNext = () => {
    navigate('/results');
  };

  const handleRetry = () => {
    setAudioBlob(null);
    setAnalysisResult(null);
    setRecordingTime(0);
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-20 bg-background">
      <Card className="w-full max-w-3xl p-8 md:p-12 space-y-8">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold">Voice Analysis</h1>
          <p className="text-muted-foreground">
            Record a 10-second voice sample for analysis
          </p>
        </div>

        <div className="flex flex-col items-center gap-8">
          {/* Recording Status */}
          <div className="text-center space-y-4">
            {isRecording ? (
              <>
                <div className="relative w-32 h-32 mx-auto">
                  <div className="absolute inset-0 bg-red-500/20 rounded-full animate-pulse" />
                  <div className="absolute inset-4 bg-red-500 rounded-full flex items-center justify-center">
                    <Mic className="w-12 h-12 text-white" />
                  </div>
                </div>
                <div className="text-5xl font-bold text-red-500">{recordingTime}s</div>
                <p className="text-sm text-muted-foreground">Recording in progress...</p>
              </>
            ) : audioBlob ? (
              <>
                <div className="w-32 h-32 mx-auto bg-green-500/20 rounded-full flex items-center justify-center">
                  <div className="w-24 h-24 bg-green-500 rounded-full flex items-center justify-center">
                    <Mic className="w-12 h-12 text-white" />
                  </div>
                </div>
                <p className="text-sm text-green-500 font-medium">Recording complete!</p>
              </>
            ) : (
              <>
                <div className="w-32 h-32 mx-auto bg-primary/20 rounded-full flex items-center justify-center">
                  <div className="w-24 h-24 bg-primary rounded-full flex items-center justify-center">
                    <Mic className="w-12 h-12 text-white" />
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">Ready to record</p>
              </>
            )}
          </div>

          {/* Instructions */}
          {!audioBlob && !isRecording && (
            <div className="text-center space-y-2 max-w-md">
              <h3 className="font-semibold">Instructions:</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Click the button below to start recording</li>
                <li>• Speak naturally for 10 seconds</li>
                <li>• Read a passage or describe your day</li>
                <li>• Ensure you're in a quiet environment</li>
              </ul>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-4">
            {!audioBlob && !isRecording && (
              <Button
                onClick={startRecording}
                size="lg"
                className="glow-primary"
              >
                <Mic className="mr-2 h-5 w-5" />
                Start Recording
              </Button>
            )}

            {isRecording && (
              <Button
                onClick={stopRecording}
                size="lg"
                variant="destructive"
              >
                <Square className="mr-2 h-5 w-5" />
                Stop Recording
              </Button>
            )}

            {audioBlob && !analysisResult && (
              <>
                <Button
                  onClick={handleRetry}
                  size="lg"
                  variant="outline"
                >
                  Retry
                </Button>
                <Button
                  onClick={analyzeVoice}
                  size="lg"
                  className="glow-primary"
                  disabled={isAnalyzing}
                >
                  {isAnalyzing ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    "Analyze Voice"
                  )}
                </Button>
              </>
            )}

            {analysisResult && (
              <div className="flex flex-col gap-4 w-full">
                <div className="p-4 bg-muted/50 rounded-lg">
                  <h3 className="font-semibold mb-2">Analysis Complete</h3>
                  <p className="text-sm text-muted-foreground">
                    Your voice analysis has been completed successfully.
                  </p>
                </div>
                <div className="flex gap-4">
                  <Button
                    onClick={handleRetry}
                    size="lg"
                    variant="outline"
                  >
                    Retry
                  </Button>
                  <Button
                    onClick={handleNext}
                    size="lg"
                    className="glow-primary flex-1"
                  >
                    View Results
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="text-center text-xs text-muted-foreground pt-4">
          Your audio is processed locally and securely
        </div>
      </Card>
    </div>
  );
};

export default VoiceTestPage;
