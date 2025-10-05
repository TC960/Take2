import { Button } from "@/components/ui/button";
import { ArrowDown } from "lucide-react";
import { useNavigate } from "react-router-dom";

const Hero = () => {
  const navigate = useNavigate();

  const startAssessment = () => {
    navigate('/typing-test');
  };

  return (
    <section className="min-h-screen flex flex-col items-center justify-center px-6 relative">
      <nav className="absolute top-8 left-0 right-0 flex justify-center gap-8 text-sm text-muted-foreground">
        <a href="#" className="hover:text-primary transition-colors">Home</a>
        <a href="#about" className="hover:text-primary transition-colors">About</a>
        <a href="#privacy" className="hover:text-primary transition-colors">Privacy</a>
      </nav>

      <div className="text-center animate-fade-in space-y-8 max-w-3xl">
        <h1 className="text-7xl md:text-8xl font-bold tracking-tight text-gradient">
          take2
        </h1>
        
        <p className="text-xl md:text-2xl text-muted-foreground font-light">
          Multimodal Parkinson's Diagnostic Aid
        </p>

        <p className="text-base md:text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          An innovative assessment tool combining typing analysis, voice patterns, 
          and behavioral metrics to support early Parkinson's disease detection.
        </p>

        <Button
          onClick={startAssessment}
          size="lg"
          className="mt-8 text-lg px-8 py-6 glow-primary hover:scale-105 transition-all"
        >
          Begin Assessment
          <ArrowDown className="ml-2 h-5 w-5 animate-bounce" />
        </Button>
      </div>

      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 text-muted-foreground text-xs">
        Medical-grade assessment • Privacy-first design
      </div>
    </section>
  );
};

export default Hero;
