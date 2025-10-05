import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useNavigate } from "react-router-dom";

const SAMPLE_TEXT = "The early morning sun cast long shadows across the quiet street as people began their daily routines. Coffee shops opened their doors, releasing the rich aroma of freshly brewed espresso into the crisp air. Commuters hurried past, their footsteps echoing on the pavement while they checked their phones and sipped their drinks. In the park, joggers followed their familiar paths, weaving between dog walkers and early cyclists. The city was waking up, transforming from its peaceful nighttime slumber into the bustling hub of activity it would remain throughout the day. Each person moved with purpose, contributing to the complex choreography of urban life that played out every morning in cities around the world.";

const TypingTest = () => {
  const navigate = useNavigate();
  const [input, setInput] = useState("");
  const [timeLeft, setTimeLeft] = useState(30);
  const [isActive, setIsActive] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [wpm, setWpm] = useState(0);
  const [accuracy, setAccuracy] = useState(100);
  const [analysisScore, setAnalysisScore] = useState<number | null>(null);
  const [analysisBand, setAnalysisBand] = useState<string>("");
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const sessionIdRef = useRef<string>("");
  const lastKeypressRef = useRef<number>(0);

  const words = SAMPLE_TEXT.split(" ");
  const typedWords = input.trim().split(" ");

  // WebSocket connection
  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket("ws://localhost:8000/ws/keystroke");

    ws.onopen = () => {
      console.log("[TypingTest] WebSocket connected");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "connected") {
        sessionIdRef.current = data.session_id;
        console.log("[TypingTest] Session ID:", data.session_id);
      } else if (data.type === "update") {
        // Update analysis metrics
        if (data.score !== undefined) {
          setAnalysisScore(data.score);
        }
        if (data.band) {
          setAnalysisBand(data.band);
        }
      } else if (data.type === "final") {
        console.log("[TypingTest] Final analysis:", data);
        if (data.score_0to1 !== undefined) {
          setAnalysisScore(data.score_0to1);
        }
        if (data.band) {
          setAnalysisBand(data.band);
        }

        // Store results in sessionStorage for Results page
        sessionStorage.setItem('typingAnalysis', JSON.stringify(data));
      }
    };

    ws.onerror = (error) => {
      console.error("[TypingTest] WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("[TypingTest] WebSocket closed");
    };

    wsRef.current = ws;

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "end" }));
      }
      ws.close();
    };
  }, []);

  // Timer effect
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isActive && timeLeft > 0) {
      interval = setInterval(() => {
        setTimeLeft((time) => {
          if (time <= 1) {
            setIsActive(false);
            setIsComplete(true);
            // Send end signal to WebSocket
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
              wsRef.current.send(JSON.stringify({ type: "end" }));
            }
            return 0;
          }
          return time - 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isActive, timeLeft]);

  // Input and metrics effect
  useEffect(() => {
    if (input.length > 0 && !isActive && !isComplete) {
      setIsActive(true);
    }

    // Calculate WPM
    const timeElapsed = (30 - timeLeft) / 60;
    if (timeElapsed > 0) {
      const wordsTyped = typedWords.length;
      setWpm(Math.round(wordsTyped / timeElapsed));
    }

    // Calculate accuracy
    let correctChars = 0;
    let totalChars = 0;
    for (let i = 0; i < typedWords.length; i++) {
      const word = words[i];
      const typedWord = typedWords[i];
      if (word) {
        totalChars += word.length;
        for (let j = 0; j < typedWord.length; j++) {
          if (typedWord[j] === word[j]) {
            correctChars++;
          }
        }
      }
    }
    if (totalChars > 0) {
      setAccuracy(Math.round((correctChars / totalChars) * 100));
    }
  }, [input, timeLeft, isActive, isComplete]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (isComplete) return;

    const now = performance.now();
    const timestamp = now / 1000; // Convert to seconds

    // Send keypress event to WebSocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        event_type: "press",
        key: e.key,
        timestamp: timestamp
      }));
    }

    lastKeypressRef.current = now;
  };

  const handleKeyUp = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (isComplete) return;

    const now = performance.now();
    const timestamp = now / 1000; // Convert to seconds

    // Send keyrelease event to WebSocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        event_type: "release",
        key: e.key,
        timestamp: timestamp
      }));
    }
  };

  const handleNext = () => {
    navigate('/voice-test');
  };

  const getWordClass = (index: number) => {
    if (index < typedWords.length) {
      if (typedWords[index] === words[index]) {
        return "text-primary";
      }
      return "text-destructive";
    }
    if (index === typedWords.length) {
      return "text-foreground underline";
    }
    return "text-muted-foreground";
  };

  const getBandColor = (band: string) => {
    switch(band) {
      case "LOW": return "text-green-500";
      case "MODERATE": return "text-yellow-500";
      case "HIGH": return "text-red-500";
      default: return "text-muted-foreground";
    }
  };

  return (
    <section id="typing-test" className="min-h-screen flex items-center justify-center px-6 py-20">
      <Card className="w-full max-w-4xl p-8 md:p-12 space-y-8">
        <div className="text-center space-y-2">
          <div className="text-6xl font-bold text-primary">{timeLeft}s</div>
          <div className="text-sm text-muted-foreground">Time Remaining</div>
        </div>

        <div className="flex justify-center gap-12 text-center">
          <div>
            <div className="text-3xl font-bold">{wpm}</div>
            <div className="text-sm text-muted-foreground">WPM</div>
          </div>
          <div>
            <div className="text-3xl font-bold">{accuracy}%</div>
            <div className="text-sm text-muted-foreground">Accuracy</div>
          </div>
          {analysisScore !== null && (
            <div>
              <div className={`text-3xl font-bold ${getBandColor(analysisBand)}`}>
                {analysisBand || "---"}
              </div>
              <div className="text-sm text-muted-foreground">PD Risk</div>
            </div>
          )}
        </div>

        <div className="text-2xl leading-relaxed p-6 bg-muted/30 rounded-lg min-h-[200px]">
          {words.map((word, index) => (
            <span key={index} className={getWordClass(index)}>
              {word}{" "}
            </span>
          ))}
        </div>

        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => !isComplete && setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onKeyUp={handleKeyUp}
          className="w-full bg-transparent border-2 border-border focus:border-primary outline-none text-xl p-6 transition-colors rounded-lg resize-none min-h-[200px]"
          placeholder={isComplete ? "Test complete!" : "Start typing the text above..."}
          autoFocus
          disabled={isComplete}
        />

        {isComplete && (
          <div className="flex flex-col items-center gap-4 pt-4">
            {analysisScore !== null && (
              <div className="text-center">
                <div className="text-lg text-muted-foreground">
                  Analysis Score: <span className={`font-bold ${getBandColor(analysisBand)}`}>
                    {(analysisScore * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            )}
            <Button onClick={handleNext} size="lg" className="glow-primary">
              Next: Voice Analysis
            </Button>
          </div>
        )}

        <div className="text-center text-xs text-muted-foreground pt-4">
          {sessionIdRef.current && `Session ID: ${sessionIdRef.current}`}
        </div>
      </Card>
    </section>
  );
};

export default TypingTest;
