"""
PD-Oriented Report Generator
Generates comprehensive clinical reports for Parkinson's Disease screening results
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import base64

class PDReportGenerator:
    """Generates detailed PD screening reports"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_risk_color(self, category: str) -> str:
        """Get color for risk category"""
        colors = {
            "low": "#10b981",
            "moderate": "#f59e0b",
            "elevated": "#f97316",
            "high": "#ef4444"
        }
        return colors.get(category.lower(), "#6b7280")

    def _encode_image_base64(self, image_path: Path) -> str:
        """Encode image to base64 for embedding in HTML"""
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')

    def generate_html_report(
        self,
        session_id: str,
        typing_results: Optional[Dict[str, Any]] = None,
        voice_results: Optional[Dict[str, Any]] = None,
        spectrogram_path: Optional[Path] = None
    ) -> str:
        """Generate comprehensive HTML report"""

        # Parse voice analysis if available
        voice_analysis = None
        if voice_results and voice_results.get('llm_analysis', {}).get('raw_response'):
            try:
                raw = voice_results['llm_analysis']['raw_response']
                voice_analysis = json.loads(raw) if isinstance(raw, str) else raw
            except Exception as e:
                print(f"Failed to parse voice analysis: {e}")

        # Calculate overall risk
        risks = []
        if typing_results and typing_results.get('score_0to1') is not None:
            risks.append(typing_results['score_0to1'])
        if voice_analysis and voice_analysis.get('risk_assessment', {}).get('overall_risk_score') is not None:
            risks.append(voice_analysis['risk_assessment']['overall_risk_score'])

        overall_risk = sum(risks) / len(risks) if risks else 0

        # Determine risk category
        if overall_risk < 0.3:
            risk_category = "low"
        elif overall_risk < 0.5:
            risk_category = "moderate"
        elif overall_risk < 0.7:
            risk_category = "elevated"
        else:
            risk_category = "high"

        risk_color = self._get_risk_color(risk_category)

        # Encode spectrogram if available
        spectrogram_base64 = ""
        if spectrogram_path and spectrogram_path.exists():
            spectrogram_base64 = self._encode_image_base64(spectrogram_path)

        # Generate HTML
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parkinson's Disease Screening Report - {session_id}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background: #f9fafb;
            padding: 2rem;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 3rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .header {{
            text-align: center;
            border-bottom: 3px solid #3b82f6;
            padding-bottom: 2rem;
            margin-bottom: 2rem;
        }}

        .header h1 {{
            font-size: 2.5rem;
            color: #1f2937;
            margin-bottom: 0.5rem;
        }}

        .header .subtitle {{
            font-size: 1.1rem;
            color: #6b7280;
        }}

        .metadata {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            padding: 1.5rem;
            background: #f3f4f6;
            border-radius: 8px;
            margin-bottom: 2rem;
        }}

        .metadata-item {{
            display: flex;
            flex-direction: column;
        }}

        .metadata-label {{
            font-size: 0.875rem;
            color: #6b7280;
            margin-bottom: 0.25rem;
        }}

        .metadata-value {{
            font-weight: 600;
            color: #1f2937;
        }}

        .risk-summary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            text-align: center;
        }}

        .risk-score {{
            font-size: 4rem;
            font-weight: 700;
            margin: 1rem 0;
        }}

        .risk-category {{
            font-size: 1.5rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}

        .section {{
            margin-bottom: 2.5rem;
        }}

        .section-title {{
            font-size: 1.75rem;
            color: #1f2937;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e5e7eb;
        }}

        .card {{
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        .card-header {{
            font-size: 1.25rem;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .badge-low {{ background: #d1fae5; color: #065f46; }}
        .badge-moderate {{ background: #fef3c7; color: #92400e; }}
        .badge-elevated {{ background: #fed7aa; color: #9a3412; }}
        .badge-high {{ background: #fee2e2; color: #991b1b; }}

        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin-top: 1rem;
        }}

        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 0.75rem;
            background: white;
            border-radius: 6px;
        }}

        .metric-label {{
            color: #6b7280;
            font-size: 0.875rem;
        }}

        .metric-value {{
            font-weight: 600;
            color: #1f2937;
        }}

        .spectrogram-container {{
            margin-top: 1rem;
            text-align: center;
        }}

        .spectrogram-img {{
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .findings-list {{
            list-style: none;
            margin-top: 1rem;
        }}

        .finding-item {{
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            background: white;
            border-left: 4px solid #3b82f6;
            border-radius: 4px;
        }}

        .clinical-text {{
            line-height: 1.8;
            color: #374151;
            margin-top: 1rem;
        }}

        .disclaimer {{
            background: #fef3c7;
            border: 2px solid #f59e0b;
            border-radius: 8px;
            padding: 1.5rem;
            margin-top: 2rem;
        }}

        .disclaimer-title {{
            font-weight: 700;
            color: #92400e;
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
        }}

        .disclaimer-text {{
            color: #78350f;
            font-size: 0.95rem;
        }}

        .footer {{
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 2px solid #e5e7eb;
            text-align: center;
            color: #6b7280;
            font-size: 0.875rem;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
                padding: 1rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Parkinson's Disease Screening Report</h1>
            <p class="subtitle">Multi-Modal Assessment Analysis</p>
        </div>

        <div class="metadata">
            <div class="metadata-item">
                <span class="metadata-label">Session ID</span>
                <span class="metadata-value">{session_id}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Report Generated</span>
                <span class="metadata-value">{datetime.now().strftime("%B %d, %Y at %I:%M %p")}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Assessment Type</span>
                <span class="metadata-value">Multi-Modal Screening</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Analysis Platform</span>
                <span class="metadata-value">take2 v1.0</span>
            </div>
        </div>

        <div class="risk-summary">
            <h2>Overall Risk Assessment</h2>
            <div class="risk-score">{(overall_risk * 100):.0f}%</div>
            <div class="risk-category">{risk_category} Risk</div>
            <p style="margin-top: 1rem; opacity: 0.9;">Combined analysis from all modalities</p>
        </div>
"""

        # Typing Analysis Section
        if typing_results:
            html += f"""
        <div class="section">
            <h2 class="section-title">⌨️ Typing Dynamics Analysis</h2>
            <div class="card">
                <div class="card-header">
                    Keystroke Pattern Assessment
                    <span class="badge badge-{typing_results.get('band', 'unknown').lower()}">{typing_results.get('band', 'N/A')}</span>
                </div>
                <div class="metric-grid">
                    <div class="metric">
                        <span class="metric-label">Risk Score</span>
                        <span class="metric-value">{(typing_results.get('score_0to1', 0) * 100):.1f}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Band Classification</span>
                        <span class="metric-value">{typing_results.get('band', 'N/A')}</span>
                    </div>
                </div>
                <p class="clinical-text">
                    Typing dynamics analysis evaluates keystroke patterns including dwell time (how long keys are held),
                    flight time (intervals between keystrokes), and rhythm consistency. These metrics can reveal
                    subtle motor control variations associated with early Parkinson's disease.
                </p>
            </div>
        </div>
"""

        # Voice Analysis Section
        if voice_analysis:
            risk_assessment = voice_analysis.get('risk_assessment', {})
            biomarkers = voice_analysis.get('biomarker_findings', {})
            clinical = voice_analysis.get('clinical_interpretation', {})

            html += f"""
        <div class="section">
            <h2 class="section-title">🎤 Voice & Acoustic Analysis</h2>
            <div class="card">
                <div class="card-header">
                    Voice Biomarker Assessment
                    <span class="badge badge-{risk_assessment.get('risk_category', 'unknown').lower()}">{risk_assessment.get('risk_category', 'N/A')}</span>
                </div>
                <div class="metric-grid">
                    <div class="metric">
                        <span class="metric-label">Overall Risk Score</span>
                        <span class="metric-value">{(risk_assessment.get('overall_risk_score', 0) * 100):.1f}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Confidence Level</span>
                        <span class="metric-value">{(risk_assessment.get('confidence', 0) * 100):.0f}%</span>
                    </div>
                </div>
"""

            # Spectrogram
            if spectrogram_base64:
                html += f"""
                <div class="spectrogram-container">
                    <h4 style="margin-bottom: 1rem; color: #1f2937;">Voice Spectrogram Analysis</h4>
                    <img src="data:image/png;base64,{spectrogram_base64}" alt="Voice Spectrogram" class="spectrogram-img">
                </div>
"""

            # Biomarker Findings
            html += """
                <h4 style="margin-top: 1.5rem; margin-bottom: 0.5rem; color: #1f2937;">Biomarker Findings</h4>
                <ul class="findings-list">
"""

            if biomarkers.get('pitch_instability'):
                html += f"""
                    <li class="finding-item">
                        <strong>Pitch Instability:</strong> {biomarkers['pitch_instability'].get('description', 'N/A')}
                        <br><small style="color: #6b7280;">Severity: {biomarkers['pitch_instability'].get('severity', 'N/A')}</small>
                    </li>
"""

            if biomarkers.get('voice_tremor'):
                html += f"""
                    <li class="finding-item">
                        <strong>Voice Tremor:</strong> {biomarkers['voice_tremor'].get('description', 'N/A')}
                        <br><small style="color: #6b7280;">Severity: {biomarkers['voice_tremor'].get('severity', 'N/A')}</small>
                    </li>
"""

            if biomarkers.get('breathiness'):
                html += f"""
                    <li class="finding-item">
                        <strong>Breathiness:</strong> {biomarkers['breathiness'].get('description', 'N/A')}
                        <br><small style="color: #6b7280;">Severity: {biomarkers['breathiness'].get('severity', 'N/A')}</small>
                    </li>
"""

            if biomarkers.get('monotonicity'):
                html += f"""
                    <li class="finding-item">
                        <strong>Monotonicity:</strong> {biomarkers['monotonicity'].get('description', 'N/A')}
                        <br><small style="color: #6b7280;">Severity: {biomarkers['monotonicity'].get('severity', 'N/A')}</small>
                    </li>
"""

            html += """
                </ul>
"""

            # Clinical Interpretation
            if clinical.get('summary'):
                html += f"""
                <h4 style="margin-top: 1.5rem; margin-bottom: 0.5rem; color: #1f2937;">Clinical Interpretation</h4>
                <p class="clinical-text">{clinical['summary']}</p>
"""

            if clinical.get('recommendations'):
                html += f"""
                <h4 style="margin-top: 1rem; margin-bottom: 0.5rem; color: #1f2937;">Clinical Recommendations</h4>
                <p class="clinical-text">{clinical['recommendations']}</p>
"""

            html += """
            </div>
        </div>
"""

        # Recommendations
        html += f"""
        <div class="section">
            <h2 class="section-title">📋 Recommendations</h2>
            <div class="card">
"""

        if risk_category == "low":
            html += """
                <ul class="findings-list">
                    <li class="finding-item" style="border-left-color: #10b981;">
                        Results appear within normal range. Continue regular health monitoring.
                    </li>
                    <li class="finding-item" style="border-left-color: #10b981;">
                        Consider establishing a baseline by repeating assessments periodically (e.g., annually).
                    </li>
                    <li class="finding-item" style="border-left-color: #10b981;">
                        Maintain healthy lifestyle habits including regular exercise and balanced nutrition.
                    </li>
                </ul>
"""
        elif risk_category in ["moderate", "elevated"]:
            html += """
                <ul class="findings-list">
                    <li class="finding-item" style="border-left-color: #f59e0b;">
                        Some indicators suggest monitoring may be beneficial. Consider follow-up assessment in 3-6 months.
                    </li>
                    <li class="finding-item" style="border-left-color: #f59e0b;">
                        Repeat assessments over time to track any changes or progression.
                    </li>
                    <li class="finding-item" style="border-left-color: #f59e0b;">
                        Discuss results with your primary care physician or healthcare provider.
                    </li>
                    <li class="finding-item" style="border-left-color: #f59e0b;">
                        Keep a log of any motor symptoms, tremors, or changes in daily functioning.
                    </li>
                </ul>
"""
        else:  # high
            html += """
                <ul class="findings-list">
                    <li class="finding-item" style="border-left-color: #ef4444;">
                        Results indicate elevated risk. Consultation with a neurologist is recommended for professional evaluation.
                    </li>
                    <li class="finding-item" style="border-left-color: #ef4444;">
                        Comprehensive clinical assessment may include MRI, DAT scan, or other diagnostic procedures.
                    </li>
                    <li class="finding-item" style="border-left-color: #ef4444;">
                        Monitor symptoms closely and keep detailed records of motor and non-motor symptoms.
                    </li>
                    <li class="finding-item" style="border-left-color: #ef4444;">
                        Early intervention can improve quality of life and treatment outcomes if diagnosis is confirmed.
                    </li>
                </ul>
"""

        html += """
            </div>
        </div>

        <div class="disclaimer">
            <div class="disclaimer-title">⚠️ Important Medical Disclaimer</div>
            <p class="disclaimer-text">
                This report is generated by an AI-powered screening tool and is <strong>NOT a medical diagnosis</strong>.
                It is designed to identify potential risk indicators that may warrant further clinical evaluation.
                Results can be affected by multiple factors including fatigue, stress, medication, or other medical conditions.
                Always consult with qualified healthcare professionals for proper medical diagnosis and treatment.
                This tool should be used as a supplementary screening aid, not as a replacement for professional medical advice.
            </p>
        </div>

        <div class="footer">
            <p><strong>take2</strong> - Multi-Modal Parkinson's Disease Screening Platform</p>
            <p>Report generated using advanced AI analysis with Claude 3.7 Sonnet</p>
            <p style="margin-top: 0.5rem;">For questions or concerns, please consult with your healthcare provider</p>
        </div>
    </div>
</body>
</html>
"""

        # Save report
        report_path = self.output_dir / f"report_{session_id}.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"[Report] Generated HTML report: {report_path}")
        return str(report_path)
