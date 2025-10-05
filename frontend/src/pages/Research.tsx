import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { BookOpen, ExternalLink, Brain, Keyboard, Mic, Eye, ArrowLeft } from "lucide-react";

const ResearchPage = () => {
  const navigate = useNavigate();

  const researchSections = [
    {
      icon: Keyboard,
      title: "Keystroke Dynamics & Parkinson's Disease",
      description: "Typing patterns can reveal motor impairments characteristic of PD through analysis of hold times, flight times, rhythm variations, and asymmetry.",
      keyFindings: [
        "PD patients show increased keystroke variability and slower typing speeds",
        "Hold times and flight times are significantly longer in PD patients",
        "Left-right hand asymmetry correlates with motor symptom lateralization",
        "Pause frequency and duration increase with disease progression"
      ],
      citations: [
        {
          title: "Computer keyboard interaction as an indicator of early Parkinson's disease",
          authors: "Giancardo et al.",
          year: "2016",
          journal: "Scientific Reports",
          link: "https://www.nature.com/articles/srep34468"
        },
        {
          title: "Real-world keystroke dynamics are a potentially valid biomarker for clinical motor impairment in Parkinson's disease",
          authors: "Adams et al.",
          year: "2017",
          journal: "IEEE Transactions on Cybernetics",
          link: "https://ieeexplore.ieee.org/document/7887040"
        }
      ]
    },
    {
      icon: Mic,
      title: "Voice Biomarkers & PD Detection",
      description: "Voice changes in PD result from rigidity, tremor, and bradykinesia affecting the vocal apparatus. Acoustic analysis can detect subtle changes before clinical diagnosis.",
      keyFindings: [
        "Vocal tremor (4-6 Hz) is detectable in sustained phonation",
        "Reduced pitch variability indicates monotone speech patterns",
        "Increased breathiness correlates with vocal fold dysfunction",
        "Harmonic-to-noise ratio decreases in PD patients"
      ],
      citations: [
        {
          title: "Quantitative acoustic measurements for characterization of speech and voice disorders in early untreated Parkinson's disease",
          authors: "Rusz et al.",
          year: "2011",
          journal: "The Journal of the Acoustical Society of America",
          link: "https://pubs.aip.org/asa/jasa/article/129/1/350/834316"
        },
        {
          title: "Novel speech signal processing algorithms for high-accuracy classification of Parkinson's disease",
          authors: "Tsanas et al.",
          year: "2012",
          journal: "IEEE Transactions on Biomedical Engineering",
          link: "https://ieeexplore.ieee.org/document/6158712"
        },
        {
          title: "Acoustic and clinical correlates in dysarthria of Parkinson's disease",
          authors: "Skodda et al.",
          year: "2011",
          journal: "Journal of Neurology",
          link: "https://link.springer.com/article/10.1007/s00415-011-5994-0"
        }
      ]
    },
    {
      icon: Eye,
      title: "Eye Blink Rate & Dopaminergic Function",
      description: "Spontaneous blink rate is modulated by dopamine. Reduced blink rate is a well-documented finding in PD, correlating with striatal dopamine depletion.",
      keyFindings: [
        "Normal blink rate: 15-20 blinks/minute; PD patients: 5-10 blinks/minute",
        "Blink rate increases with dopaminergic medication",
        "Reduced spontaneous blinking precedes motor symptoms",
        "Blink rate variability increases in PD"
      ],
      citations: [
        {
          title: "Real-Time Eye Blink Detection using Facial Landmarks",
          authors: "Soukupová and Čech",
          year: "2016",
          journal: "21st Computer Vision Winter Workshop",
          link: "https://vision.fe.uni-lj.si/cvww2016/proceedings/papers/05.pdf"
        },
        {
          title: "Spontaneous eye-blink rates and dopaminergic systems",
          authors: "Karson",
          year: "1983",
          journal: "Brain",
          link: "https://academic.oup.com/brain/article/106/3/643/274726"
        },
        {
          title: "Blink rate in Parkinson's disease",
          authors: "Bologna et al.",
          year: "2013",
          journal: "Movement Disorders",
          link: "https://movementdisorders.onlinelibrary.wiley.com/doi/10.1002/mds.25396"
        }
      ]
    },
    {
      icon: Brain,
      title: "Multi-Modal Biomarker Integration",
      description: "Combining multiple digital biomarkers improves screening accuracy. Multi-modal approaches capture the diverse symptomatology of PD.",
      keyFindings: [
        "Multi-modal assessments show higher sensitivity than single modality",
        "Digital biomarkers enable continuous, remote monitoring",
        "Machine learning integration improves predictive accuracy",
        "Longitudinal tracking detects subtle progression"
      ],
      citations: [
        {
          title: "Detecting and monitoring the symptoms of Parkinson's disease using smartphones: A pilot study",
          authors: "Arora et al.",
          year: "2015",
          journal: "Parkinsonism & Related Disorders",
          link: "https://www.sciencedirect.com/science/article/pii/S1353802015003089"
        },
        {
          title: "Distinguishing different stages of Parkinson's disease using composite index of speed and pen-pressure",
          authors: "Zham et al.",
          year: "2017",
          journal: "Frontiers in Neurology",
          link: "https://www.frontiersin.org/articles/10.3389/fneur.2017.00435/full"
        }
      ]
    }
  ];

  return (
    <div className="min-h-screen px-6 py-12 bg-background">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header */}
        <div className="space-y-4">
          <Button
            onClick={() => navigate(-1)}
            variant="ghost"
            className="mb-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>

          <div className="flex items-center gap-3">
            <BookOpen className="h-10 w-10 text-primary" />
            <h1 className="text-5xl font-bold">Research Foundation</h1>
          </div>

          <p className="text-lg text-muted-foreground max-w-3xl">
            Our screening methodology is grounded in peer-reviewed scientific research.
            Below is the evidence supporting each assessment modality.
          </p>
        </div>

        {/* Methodology Overview */}
        <Card className="p-8 bg-primary/5 border-primary/20">
          <h2 className="text-2xl font-bold mb-4">Methodology Overview</h2>
          <div className="space-y-3 text-muted-foreground">
            <p>
              <strong className="text-foreground">take2</strong> employs a multi-modal digital biomarker approach to screen for
              early signs of Parkinson's Disease. Our platform analyzes:
            </p>
            <ul className="space-y-2 ml-6">
              <li className="flex gap-2">
                <span className="text-primary">•</span>
                <span><strong>Keystroke dynamics:</strong> Temporal patterns and rhythm in typing behavior</span>
              </li>
              <li className="flex gap-2">
                <span className="text-primary">•</span>
                <span><strong>Voice acoustics:</strong> Spectral features and prosodic characteristics</span>
              </li>
              <li className="flex gap-2">
                <span className="text-primary">•</span>
                <span><strong>Eye blink frequency:</strong> Spontaneous blink rate and variability</span>
              </li>
            </ul>
            <p className="pt-2">
              Each modality targets different aspects of PD pathophysiology, providing complementary information
              for more robust screening outcomes.
            </p>
          </div>
        </Card>

        {/* Research Sections */}
        {researchSections.map((section, idx) => (
          <Card key={idx} className="p-8 space-y-6">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-primary/10 rounded-lg">
                <section.icon className="h-6 w-6 text-primary" />
              </div>
              <div className="flex-1 space-y-2">
                <h2 className="text-2xl font-bold">{section.title}</h2>
                <p className="text-muted-foreground">{section.description}</p>
              </div>
            </div>

            {/* Key Findings */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Key Findings</h3>
              <ul className="space-y-2">
                {section.keyFindings.map((finding, i) => (
                  <li key={i} className="flex gap-2 text-sm">
                    <span className="text-primary mt-1">▸</span>
                    <span className="text-muted-foreground">{finding}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Citations */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Supporting Research</h3>
              <div className="space-y-3">
                {section.citations.map((citation, i) => (
                  <div key={i} className="p-4 bg-muted/50 rounded-lg space-y-2">
                    <h4 className="font-semibold text-sm">{citation.title}</h4>
                    <p className="text-xs text-muted-foreground">
                      {citation.authors} ({citation.year}). <em>{citation.journal}</em>
                    </p>
                    <a
                      href={citation.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                    >
                      View Publication
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        ))}

        {/* Ethical Considerations */}
        <Card className="p-8 bg-orange-500/5 border-orange-500/20">
          <h2 className="text-2xl font-bold mb-4 text-orange-500">Important Disclaimers</h2>
          <div className="space-y-3 text-sm text-muted-foreground">
            <p>
              <strong className="text-foreground">Not a Diagnostic Tool:</strong> This platform is a screening instrument
              designed to identify individuals who may benefit from further clinical evaluation. It is not a substitute
              for professional medical diagnosis.
            </p>
            <p>
              <strong className="text-foreground">Clinical Validation:</strong> While our methods are based on published
              research, this specific implementation requires validation against clinical gold standards before use in
              healthcare decision-making.
            </p>
            <p>
              <strong className="text-foreground">Confounding Factors:</strong> Results may be influenced by fatigue,
              stress, concurrent illness, medications, or other neurological conditions. Longitudinal assessment
              is more reliable than single-session screening.
            </p>
            <p>
              <strong className="text-foreground">Privacy & Data:</strong> All assessments are processed with strict
              privacy protections. User data is not shared with third parties.
            </p>
          </div>
        </Card>

        {/* Call to Action */}
        <div className="flex justify-center gap-4 pt-4">
          <Button
            onClick={() => navigate('/')}
            variant="outline"
            size="lg"
          >
            Return Home
          </Button>
          <Button
            onClick={() => navigate('/chat')}
            size="lg"
            className="glow-primary"
          >
            Have Questions? Ask Our AI
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ResearchPage;
