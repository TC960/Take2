# PD Screening Platform - Architecture Documentation

## Project Overview

A multi-modal early Parkinson's Disease (PD) screening platform that combines:
- **Typing dynamics analysis** (keystroke patterns)
- **Voice biomarker analysis** (spectrograms + LLM)
- **Eye blink frequency detection** (computer vision)

This is a **research prototype** for early detection screening, not a diagnostic tool.

---

## System Architecture

### Frontend (React + TypeScript + Vite)
- **Location**: `/frontend`
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Components**: Shadcn/ui
- **Port**: http://localhost:8081/

#### Planned Multi-Page Structure
1. **`/` - Hero/Landing Page**
   - Entry point with overview
   - CTA buttons to start tests

2. **`/typing-test` - Typing Assessment**
   - Real-time typing speed and accuracy test
   - Eye blink detection running in background

3. **`/voice-test` - Voice Analysis**
   - Voice recording interface
   - Eye blink detection running in background

4. **`/results` - Summary Statistics**
   - Aggregate results from all tests
   - Visual charts/graphs
   - Interpretation of results

5. **`/research` - Research Evidence**
   - Scientific background
   - Citations and methodology

6. **`/chat` - RAG Chatbot**
   - Personalized insights using RAG
   - Based on test results

#### Current Implementation Status
- ✅ Multi-page routing implemented (Hero, Typing, Voice, Results, Research, Chat)
- ✅ State management via sessionStorage (typing/voice results)
- ✅ WebSocket real-time typing analysis with PD risk scoring
- ✅ Voice recording + spectrogram + LLM analysis pipeline
- ✅ Results aggregation page with multi-modal risk assessment
- ✅ Research citations page with peer-reviewed sources
- ✅ AI chatbot interface (mock RAG - ready for backend integration)

---

### Backend (Python)
- **Location**: `/backend`
- **Language**: Python 3.8+

#### Module Breakdown

##### 1. Keystroke Analysis Module
**Files**:
- `keystroke_pd.py` - Main keystroke recorder and analyzer
- `pd_keystroke_rules.py` - Analysis rules and models

**Features**:
- Records press/release timestamps
- Computes hold times, flight times
- Tracks backspaces, pauses
- Extracts features: mean, std, median, IQR, MAD, CV
- Asymmetry detection (left vs right hand)
- Error rate calculation
- Speed metrics (chars per second)

**Modes**:
- `collect_baseline`: Build user's normal typing baseline (5-10 sessions recommended)
- `screen`: Evaluate current session against baseline
- `just_features`: Extract features without scoring

**Models**:
- **Supervised**: Loads pre-trained scikit-learn pipeline from `pd_keystroke_model.joblib`
- **Unsupervised**: OneClassSVM trained on user's baseline

**Output**: Risk score 0-1 (higher = more PD-like)

---

##### 2. Eye Blink Detection Module
**File**: `blink_counter.py`

**Technology**:
- OpenCV + MediaPipe Face Mesh
- Eye Aspect Ratio (EAR) algorithm

**Features**:
- Real-time blink counting
- EAR threshold detection (default: 0.25)
- Consecutive frame validation (default: 2 frames)
- Visual feedback with landmarks
- FPS monitoring

**Controls**:
- `q`: Quit
- `r`: Reset counter

**Integration**: Runs as background service during typing and voice tests

---

##### 3. Voice Analysis Pipeline (NEW)
**Files**:
- `audio_recorder.py` - Audio capture
- `spectrogram_generator.py` - Acoustic analysis
- `llm_audio_analyzer.py` - Claude-based interpretation
- `voice_pipeline.py` - Orchestration

**Pipeline Flow**:
```
Audio Recording → Spectrogram Generation → LLM Analysis
```

###### 3.1 Audio Recorder (`audio_recorder.py`)
- **Technology**: PyAudio
- **Format**: WAV (44.1kHz, mono, 16-bit)
- **Output**: Audio file + metadata JSON

**Usage**:
```bash
python audio_recorder.py --duration 10 --output_dir audio_sessions
```

###### 3.2 Spectrogram Generator (`spectrogram_generator.py`)
- **Technology**: SciPy STFT, Matplotlib
- **Parameters**:
  - `n_fft=2048` - FFT window size
  - `hop_length=512` - Frame stride
  - `n_mels=128` - Mel bands
  - `fmin=50, fmax=8000` - Frequency range

**Extracted Features**:
- **Spectral Centroid**: Weighted mean frequency (mean/std)
- **Tremor Band Ratio**: Energy in 4-6 Hz (PD tremor indicator)
- **Spectral Flatness**: Tonality measure
- **Frequency Stability**: Variance over time
- **High Frequency Energy**: Breathiness/aspiration indicator

**Output**:
- Spectrogram PNG with annotations
- Features JSON

**Usage**:
```bash
python spectrogram_generator.py audio_sessions/audio_123.wav --output_dir spectrograms
```

