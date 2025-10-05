"""
FastAPI Backend for PD Screening Platform
Provides REST endpoints for typing, voice, and eye blink analysis
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import pathlib
import shutil
import os
from datetime import datetime
import tempfile
import asyncio
import time as pytime

# Import our analysis modules (lazy imports to avoid dependency issues)
# from audio_recorder import AudioRecorder
# from spectrogram_generator import generate_spectrogram_from_audio
# from llm_audio_analyzer import analyze_audio_with_llm

app = FastAPI(
    title="PD Screening Platform API",
    description="Multi-modal Parkinson's Disease screening API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081", "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data directories
AUDIO_DIR = pathlib.Path("audio_sessions")
SPECTROGRAM_DIR = pathlib.Path("spectrograms")
ANALYSIS_DIR = pathlib.Path("llm_analysis")
SESSIONS_DIR = pathlib.Path("sessions")

# Create directories
for dir_path in [AUDIO_DIR, SPECTROGRAM_DIR, ANALYSIS_DIR, SESSIONS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Pydantic Models
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

class UserMetadata(BaseModel):
    age: Optional[int] = None
    baseline_id: Optional[str] = None
    notes: Optional[str] = None

class VoiceAnalysisRequest(BaseModel):
    user_metadata: Optional[Dict[str, Any]] = None

class VoiceAnalysisResponse(BaseModel):
    session_id: str
    timestamp: str
    audio_path: str
    spectrogram_path: str
    acoustic_features: Dict[str, Any]
    llm_analysis: Dict[str, Any]
    status: str

class KeystrokeFeatures(BaseModel):
    features: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class KeystrokeAnalysisResponse(BaseModel):
    session_id: str
    risk_score: float
    model_source: str
    features: Dict[str, Any]
    timestamp: str

class BlinkData(BaseModel):
    blink_count: int
    duration_seconds: float
    blink_timestamps: List[float]
    ear_values: Optional[List[float]] = None

class BlinkAnalysisResponse(BaseModel):
    session_id: str
    blink_rate: float  # blinks per minute
    variability: float
    risk_indicators: Dict[str, Any]
    timestamp: str

class AggregateAnalysisRequest(BaseModel):
    typing_results: Optional[Dict[str, Any]] = None
    voice_results: Optional[Dict[str, Any]] = None
    blink_results: Optional[Dict[str, Any]] = None
    user_metadata: Optional[Dict[str, Any]] = None

class AggregateAnalysisResponse(BaseModel):
    overall_risk_score: float
    confidence: float
    risk_category: str
    recommendations: List[str]
    individual_results: Dict[str, Any]
    timestamp: str

# ============================================================================
# Utility Functions
# ============================================================================

def generate_session_id():
    """Generate unique session ID"""
    return f"session_{int(datetime.now().timestamp() * 1000)}"

# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@app.get("/api/health", response_model=HealthResponse)
async def api_health():
    """API health check"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

# ============================================================================
# Voice Analysis Endpoints
# ============================================================================

