import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Mic, Square, Play } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const VoiceTest = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const { toast } = useToast();

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

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  };

  const playRecording = () => {
    if (audioBlob) {
      const audio = new Audio(URL.createObjectURL(audioBlob));
      audio.play();
    }
  };

  const completeTest = () => {
    setIsComplete(true);
    document.getElementById('results')?.scrollIntoView({ behavior: 'smooth' });
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

        {audioBlob && !isComplete && (
          <Button onClick={completeTest} size="lg" className="w-full glow-primary">
            Complete Assessment
          </Button>
        )}

        <div className="text-xs text-muted-foreground pt-4">
          Voice tremor analysis algorithm in development
        </div>
      </Card>
    </section>
  );
};

export default VoiceTest;