###### 3.3 LLM Audio Analyzer (`llm_audio_analyzer.py`)
- **Model**: Claude 3.5 Sonnet (vision-enabled)
- **API**: Anthropic API
- **Input**: Spectrogram image + acoustic features + user metadata

**Analysis Components**:
1. **Visual Analysis**: Examines spectrogram patterns
2. **Quantitative Analysis**: Correlates with acoustic features
3. **PD Biomarker Assessment**:
   - Vocal Tremor (4-6 Hz modulation)
   - Frequency Instability (pitch perturbations)
   - Breathiness/Aspiration (noise characteristics)
   - Monotonicity (reduced pitch variation)
   - Voice Quality (hoarseness, spectral clarity)

**Output Format** (JSON):
```json
{
  "risk_assessment": {
    "overall_risk_score": 0.0-1.0,
    "confidence": 0.0-1.0,
    "risk_category": "low|moderate|elevated|high"
  },
  "biomarker_findings": {
    "vocal_tremor": {"detected": bool, "severity": "none|mild|moderate|severe", "evidence": "..."},
    "frequency_instability": {...},
    "breathiness": {...},
    "monotonicity": {...}
  },
  "clinical_interpretation": {
    "summary": "...",
    "key_concerns": [...],
    "recommendation": "..."
  },
  "limitations": "..."
}
```

**Usage**:
```bash
python llm_audio_analyzer.py spectrograms/audio_123_spectrogram.png spectrograms/audio_123_features.json
```

**Environment Setup**:
```bash
export ANTHROPIC_API_KEY="your-api-key"
```

###### 3.4 Voice Pipeline Orchestrator (`voice_pipeline.py`)
Complete end-to-end pipeline automation

**Modes**:
- `record`: New recording → Analysis
- `analyze`: Existing audio → Analysis

**Usage**:
```bash
# Record and analyze
python voice_pipeline.py --mode record --duration 10

# Analyze existing audio
python voice_pipeline.py --mode analyze --audio_path audio_sessions/audio_123.wav

# With user context
python voice_pipeline.py --mode record --user_metadata user_profile.json
```

**Output**: Complete results JSON with all pipeline stages

---

## Data Flow

### Typing Test Flow
```
User Types → keystroke_pd.py → Feature Extraction → Model Prediction → Risk Score
```

### Voice Test Flow
```
User Speaks → audio_recorder.py → spectrogram_generator.py → llm_audio_analyzer.py → Analysis JSON
```

### Eye Blink Flow (Background)
```
Camera Feed → blink_counter.py (MediaPipe) → EAR Calculation → Blink Count
```

### Integrated Multi-Modal Flow (Planned)
```
[Typing Test] → Features A
[Voice Test]  → Features B  → Aggregate Analysis → Final Risk Assessment
[Eye Blinks]  → Features C
```

---

## Dependencies

### Backend Dependencies
Current (`requirements.txt`):
```
opencv-python>=4.8.0
mediapipe>=0.10.0
scipy>=1.11.0
numpy>=1.26.0
```

**Additional Required** (for voice pipeline):
```
pyaudio>=0.2.13
matplotlib>=3.7.0
anthropic>=0.18.0
pandas>=2.0.0
scikit-learn>=1.3.0
joblib>=1.3.0
```

### Frontend Dependencies
```
react, react-dom
typescript
vite
shadcn/ui components
```

---

## Directory Structure

```
/Take2
├── frontend/                 # React frontend
│   ├── src/
│   ├── components.json
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                  # Python backend
│   ├── keystroke_pd.py      # Typing analysis
│   ├── pd_keystroke_rules.py
│   ├── blink_counter.py     # Eye tracking
│   ├── audio_recorder.py    # NEW: Audio capture
│   ├── spectrogram_generator.py  # NEW: Acoustic analysis
│   ├── llm_audio_analyzer.py     # NEW: LLM integration
│   ├── voice_pipeline.py    # NEW: Pipeline orchestrator
│   ├── requirements.txt
│   ├── sessions/            # Keystroke session logs
│   ├── baseline_sessions/   # Baseline typing data
│   ├── baseline_store/
│   ├── audio_sessions/      # NEW: Audio recordings
│   ├── spectrograms/        # NEW: Spectrogram outputs
│   └── llm_analysis/        # NEW: LLM analysis results
│
└── claude.md                # THIS FILE
```

---

## Research Foundation

### Keystroke Dynamics & PD
- Based on "Real-world keystroke dynamics are a potentially valid biomarker for clinical motor impairment in Parkinson's disease" and related research
- Features: Hold times, flight times, rhythm, asymmetry, pauses
- Supervised + unsupervised learning approaches

