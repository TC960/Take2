"""
LLM-based Audio Analysis Module
Uses Claude API to analyze spectrograms and acoustic features for PD detection
"""

import anthropic
import base64
import json
import pathlib
from datetime import datetime
import os


class LLMAudioAnalyzer:
    """
    Analyzes voice spectrograms using Claude's vision capabilities.
    Integrates acoustic features with visual spectrogram analysis.
    """

    def __init__(self, api_key=None):
        """
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY or pass api_key parameter.")

        self.client = anthropic.Anthropic(api_key=self.api_key)

    def analyze_spectrogram(
        self,
        spectrogram_image_path,
        acoustic_features,
        user_metadata=None
    ):
        """
        Analyze spectrogram image and acoustic features using Claude

        Args:
            spectrogram_image_path: Path to spectrogram PNG image
            acoustic_features: Dict of extracted acoustic features
            user_metadata: Optional dict with user context (age, baseline data, etc.)

        Returns:
            Analysis dict with risk assessment and insights
        """
        # Read and encode spectrogram image
        image_path = pathlib.Path(spectrogram_image_path)
        with open(image_path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')

        # Construct analysis prompt
        prompt = self._build_analysis_prompt(acoustic_features, user_metadata)

        # Call Claude API
        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )

        # Parse response
        response_text = message.content[0].text

        # Structure the analysis
        analysis = {
            "raw_response": response_text,
            "acoustic_features": acoustic_features,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "model": "claude-3-5-sonnet-20241022",
                "spectrogram_path": str(image_path),
                "user_metadata": user_metadata
            }
        }

        return analysis

    def _build_analysis_prompt(self, features, user_metadata):
        """Construct the analysis prompt with acoustic features and context"""

        features_str = json.dumps(features, indent=2)
        metadata_str = json.dumps(user_metadata, indent=2) if user_metadata else "None provided"

        prompt = f"""You are an expert in analyzing voice biomarkers for early Parkinson's Disease (PD) detection.

Analyze this voice spectrogram and acoustic features for signs of PD-related vocal changes.

**Acoustic Features Extracted:**
```json
{features_str}
```

**User Context:**
```json
{metadata_str}
```

**Key PD Voice Biomarkers to Assess:**

1. **Vocal Tremor (4-6 Hz)**
   - Tremor band ratio in features
   - Visual periodic modulation in spectrogram
   - Assess severity: None/Mild/Moderate/Severe

2. **Frequency Instability**
   - Spectral centroid variability
   - Harmonic irregularities
   - Fundamental frequency (F0) perturbations

3. **Breathiness/Aspiration**
   - High frequency energy ratio
   - Spectral noise characteristics
   - Harmonic-to-noise patterns

4. **Monotonicity**
   - Reduced pitch variation
   - Spectral flatness
   - Prosodic range limitation

5. **Voice Quality**
   - Hoarseness indicators
   - Spectral clarity
   - Energy distribution patterns

**Analysis Instructions:**

1. Examine the spectrogram for visual patterns (tremor modulation, harmonic structure, noise)
2. Correlate visual findings with quantitative acoustic features
3. Compare against typical PD voice signatures
4. Consider user context (age, baseline if available)

**Output Format (JSON):**

```json
{{
  "risk_assessment": {{
    "overall_risk_score": 0.0-1.0,
    "confidence": 0.0-1.0,
    "risk_category": "low" | "moderate" | "elevated" | "high"
  }},
  "biomarker_findings": {{
    "vocal_tremor": {{
      "detected": true/false,
      "severity": "none" | "mild" | "moderate" | "severe",
      "evidence": "brief explanation"
    }},
    "frequency_instability": {{
      "detected": true/false,
      "severity": "none" | "mild" | "moderate" | "severe",
      "evidence": "brief explanation"
    }},
    "breathiness": {{
      "detected": true/false,
      "severity": "none" | "mild" | "moderate" | "severe",
      "evidence": "brief explanation"
    }},
    "monotonicity": {{
      "detected": true/false,
      "severity": "none" | "mild" | "moderate" | "severe",
      "evidence": "brief explanation"
    }}
  }},
  "clinical_interpretation": {{
    "summary": "2-3 sentence summary of findings",
    "key_concerns": ["list", "of", "concerns"],
    "recommendation": "clinical recommendation"
  }},
  "limitations": "Note any limitations or caveats in this analysis"
}}
```

**Important Notes:**
- This is a screening tool, NOT a diagnostic tool
- Results should be interpreted by healthcare professionals
- Multiple factors can affect voice (illness, fatigue, etc.)
- Longitudinal tracking is more reliable than single assessments

Provide your analysis in valid JSON format."""

        return prompt

    def save_analysis(self, analysis, output_path):
        """Save analysis results to JSON file"""
        output_path = pathlib.Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=2)

        print(f"[LLM Analyzer] Analysis saved to {output_path}")


def analyze_audio_with_llm(
    spectrogram_path,
    features_dict,
    user_metadata=None,
    output_dir="llm_analysis"
):
    """
    Convenience function to run LLM analysis on spectrogram

    Args:
        spectrogram_path: Path to spectrogram image
        features_dict: Acoustic features dictionary
        user_metadata: Optional user context
        output_dir: Directory to save analysis results

    Returns:
        Analysis dictionary
    """
    analyzer = LLMAudioAnalyzer()

    print("\n[LLM Analysis] Analyzing spectrogram with Claude...")

    analysis = analyzer.analyze_spectrogram(
        spectrogram_path,
        features_dict,
        user_metadata
    )

    # Save results
    session_id = pathlib.Path(spectrogram_path).stem.replace('_spectrogram', '')
    output_path = pathlib.Path(output_dir) / f"{session_id}_llm_analysis.json"

    analyzer.save_analysis(analysis, output_path)

    return analysis


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze spectrogram using Claude LLM")
    parser.add_argument("spectrogram_path", type=str, help="Path to spectrogram PNG")
    parser.add_argument("features_path", type=str, help="Path to acoustic features JSON")
    parser.add_argument("--output_dir", type=str, default="llm_analysis", help="Output directory")
    parser.add_argument("--user_metadata", type=str, help="Optional JSON file with user metadata")
    args = parser.parse_args()

    # Load acoustic features
    with open(args.features_path, 'r') as f:
        data = json.load(f)
        features = data.get("features", data)

    # Load user metadata if provided
    user_metadata = None
    if args.user_metadata:
        with open(args.user_metadata, 'r') as f:
            user_metadata = json.load(f)

    # Run analysis
    analysis = analyze_audio_with_llm(
        args.spectrogram_path,
        features,
        user_metadata,
        args.output_dir
    )

    print(f"\n✓ LLM Analysis complete!")
    print(f"\nAnalysis Preview:")
    print(analysis.get("raw_response", "")[:500] + "...")
