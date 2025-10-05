import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { AlertCircle, CheckCircle2, Download, RotateCcw } from "lucide-react";

const Results = () => {
  const metrics = [
    { label: "Typing Speed", value: "45 WPM", status: "normal" },
    { label: "Typing Accuracy", value: "94%", status: "normal" },
    { label: "Eye Blink Rate", value: "Pending", status: "pending" },
    { label: "Voice Tremor", value: "Analysis", status: "pending" },
  ];

  const riskScore = 23; // Mock score
  const riskLevel = riskScore < 30 ? "low" : riskScore < 60 ? "medium" : "high";
  const riskColor = riskLevel === "low" ? "text-success" : riskLevel === "medium" ? "text-accent" : "text-destructive";

  const handleDownload = () => {
    // PDF generation logic would go here
    alert("PDF download functionality coming soon");
  };

  const handleRestart = () => {
    window.location.reload();
  };

  return (
    <section id="results" className="min-h-screen flex items-center justify-center px-6 py-20">
      <div className="w-full max-w-5xl space-y-8">
        <div className="text-center space-y-4">
          <h2 className="text-4xl font-bold">Assessment Results</h2>
          <p className="text-muted-foreground">
            Your comprehensive multimodal diagnostic analysis
          </p>
        </div>

        <Card className="p-8 md:p-12 space-y-8">
          <div className="text-center space-y-4">
            <div className={`text-7xl font-bold ${riskColor}`}>
              {riskScore}
            </div>
            <div className="text-xl text-muted-foreground">Overall Risk Score</div>
            <div className="flex items-center justify-center gap-2">
              {riskLevel === "low" ? (
                <CheckCircle2 className="h-5 w-5 text-success" />
              ) : (
                <AlertCircle className="h-5 w-5 text-accent" />
              )}
              <span className={`font-semibold uppercase ${riskColor}`}>
                {riskLevel} Risk
              </span>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {metrics.map((metric) => (
              <Card key={metric.label} className="p-6 space-y-2 border-border/50">
                <div className="text-sm text-muted-foreground">{metric.label}</div>
                <div className="text-2xl font-bold">{metric.value}</div>
                <div className="text-xs">
                  {metric.status === "normal" && (
                    <span className="text-success">Within normal range</span>
                  )}
                  {metric.status === "pending" && (
                    <span className="text-muted-foreground">In development</span>
                  )}
                </div>
              </Card>
            ))}
          </div>

          <div className="border-t border-border pt-8 space-y-4">
            <h3 className="text-xl font-semibold">Interpretation</h3>
            <p className="text-muted-foreground leading-relaxed">
              Based on the typing analysis, your motor function indicators are within normal 
              parameters. Voice and eye tracking analysis modules are currently in development 
              to provide more comprehensive assessment. This tool is designed to support, not 
              replace, professional medical evaluation.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 pt-4">
            <Button onClick={handleDownload} size="lg" className="flex-1 glow-primary">
              <Download className="mr-2 h-5 w-5" />
              Download Report
            </Button>
            <Button onClick={handleRestart} size="lg" variant="outline" className="flex-1">
              <RotateCcw className="mr-2 h-5 w-5" />
              Start New Test
            </Button>
          </div>
        </Card>

        <div className="text-center text-xs text-muted-foreground">
          <p>This is an experimental diagnostic aid and should not replace professional medical advice.</p>
          <p className="mt-2">Consult with a healthcare provider for proper diagnosis and treatment.</p>
        </div>
      </div>
    </section>
  );
};

export default Results;