@app.post("/api/voice/analyze", response_model=VoiceAnalysisResponse)
async def analyze_voice(
    audio: UploadFile = File(...),
    user_metadata: Optional[str] = None
):
    """
    Analyze voice recording for PD biomarkers

    Args:
        audio: WAV audio file
        user_metadata: Optional JSON string with user context

    Returns:
        Complete voice analysis with risk assessment
    """
    session_id = generate_session_id()

    try:
        # Lazy import to avoid dependency issues
        from spectrogram_generator import generate_spectrogram_from_audio
        from llm_audio_analyzer import analyze_audio_with_llm

        # Parse user metadata
        metadata = None
        if user_metadata:
            try:
                metadata = json.loads(user_metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid user_metadata JSON")

        # Save uploaded audio file
        audio_path = AUDIO_DIR / f"{session_id}.wav"
        with open(audio_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        # Generate spectrogram
        spectrogram_path, acoustic_features, spec_metadata = generate_spectrogram_from_audio(
            str(audio_path),
            output_dir=str(SPECTROGRAM_DIR)
        )

        # Run LLM analysis
        analysis = analyze_audio_with_llm(
            spectrogram_path,
            acoustic_features,
            user_metadata=metadata,
            output_dir=str(ANALYSIS_DIR)
        )

        return VoiceAnalysisResponse(
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            audio_path=str(audio_path),
            spectrogram_path=spectrogram_path,
            acoustic_features=acoustic_features,
            llm_analysis=analysis,
            status="completed"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice analysis failed: {str(e)}")

@app.get("/api/voice/spectrogram/{session_id}")
async def get_spectrogram(session_id: str):
    """Get spectrogram image for a session"""
    spectrogram_path = SPECTROGRAM_DIR / f"{session_id}_spectrogram.png"

    if not spectrogram_path.exists():
        raise HTTPException(status_code=404, detail="Spectrogram not found")

    return FileResponse(spectrogram_path, media_type="image/png")

# ============================================================================
# Keystroke Analysis Endpoints
# ============================================================================

@app.post("/api/keystroke/analyze", response_model=KeystrokeAnalysisResponse)
async def analyze_keystroke(data: KeystrokeFeatures):
    """
    Analyze keystroke dynamics for PD indicators

    Args:
        data: Keystroke features and metadata

    Returns:
        Risk score and analysis
    """
    session_id = generate_session_id()

    try:
        # Import here to avoid circular dependencies
        from keystroke_pd import PDKeystrokeModel

        # Initialize model
        model = PDKeystrokeModel(
            model_path="pd_keystroke_model.joblib",
            baseline_dir="baseline_sessions"
        )

        # Predict risk
        risk_score, model_source = model.predict(data.features)

        # Save session
        session_path = SESSIONS_DIR / f"{session_id}_keystroke.json"
        with open(session_path, 'w') as f:
            json.dump({
                "session_id": session_id,
                "features": data.features,
                "metadata": data.metadata,
                "risk_score": risk_score,
                "model_source": model_source,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)

        return KeystrokeAnalysisResponse(
            session_id=session_id,
            risk_score=risk_score,
            model_source=model_source,
            features=data.features,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Keystroke analysis failed: {str(e)}")

# ============================================================================
# Eye Blink Analysis Endpoints
# ============================================================================

@app.post("/api/blink/analyze", response_model=BlinkAnalysisResponse)
async def analyze_blink(data: BlinkData):
    """
    Analyze eye blink patterns for PD indicators

    Args:
        data: Blink count, duration, and timestamps

    Returns:
        Blink rate analysis and risk indicators
    """
    session_id = generate_session_id()

    try:
        # Calculate blink rate (per minute)
        blink_rate = (data.blink_count / data.duration_seconds) * 60

        # Calculate variability (coefficient of variation of inter-blink intervals)
        if len(data.blink_timestamps) > 1:
            import numpy as np
            intervals = np.diff(data.blink_timestamps)
            variability = float(np.std(intervals) / np.mean(intervals)) if np.mean(intervals) > 0 else 0.0
        else:
            variability = 0.0

        # Risk indicators
        # Normal blink rate: 15-20 blinks/min
        # PD typically shows reduced spontaneous blink rate: 5-10 blinks/min
        risk_indicators = {
            "reduced_blink_rate": blink_rate < 12,
            "increased_variability": variability > 0.5,
            "blink_rate_percentile": "low" if blink_rate < 12 else "normal" if blink_rate < 20 else "high"
        }

        # Save session
        session_path = SESSIONS_DIR / f"{session_id}_blink.json"
        with open(session_path, 'w') as f:
            json.dump({
                "session_id": session_id,
                "blink_count": data.blink_count,
                "duration_seconds": data.duration_seconds,
                "blink_rate": blink_rate,
                "variability": variability,
                "risk_indicators": risk_indicators,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)

        return BlinkAnalysisResponse(
            session_id=session_id,
            blink_rate=blink_rate,
            variability=variability,
            risk_indicators=risk_indicators,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blink analysis failed: {str(e)}")

# ============================================================================
# Aggregate Multi-Modal Analysis
# ============================================================================

@app.post("/api/aggregate/analyze", response_model=AggregateAnalysisResponse)
async def analyze_aggregate(data: AggregateAnalysisRequest):
    """
    Aggregate analysis across typing, voice, and blink modalities

    Args:
        data: Results from individual tests

    Returns:
        Overall risk assessment with recommendations
    """
    session_id = generate_session_id()

    try:
        import numpy as np

        # Extract risk scores from each modality
        risk_scores = []
        weights = []

        # Keystroke risk (0-1 scale)
        if data.typing_results:
            typing_risk = data.typing_results.get("risk_score", 0.0)
            risk_scores.append(typing_risk)
            weights.append(0.35)  # 35% weight

        # Voice risk (0-1 scale from LLM)
        if data.voice_results:
            voice_risk = data.voice_results.get("llm_analysis", {}).get("risk_assessment", {}).get("overall_risk_score", 0.0)
            risk_scores.append(voice_risk)
            weights.append(0.40)  # 40% weight (most sensitive)

        # Blink risk (normalized)
        if data.blink_results:
            blink_rate = data.blink_results.get("blink_rate", 15)
            # Convert blink rate to risk score (inverse relationship)
            # Normal: 15-20, PD: 5-10
            blink_risk = max(0.0, min(1.0, (20 - blink_rate) / 15))
            risk_scores.append(blink_risk)
            weights.append(0.25)  # 25% weight

        # Calculate weighted average
        if risk_scores:
            # Normalize weights
            weights = np.array(weights)
            weights = weights / weights.sum()

            overall_risk = float(np.average(risk_scores, weights=weights))
            confidence = float(len(risk_scores) / 3.0)  # Confidence based on completeness
        else:
            overall_risk = 0.0
            confidence = 0.0

        # Categorize risk
        if overall_risk < 0.3:
            risk_category = "low"
        elif overall_risk < 0.5:
            risk_category = "moderate"
        elif overall_risk < 0.7:
            risk_category = "elevated"
        else:
            risk_category = "high"

        # Generate recommendations
        recommendations = []

        if risk_category in ["elevated", "high"]:
            recommendations.append("Consider consultation with a neurologist for professional evaluation")
            recommendations.append("Monitor symptoms over time with repeated assessments")

        if data.typing_results and data.typing_results.get("risk_score", 0) > 0.5:
            recommendations.append("Typing patterns show irregularities - track changes over time")

        if data.voice_results and voice_risk > 0.5:
            recommendations.append("Voice analysis indicates potential vocal changes - consider speech therapy consultation")

        if data.blink_results and blink_risk > 0.5:
            recommendations.append("Reduced blink rate observed - discuss with healthcare provider")

        if risk_category == "low":
            recommendations.append("Results appear normal - continue regular health monitoring")
            recommendations.append("Consider establishing a baseline by repeating tests periodically")

        # Save aggregate analysis
        session_path = SESSIONS_DIR / f"{session_id}_aggregate.json"
        with open(session_path, 'w') as f:
            json.dump({
                "session_id": session_id,
                "overall_risk_score": overall_risk,
                "confidence": confidence,
                "risk_category": risk_category,
                "recommendations": recommendations,
                "individual_results": {
                    "typing": data.typing_results,
                    "voice": data.voice_results,
                    "blink": data.blink_results
                },
                "user_metadata": data.user_metadata,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)

        return AggregateAnalysisResponse(
            overall_risk_score=overall_risk,
            confidence=confidence,
            risk_category=risk_category,
            recommendations=recommendations,
            individual_results={
                "typing": data.typing_results,
                "voice": data.voice_results,
                "blink": data.blink_results
            },
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Aggregate analysis failed: {str(e)}")

# ============================================================================
# WebSocket Keystroke Analysis
# ============================================================================

@app.websocket("/ws/keystroke")
async def websocket_keystroke(websocket: WebSocket):
    """
    WebSocket endpoint for real-time keystroke analysis

    Client sends: {"type": "press"|"release", "key": "a", "timestamp": 1234567890.123}
    Server sends: {"status": "analyzing", "keystrokes": 50, "score": 0.3, ...}
    """
    await websocket.accept()

    # Import analyzer
    from websocket_keystroke import KeystrokeAnalyzer

    analyzer = KeystrokeAnalyzer(baseline_dir="baseline_store")
    session_id = generate_session_id()

    try:
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "WebSocket connected. Start typing..."
        })

        while True:
            # Receive keystroke event
            data = await websocket.receive_json()

            if data.get("type") == "end":
                # Client signals end of session
                final_result = analyzer.finalize_session()

                # Save session
                session_path = SESSIONS_DIR / f"{session_id}_keystroke.json"
                with open(session_path, 'w') as f:
                    json.dump({
                        "session_id": session_id,
                        **final_result
                    }, f, indent=2)

                await websocket.send_json({
                    "type": "final",
                    "session_id": session_id,
                    **final_result
                })
                break

            # Process keystroke
            event_type = data.get("event_type")  # "press" or "release"
            key = data.get("key", "")
            timestamp = data.get("timestamp", pytime.time())

            # Analyze
            metrics = analyzer.process_keystroke(event_type, key, timestamp)

            # Send back current metrics
            await websocket.send_json({
                "type": "update",
                "session_id": session_id,
                **metrics
            })

    except WebSocketDisconnect:
        print(f"[WebSocket] Client disconnected: {session_id}")
        # Save whatever data we have
        final_result = analyzer.finalize_session()
        session_path = SESSIONS_DIR / f"{session_id}_keystroke_incomplete.json"
        with open(session_path, 'w') as f:
            json.dump({
                "session_id": session_id,
                "status": "incomplete",
                **final_result
            }, f, indent=2)
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })

# ============================================================================
# Session Management Endpoints
# ============================================================================

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Retrieve a specific session's data"""

    # Try different file types
    for suffix in ["_keystroke.json", "_blink.json", "_aggregate.json", "_complete_results.json"]:
        session_path = SESSIONS_DIR / f"{session_id}{suffix}"
        if session_path.exists():
            with open(session_path, 'r') as f:
                return json.load(f)

    # Try analysis directory
    analysis_path = ANALYSIS_DIR / f"{session_id}_llm_analysis.json"
    if analysis_path.exists():
        with open(analysis_path, 'r') as f:
            return json.load(f)

    raise HTTPException(status_code=404, detail="Session not found")

@app.get("/api/sessions")
async def list_sessions(limit: int = 10):
    """List recent sessions"""

    sessions = []

    # Get all session files
    for json_file in sorted(SESSIONS_DIR.glob("*.json"), reverse=True)[:limit]:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                sessions.append({
                    "session_id": data.get("session_id", json_file.stem),
                    "timestamp": data.get("timestamp"),
                    "type": "keystroke" if "_keystroke" in json_file.name else
                            "blink" if "_blink" in json_file.name else
                            "aggregate" if "_aggregate" in json_file.name else "unknown"
                })
        except:
            pass

    return {"sessions": sessions, "total": len(sessions)}

# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
