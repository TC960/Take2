"""
Complete Voice Analysis Pipeline
Orchestrates: Audio Recording → Spectrogram Generation → LLM Analysis
"""

import argparse
import json
import pathlib
from datetime import datetime

from audio_recorder import record_session
from spectrogram_generator import generate_spectrogram_from_audio
from llm_audio_analyzer import analyze_audio_with_llm


class VoiceAnalysisPipeline:
    """
    Complete pipeline for voice-based PD screening
    """

    def __init__(
        self,
        audio_dir="audio_sessions",
        spectrogram_dir="spectrograms",
        analysis_dir="llm_analysis"
    ):
        self.audio_dir = pathlib.Path(audio_dir)
        self.spectrogram_dir = pathlib.Path(spectrogram_dir)
        self.analysis_dir = pathlib.Path(analysis_dir)

        # Create directories
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.spectrogram_dir.mkdir(parents=True, exist_ok=True)
        self.analysis_dir.mkdir(parents=True, exist_ok=True)

    def run_full_analysis(
        self,
        duration_seconds=10,
        user_metadata=None,
        save_intermediate=True
    ):
        """
        Run complete voice analysis pipeline

        Args:
            duration_seconds: Recording duration
            user_metadata: Optional user context (age, baseline, etc.)
            save_intermediate: Whether to save intermediate outputs

        Returns:
            Complete analysis results dictionary
        """
        print("=" * 60)
        print("VOICE ANALYSIS PIPELINE - PD SCREENING")
        print("=" * 60)

        # Step 1: Record Audio
        print("\n[Step 1/3] Recording Audio...")
        audio_path, audio_metadata = record_session(
            duration_seconds=duration_seconds,
            output_dir=str(self.audio_dir)
        )

        # Step 2: Generate Spectrogram
        print("\n[Step 2/3] Generating Spectrogram...")
        spectrogram_path, acoustic_features, spec_metadata = generate_spectrogram_from_audio(
            audio_path,
            output_dir=str(self.spectrogram_dir)
        )

        # Step 3: LLM Analysis
        print("\n[Step 3/3] Running LLM Analysis...")
        analysis = analyze_audio_with_llm(
            spectrogram_path,
            acoustic_features,
            user_metadata=user_metadata,
            output_dir=str(self.analysis_dir)
        )

        # Compile complete results
        complete_results = {
            "pipeline_version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "audio": {
                "path": audio_path,
                "metadata": audio_metadata
            },
            "spectrogram": {
                "path": spectrogram_path,
                "acoustic_features": acoustic_features,
                "metadata": spec_metadata
            },
            "llm_analysis": analysis,
            "user_metadata": user_metadata
        }

        # Save complete results
        session_id = pathlib.Path(audio_path).stem
        results_path = self.analysis_dir / f"{session_id}_complete_results.json"

        with open(results_path, 'w') as f:
            json.dump(complete_results, f, indent=2)

        print(f"\n{'=' * 60}")
        print(f"✓ ANALYSIS COMPLETE")
        print(f"{'=' * 60}")
        print(f"Complete results: {results_path}")

        return complete_results

    def run_from_existing_audio(self, audio_path, user_metadata=None):
        """
        Run pipeline on existing audio file (skip recording step)

        Args:
            audio_path: Path to existing WAV file
            user_metadata: Optional user context

        Returns:
            Complete analysis results
        """
        print("=" * 60)
        print("VOICE ANALYSIS PIPELINE - FROM EXISTING AUDIO")
        print("=" * 60)

        # Step 1: Generate Spectrogram
        print("\n[Step 1/2] Generating Spectrogram...")
        spectrogram_path, acoustic_features, spec_metadata = generate_spectrogram_from_audio(
            audio_path,
            output_dir=str(self.spectrogram_dir)
        )

        # Step 2: LLM Analysis
        print("\n[Step 2/2] Running LLM Analysis...")
        analysis = analyze_audio_with_llm(
            spectrogram_path,
            acoustic_features,
            user_metadata=user_metadata,
            output_dir=str(self.analysis_dir)
        )

        # Compile results
        complete_results = {
            "pipeline_version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "audio": {
                "path": str(audio_path),
                "metadata": spec_metadata
            },
            "spectrogram": {
                "path": spectrogram_path,
                "acoustic_features": acoustic_features
            },
            "llm_analysis": analysis,
            "user_metadata": user_metadata
        }

        # Save results
        session_id = pathlib.Path(audio_path).stem
        results_path = self.analysis_dir / f"{session_id}_complete_results.json"

        with open(results_path, 'w') as f:
            json.dump(complete_results, f, indent=2)

        print(f"\n{'=' * 60}")
        print(f"✓ ANALYSIS COMPLETE")
        print(f"{'=' * 60}")
        print(f"Complete results: {results_path}")

        return complete_results


def main():
    parser = argparse.ArgumentParser(
        description="Voice Analysis Pipeline for PD Screening"
    )

    parser.add_argument(
        "--mode",
        choices=["record", "analyze"],
        default="record",
        help="'record' for new recording + analysis, 'analyze' for existing audio"
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=10,
        help="Recording duration in seconds (for 'record' mode)"
    )

    parser.add_argument(
        "--audio_path",
        type=str,
        help="Path to existing audio file (for 'analyze' mode)"
    )

    parser.add_argument(
        "--user_metadata",
        type=str,
        help="Path to JSON file with user metadata"
    )

    parser.add_argument(
        "--audio_dir",
        type=str,
        default="audio_sessions",
        help="Directory for audio files"
    )

    parser.add_argument(
        "--spectrogram_dir",
        type=str,
        default="spectrograms",
        help="Directory for spectrogram outputs"
    )

    parser.add_argument(
        "--analysis_dir",
        type=str,
        default="llm_analysis",
        help="Directory for analysis results"
    )

    args = parser.parse_args()

    # Load user metadata if provided
    user_metadata = None
    if args.user_metadata:
        with open(args.user_metadata, 'r') as f:
            user_metadata = json.load(f)

    # Initialize pipeline
    pipeline = VoiceAnalysisPipeline(
        audio_dir=args.audio_dir,
        spectrogram_dir=args.spectrogram_dir,
        analysis_dir=args.analysis_dir
    )

    # Run pipeline
    if args.mode == "record":
        results = pipeline.run_full_analysis(
            duration_seconds=args.duration,
            user_metadata=user_metadata
        )
    elif args.mode == "analyze":
        if not args.audio_path:
            parser.error("--audio_path required for 'analyze' mode")
        results = pipeline.run_from_existing_audio(
            args.audio_path,
            user_metadata=user_metadata
        )

    # Print summary
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)

    llm_response = results.get("llm_analysis", {}).get("raw_response", "")
    if llm_response:
        # Try to extract JSON from response
        try:
            # Look for JSON block in response
            import re
            json_match = re.search(r'```json\n(.*?)\n```', llm_response, re.DOTALL)
            if json_match:
                analysis_json = json.loads(json_match.group(1))
                print("\nRisk Assessment:")
                print(json.dumps(analysis_json.get("risk_assessment", {}), indent=2))
                print("\nClinical Interpretation:")
                print(json.dumps(analysis_json.get("clinical_interpretation", {}), indent=2))
            else:
                print(llm_response[:1000])
        except:
            print(llm_response[:1000])


if __name__ == "__main__":
    main()
