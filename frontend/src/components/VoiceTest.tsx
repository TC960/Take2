import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Mic, Square, Play, Eye, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useBlinkTracker } from "@/hooks/use-blink-tracker";
import { useNavigate } from "react-router-dom";

const VoiceTest = () => {
  const navigate = useNavigate();
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const { toast } = useToast();
  
  // Blink tracking
  const { blinkCount, isTracking, stopTracking } = useBlinkTracker(isRecording);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const chunks: BlobPart[] = [];

      mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: "audio/webm" });
        setAudioBlob(blob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      timerRef.current = setInterval(() => {
        setRecordingTime((t) => {
          if (t >= 5) {
            stopRecording();
            return 5;
          }
          return t + 1;
        });
      }, 1000);
    } catch (error) {
      toast({
        title: "Microphone access denied",
        description: "Please allow microphone access to continue.",
        variant: "destructive",
      });
    }
  };

  const stopRecording = async () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      
      // Stop blink tracking and save data
      const blinkData = await stopTracking();
      if (blinkData) {
        sessionStorage.setItem('blinkAnalysisVoice', JSON.stringify(blinkData));
      }
    }
  };

  const playRecording = () => {
    if (audioBlob) {
      const audio = new Audio(URL.createObjectURL(audioBlob));
      audio.play();
    }
  };

  const analyzeVoice = async () => {
    if (!audioBlob) return;
    
    setIsAnalyzing(true);
    
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      
      const response = await fetch('http://localhost:8000/api/voice/analyze', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error('Analysis failed');
      }
      
      const result = await response.json();
      console.log('[VoiceTest] Analysis result:', result);
      
      // Save to sessionStorage
      sessionStorage.setItem('voiceAnalysis', JSON.stringify(result));
      
      toast({
        title: "Analysis Complete",
        description: "Voice analysis completed successfully!",
      });
      
      // Navigate to results
      setTimeout(() => {
        navigate('/results');
      }, 1000);
      
    } catch (error) {
      console.error('[VoiceTest] Voice analysis error:', error);
      toast({
        title: "Analysis Error",
        description: "Failed to analyze voice recording. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <section id="voice-test" className="min-h-screen flex items-center justify-center px-6 py-20">
      <Card className="w-full max-w-2xl p-8 md:p-12 space-y-8 text-center">
        <div className="space-y-2">
          <h2 className="text-3xl font-bold">Voice Analysis</h2>
          <p className="text-muted-foreground">
            Say "Ahhh" for 5 seconds to analyze voice patterns
          </p>
        </div>

        <div className="relative py-12">
          {isRecording && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-32 h-32 rounded-full bg-primary/20 animate-ping" />
            </div>
          )}
          
          <div className="relative z-10 flex flex-col items-center gap-6">
            <div className="text-6xl font-bold text-primary">
              {isRecording ? `${recordingTime}s` : audioBlob ? "✓" : "0s"}
            </div>
            
            {/* Blink counter */}
            {isTracking && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Eye className="h-4 w-4" />
                <span>Blinks tracked: {blinkCount}</span>
              </div>
            )}
            
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
                  Stop
                </Button>
              )}

              {audioBlob && !isRecording && (
                <>
                  <Button
                    onClick={playRecording}
                    size="lg"
                    variant="secondary"
                  >
                    <Play className="mr-2 h-5 w-5" />
                    Play Back
                  </Button>
                  <Button
                    onClick={() => setAudioBlob(null)}
                    size="lg"
                    variant="outline"
                  >
                    Retry
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>

        {audioBlob && !isAnalyzing && (
          <Button 
            onClick={analyzeVoice} 
            size="lg" 
            className="w-full glow-primary"
            disabled={isAnalyzing}
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Analyzing...
              </>
            ) : (
              "Analyze & View Results"
            )}
          </Button>
        )}
        
        {isAnalyzing && (
          <div className="text-sm text-muted-foreground">
            Analyzing your voice recording and eye blink patterns...
          </div>
        )}

        <div className="text-xs text-muted-foreground pt-4">
          Multi-modal analysis: Voice + Eye blink patterns
        </div>
      </Card>
    </section>
  );
};

export default VoiceTest;
