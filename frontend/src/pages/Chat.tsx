import { useState, useRef, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useNavigate } from "react-router-dom";
import { Send, Bot, User, ArrowLeft, Loader2 } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

const ChatPage = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I'm your AI assistant for take2. I can answer questions about Parkinson's disease screening, explain your test results, or provide information about the research behind our methods. How can I help you today?",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // TODO: Replace with actual RAG API endpoint
      // For now, using a mock response
      await new Promise(resolve => setTimeout(resolve, 1000));

      const assistantMessage: Message = {
        role: "assistant",
        content: getMockResponse(input),
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage: Message = {
        role: "assistant",
        content: "I'm sorry, I encountered an error. Please try again.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const getMockResponse = (query: string): string => {
    const lowerQuery = query.toLowerCase();

    if (lowerQuery.includes("result") || lowerQuery.includes("score")) {
      return "Your assessment results combine data from multiple modalities (typing, voice, eye blink) to provide a comprehensive risk evaluation. A 'LOW' risk indicates patterns within normal range, while 'MODERATE' or 'HIGH' suggest you may benefit from clinical consultation. Remember, this is a screening tool, not a diagnosis. Would you like me to explain any specific aspect of your results?";
    }

    if (lowerQuery.includes("typing") || lowerQuery.includes("keystroke")) {
      return "The typing test analyzes your keystroke dynamics - the timing patterns when you press and release keys. Research shows that PD affects motor control, leading to increased variability in hold times (how long you press keys) and flight times (intervals between keystrokes). We also measure asymmetry between left and right hands, which can indicate lateralized motor symptoms.";
    }

    if (lowerQuery.includes("voice") || lowerQuery.includes("speech")) {
      return "Voice analysis examines acoustic features like pitch variation, tremor frequency (4-6 Hz), and spectral characteristics. PD affects the vocal apparatus through rigidity and bradykinesia, causing reduced pitch range (monotone speech), increased breathiness, and vocal tremor. Our system uses spectrogram analysis combined with AI to detect these subtle changes.";
    }

    if (lowerQuery.includes("blink") || lowerQuery.includes("eye")) {
      return "Eye blink rate is modulated by dopamine in the basal ganglia. Normal blink rate is 15-20 blinks per minute, but PD patients typically show 5-10 blinks per minute due to striatal dopamine depletion. Reduced spontaneous blinking can appear before motor symptoms become clinically apparent.";
    }

    if (lowerQuery.includes("accurate") || lowerQuery.includes("reliable")) {
      return "Our screening tool is based on peer-reviewed research showing digital biomarkers can detect PD-related changes. However, accuracy depends on multiple factors: baseline establishment (multiple sessions improve reliability), confounding variables (stress, fatigue, other conditions), and longitudinal tracking (trends over time are more informative than single assessments). This is why we emphasize this is a screening tool requiring professional clinical follow-up.";
    }

    if (lowerQuery.includes("next") || lowerQuery.includes("do now")) {
      return "If your risk assessment shows MODERATE or HIGH, consider: (1) Scheduling a consultation with a neurologist or movement disorder specialist, (2) Documenting any symptoms you've noticed (tremor, rigidity, slowness, balance issues), (3) Repeating this assessment in 2-4 weeks to track changes, (4) Maintaining the session IDs for longitudinal comparison. If LOW risk, continue periodic monitoring and establish your personal baseline.";
    }

    if (lowerQuery.includes("parkinson") || lowerQuery.includes("pd")) {
      return "Parkinson's Disease (PD) is a progressive neurodegenerative disorder affecting movement, caused by loss of dopamine-producing neurons in the substantia nigra. Cardinal symptoms include: tremor at rest, rigidity (muscle stiffness), bradykinesia (slowness of movement), and postural instability. Early detection is crucial as treatments are most effective in early stages. Digital biomarkers like those assessed by take2 can detect subtle changes before clinical diagnosis.";
    }

    if (lowerQuery.includes("research") || lowerQuery.includes("science")) {
      return "Our methods are based on published research in scientific journals. Key studies include work by Giancardo et al. on keystroke dynamics, Tsanas et al. on voice biomarkers, and Karson on blink rate and dopamine. You can view detailed citations and research foundations on our Research page. Each modality has been validated in peer-reviewed studies, though this specific platform implementation requires further clinical validation.";
    }

    if (lowerQuery.includes("privacy") || lowerQuery.includes("data")) {
      return "Your privacy is our priority. All assessments are processed securely, with data encrypted in transit and at rest. We do not share your personal data with third parties. Session data is stored locally and can be deleted at any time. Voice recordings are processed for analysis only and are not retained beyond the session unless you choose to save them. For detailed information, please review our privacy policy.";
    }

    // Default response
    return "That's a great question! I can help you understand your assessment results, explain how our screening methods work, discuss the research behind PD detection, or provide general information about Parkinson's disease. Could you please be more specific about what you'd like to know?";
  };

  const suggestedQuestions = [
    "What do my test results mean?",
    "How accurate is this screening?",
    "What should I do next?",
    "How does the typing test work?",
    "What is Parkinson's disease?"
  ];

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <div className="border-b bg-card">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              onClick={() => navigate(-1)}
              variant="ghost"
              size="sm"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <Bot className="h-6 w-6 text-primary" />
            <div>
              <h1 className="text-xl font-bold">AI Assistant</h1>
              <p className="text-xs text-muted-foreground">Ask me anything about your results</p>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
          {messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex gap-4 ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {message.role === "assistant" && (
                <div className="flex-shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                  <Bot className="h-5 w-5 text-primary-foreground" />
                </div>
              )}

              <Card className={`max-w-[80%] p-4 ${
                message.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              }`}>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                  {message.content}
                </p>
                <p className={`text-xs mt-2 ${
                  message.role === "user" ? "text-primary-foreground/70" : "text-muted-foreground"
                }`}>
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </Card>

              {message.role === "user" && (
                <div className="flex-shrink-0 w-8 h-8 bg-muted rounded-full flex items-center justify-center">
                  <User className="h-5 w-5 text-muted-foreground" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-4 justify-start">
              <div className="flex-shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                <Bot className="h-5 w-5 text-primary-foreground" />
              </div>
              <Card className="max-w-[80%] p-4 bg-muted">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <p className="text-sm text-muted-foreground">Thinking...</p>
                </div>
              </Card>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Suggested Questions (only show when no messages yet) */}
      {messages.length === 1 && (
        <div className="border-t bg-card">
          <div className="max-w-4xl mx-auto px-6 py-4">
            <p className="text-xs text-muted-foreground mb-3">Suggested questions:</p>
            <div className="flex flex-wrap gap-2">
              {suggestedQuestions.map((question, idx) => (
                <Button
                  key={idx}
                  variant="outline"
                  size="sm"
                  onClick={() => setInput(question)}
                  className="text-xs"
                >
                  {question}
                </Button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t bg-card">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex gap-2">
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your question..."
              disabled={isLoading}
              className="flex-1"
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              size="icon"
              className="glow-primary"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Note: This is an AI assistant. For medical advice, consult a healthcare professional.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
