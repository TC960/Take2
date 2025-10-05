import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { Brain, Keyboard, Mic, Eye, ArrowRight, AlertCircle } from "lucide-react";

interface TypingResults {
  session_id: string;
  score_0to1?: number;
  band?: string;
  features?: any;
}

interface VoiceResults {
  session_id: string;
  llm_analysis?: any;
  acoustic_features?: any;
}

const ResultsPage = () => {
  const navigate = useNavigate();
  const [typingResults, setTypingResults] = useState<TypingResults | null>(null);
  const [voiceResults, setVoiceResults] = useState<VoiceResults | null>(null);
  const [parsedVoiceAnalysis, setParsedVoiceAnalysis] = useState<any>(null);
  const [overallRisk, setOverallRisk] = useState<number>(0);
  const [riskCategory, setRiskCategory] = useState<string>("unknown");

  useEffect(() => {
    // Load results from sessionStorage
    const typingData = sessionStorage.getItem('typingAnalysis');
    const voiceData = sessionStorage.getItem('voiceAnalysis');

    if (typingData) {
      setTypingResults(JSON.parse(typingData));
    }

    if (voiceData) {
      const voice = JSON.parse(voiceData);
      setVoiceResults(voice);

      // Parse LLM raw_response if it's a string
      if (voice?.llm_analysis?.raw_response) {
        try {
          let parsed;
          if (typeof voice.llm_analysis.raw_response === 'string') {
            // Try to extract JSON from markdown code blocks
            const jsonMatch = voice.llm_analysis.raw_response.match(/```(?:json)?\s*(\{[\s\S]*?\})\s*```/);
            if (jsonMatch) {
              parsed = JSON.parse(jsonMatch[1]);
            } else {
              // Try direct parsing
              parsed = JSON.parse(voice.llm_analysis.raw_response);
            }
          } else {
            parsed = voice.llm_analysis.raw_response;
          }
          setParsedVoiceAnalysis(parsed);
        } catch (e) {
          console.error("Failed to parse LLM response:", e);
        }
      }
    }

    // Calculate overall risk
    calculateOverallRisk(
      typingData ? JSON.parse(typingData) : null,
      voiceData ? JSON.parse(voiceData) : null
    );
  }, []);

  const calculateOverallRisk = (typing: any, voice: any) => {
    const risks: number[] = [];

    if (typing?.score_0to1 !== undefined) {
      risks.push(typing.score_0to1);
    }

    // Parse voice analysis
    if (voice?.llm_analysis?.raw_response) {
      try {
        let parsed;
        if (typeof voice.llm_analysis.raw_response === 'string') {
          // Try to extract JSON from markdown code blocks
          const jsonMatch = voice.llm_analysis.raw_response.match(/```(?:json)?\s*(\{[\s\S]*?\})\s*```/);
          if (jsonMatch) {
            parsed = JSON.parse(jsonMatch[1]);
          } else {
            // Try direct parsing
            parsed = JSON.parse(voice.llm_analysis.raw_response);
          }
        } else {
          parsed = voice.llm_analysis.raw_response;
        }

        if (parsed?.risk_assessment?.overall_risk_score !== undefined) {
          risks.push(parsed.risk_assessment.overall_risk_score);
        }
      } catch (e) {
        console.error("Failed to parse voice risk:", e);
      }
    }

    if (risks.length > 0) {
      const avgRisk = risks.reduce((a, b) => a + b, 0) / risks.length;
      setOverallRisk(avgRisk);

      if (avgRisk < 0.3) {
        setRiskCategory("low");
      } else if (avgRisk < 0.5) {
        setRiskCategory("moderate");
      } else if (avgRisk < 0.7) {
        setRiskCategory("elevated");
      } else {
        setRiskCategory("high");
      }
    }
  };

  const getRiskColor = (category: string) => {
    switch (category) {
      case "low": return "text-green-500";
      case "moderate": return "text-yellow-500";
      case "elevated": return "text-orange-500";
      case "high": return "text-red-500";
      default: return "text-muted-foreground";
    }
  };

  const getRiskBgColor = (category: string) => {
    switch (category) {
      case "low": return "bg-green-500/10";
      case "moderate": return "bg-yellow-500/10";
      case "elevated": return "bg-orange-500/10";
      case "high": return "bg-red-500/10";
      default: return "bg-muted";
    }
  };

  return (
    <div className="min-h-screen px-6 py-12 bg-background">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-5xl font-bold">Assessment Results</h1>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Your comprehensive multi-modal Parkinson's disease screening analysis
          </p>
        </div>

        {/* Overall Risk Score */}
        <Card className={`p-8 ${getRiskBgColor(riskCategory)}`}>
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Brain className="h-6 w-6" />
                <h2 className="text-2xl font-bold">Overall Risk Assessment</h2>
              </div>
              <p className="text-sm text-muted-foreground">
                Combined analysis from all modalities
              </p>
            </div>
            <div className="text-center">
              <div className={`text-6xl font-bold ${getRiskColor(riskCategory)}`}>
                {(overallRisk * 100).toFixed(0)}%
              </div>
              <div className={`text-lg font-semibold uppercase ${getRiskColor(riskCategory)}`}>
                {riskCategory}
              </div>
            </div>
          </div>
        </Card>

        {/* Disclaimer */}
        <Card className="p-6 bg-blue-500/10 border-blue-500/20">
          <div className="flex gap-3">
            <AlertCircle className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h3 className="font-semibold text-blue-500">Important Notice</h3>
              <p className="text-sm text-muted-foreground">
                This is a screening tool, not a diagnostic instrument. Results should be discussed with a healthcare professional.
                Multiple factors can affect performance including fatigue, stress, or other medical conditions.
              </p>
            </div>
          </div>
        </Card>

        {/* Individual Test Results */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Typing Test Results */}
          <Card className="p-6 space-y-4">
            <div className="flex items-center gap-2">
              <Keyboard className="h-5 w-5 text-primary" />
              <h3 className="text-xl font-bold">Typing Analysis</h3>
            </div>

            {typingResults ? (
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Risk Score</span>
                  <span className={`text-2xl font-bold ${getRiskColor(typingResults.band?.toLowerCase() || "unknown")}`}>
                    {typingResults.band || "N/A"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Confidence</span>
                  <span className="font-semibold">
                    {typingResults.score_0to1 ? `${(typingResults.score_0to1 * 100).toFixed(0)}%` : "N/A"}
                  </span>
                </div>
                <div className="pt-2 border-t">
                  <p className="text-xs text-muted-foreground">
                    Session ID: {typingResults.session_id}
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <p className="text-sm">No typing test data available</p>
                <Button
                  onClick={() => navigate('/typing-test')}
                  variant="outline"
                  size="sm"
                  className="mt-4"
                >
                  Take Typing Test
                </Button>
              </div>
            )}
          </Card>

          {/* Voice Test Results */}
          <Card className="p-6 space-y-4">
            <div className="flex items-center gap-2">
              <Mic className="h-5 w-5 text-primary" />
              <h3 className="text-xl font-bold">Voice Analysis</h3>
            </div>

            {parsedVoiceAnalysis?.risk_assessment ? (
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Risk Category</span>
                  <span className={`text-2xl font-bold ${getRiskColor(
                    parsedVoiceAnalysis.risk_assessment.risk_category || "unknown"
                  )}`}>
                    {parsedVoiceAnalysis.risk_assessment.risk_category?.toUpperCase() || "N/A"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Confidence</span>
                  <span className="font-semibold">
                    {parsedVoiceAnalysis.risk_assessment.confidence
                      ? `${(parsedVoiceAnalysis.risk_assessment.confidence * 100).toFixed(0)}%`
                      : "N/A"}
                  </span>
                </div>
                <div className="pt-2 border-t">
                  <p className="text-xs text-muted-foreground">
                    Session ID: {voiceResults?.session_id}
                  </p>
                </div>
                {voiceResults?.session_id && (
                  <div className="flex gap-2 mt-2">
                    <Button
                      onClick={() => window.open(`http://localhost:8000/api/voice/spectrogram/${voiceResults.session_id}`, '_blank')}
                      variant="outline"
                      size="sm"
                      className="flex-1"
                    >
                      View Spectrogram
                    </Button>
                    <Button
                      onClick={() => window.open(`http://localhost:8000/api/voice/report/${voiceResults.session_id}`, '_blank')}
                      variant="default"
                      size="sm"
                      className="flex-1"
                    >
                      Download Report
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <p className="text-sm">No voice test data available</p>
                <Button
                  onClick={() => navigate('/voice-test')}
                  variant="outline"
                  size="sm"
                  className="mt-4"
                >
                  Take Voice Test
                </Button>
              </div>
            )}
          </Card>

          {/* Eye Blink Results - Placeholder */}
          <Card className="p-6 space-y-4 opacity-50">
            <div className="flex items-center gap-2">
              <Eye className="h-5 w-5 text-primary" />
              <h3 className="text-xl font-bold">Eye Blink Analysis</h3>
            </div>
            <div className="text-center py-8 text-muted-foreground">
              <p className="text-sm">Coming soon</p>
            </div>
          </Card>
        </div>

        {/* Recommendations */}
        {(typingResults || parsedVoiceAnalysis) && (
          <Card className="p-6 space-y-4">
            <h3 className="text-xl font-bold">Recommendations</h3>
            <ul className="space-y-2 text-sm">
              {riskCategory === "low" && (
                <>
                  <li className="flex gap-2">
                    <span className="text-green-500">•</span>
                    <span>Results appear within normal range. Continue regular health monitoring.</span>
                  </li>
                  <li className="flex gap-2">
                    <span className="text-green-500">•</span>
                    <span>Consider establishing a baseline by repeating assessments periodically.</span>
                  </li>
                </>
              )}
              {(riskCategory === "moderate" || riskCategory === "elevated") && (
                <>
                  <li className="flex gap-2">
                    <span className="text-yellow-500">•</span>
                    <span>Some indicators suggest monitoring may be beneficial.</span>
                  </li>
                  <li className="flex gap-2">
                    <span className="text-yellow-500">•</span>
                    <span>Repeat assessments over time to track any changes.</span>
                  </li>
                  <li className="flex gap-2">
                    <span className="text-yellow-500">•</span>
                    <span>Consider discussing results with your healthcare provider.</span>
                  </li>
                </>
              )}
              {riskCategory === "high" && (
                <>
                  <li className="flex gap-2">
                    <span className="text-red-500">•</span>
                    <span>Consider consultation with a neurologist for professional evaluation.</span>
                  </li>
                  <li className="flex gap-2">
                    <span className="text-red-500">•</span>
                    <span>Monitor symptoms over time with repeated assessments.</span>
                  </li>
                  <li className="flex gap-2">
                    <span className="text-red-500">•</span>
                    <span>Keep a log of any motor or cognitive changes you notice.</span>
                  </li>
                </>
              )}
            </ul>
          </Card>
        )}

        {/* Navigation */}
        <div className="flex justify-center gap-4 pt-4">
          <Button
            onClick={() => navigate('/research')}
            variant="outline"
            size="lg"
          >
            Learn About the Science
          </Button>
          <Button
            onClick={() => navigate('/chat')}
            size="lg"
            className="glow-primary"
          >
            Ask Questions
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ResultsPage;