### Voice Biomarkers & PD
PD affects voice through multiple mechanisms:
- **Tremor**: 4-6 Hz modulation in vocal fold vibration
- **Rigidity**: Reduced pitch range, monotone speech
- **Bradykinesia**: Slow articulation, reduced loudness
- **Coordination**: Imprecise consonants, breathiness

**Key Voice Features**:
- Jitter (frequency perturbation)
- Shimmer (amplitude perturbation)
- Harmonic-to-Noise Ratio (HNR)
- Fundamental frequency (F0) variation
- Spectral characteristics

### Eye Blink & PD
- Reduced spontaneous blink rate in PD
- Increased blink rate variability
- Eye Aspect Ratio (EAR) algorithm by Soukupová and Čech

---

## API Integration Points

### 1. Keystroke Analysis API (Future)
```
POST /api/keystroke/analyze
Body: { features: {...}, baseline_id?: string }
Response: { risk_score: number, model_source: string }
```

### 2. Voice Analysis API (Future)
```
POST /api/voice/analyze
Body: FormData { audio: File, user_metadata?: JSON }
Response: { risk_assessment: {...}, biomarker_findings: {...} }
```

### 3. Eye Blink API (Future)
```
POST /api/blink/analyze
Body: { blink_data: [...], duration: number }
Response: { blink_rate: number, variability: number, risk_indicators: {...} }
```

### 4. Aggregate Analysis API (Future)
```
POST /api/aggregate/analyze
Body: {
  typing_results: {...},
  voice_results: {...},
  blink_results: {...}
}
Response: {
  overall_risk: number,
  confidence: number,
  recommendations: [...]
}
```

---

## Development Workflow

### Backend Setup
```bash
cd backend
pip install -r requirements.txt

# For voice pipeline, add additional deps:
pip install pyaudio matplotlib anthropic pandas scikit-learn joblib

# Set API key
export ANTHROPIC_API_KEY="your-key"

# Test individual modules
python keystroke_pd.py --mode collect_baseline --duration 60
python blink_counter.py
python voice_pipeline.py --mode record --duration 10
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:8081/
```

---

## Next Steps / TODO

### Backend
- [ ] Update `requirements.txt` with voice pipeline dependencies
- [ ] Add Flask/FastAPI REST API layer
- [ ] Implement baseline storage/retrieval system
- [ ] Add multi-modal feature fusion
- [ ] Longitudinal tracking and trend analysis
- [ ] Add authentication/user management

### Frontend
- [ ] Implement React Router for multi-page structure
- [ ] Create typing test UI with real-time feedback
- [ ] Create voice recording UI with waveform visualization
- [ ] Integrate eye blink counter (background service)
- [ ] Build results dashboard with charts (D3.js/Recharts)
- [ ] Implement RAG chatbot for personalized insights
- [ ] Add state management (Redux/Zustand/Context)
- [ ] Connect frontend to backend APIs

### Research/Clinical
- [ ] Validate models with clinical datasets
- [ ] Establish normative baselines by age/demographics
- [ ] Define clinical decision thresholds
- [ ] Add disclaimers and ethical guidelines
- [ ] HIPAA/privacy compliance for health data

---

## Ethical Considerations

⚠️ **Important Disclaimers**:

1. **Not a Diagnostic Tool**: This is a screening/research prototype, not medical diagnosis
2. **Clinical Validation Required**: Models need validation on clinical datasets
3. **False Positives/Negatives**: Screening tools have inherent limitations
4. **Professional Interpretation**: Results should be reviewed by healthcare professionals
5. **Privacy**: Health data requires strict compliance (HIPAA, GDPR)
6. **Bias Considerations**: Models may not generalize across demographics
7. **Longitudinal Tracking**: Single assessments less reliable than trends over time

---

## References

### Keystroke Dynamics
- Giancardo et al. (2016) - "Computer keyboard interaction as an indicator of early Parkinson's disease"
- Adams et al. (2017) - "Real-world keystroke dynamics are a potentially valid biomarker"

### Voice Biomarkers
- Rusz et al. (2011) - "Quantitative acoustic measurements for characterization of speech and voice disorders in early untreated Parkinson's disease"
- Tsanas et al. (2012) - "Novel speech signal processing algorithms for high-accuracy classification of Parkinson's disease"

### Eye Blink
- Soukupová and Čech (2016) - "Real-Time Eye Blink Detection using Facial Landmarks"
- Karson (1983) - "Spontaneous eye-blink rates and dopaminergic systems"

### Multi-Modal Approaches
- Arora et al. (2015) - "Detecting and monitoring the symptoms of Parkinson's disease using smartphones"
- Zham et al. (2017) - "Distinguishing different stages of Parkinson's disease using composite index of speed and pen-pressure"

---

## Contact & Contribution

This is a research prototype. For questions or contributions:
- Review existing issues
- Follow coding standards
- Add tests for new features
- Update this documentation

---

**Last Updated**: 2025-10-05
**Version**: 1.0
**Author**: Claude Code Assistant
