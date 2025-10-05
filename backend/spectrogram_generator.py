"""
Spectrogram Generation Module
Converts audio files to visual spectrograms for LLM analysis
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import matplotlib.pyplot as plt
from scipy import signal
from scipy.io import wavfile
import pathlib
import json
from datetime import datetime


class SpectrogramGenerator:
    """
    Generates mel spectrograms from audio files.
    Optimized for voice analysis and neural tremor detection.
    """

    def __init__(
        self,
        n_fft=2048,
        hop_length=512,
        n_mels=128,
        fmin=50,
        fmax=8000
    ):
        """
        Args:
            n_fft: FFT window size
            hop_length: Number of samples between successive frames
            n_mels: Number of mel bands
            fmin: Minimum frequency (Hz)
            fmax: Maximum frequency (Hz)
        """
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.n_mels = n_mels
        self.fmin = fmin
        self.fmax = fmax

    def generate_from_wav(self, wav_path, output_path=None):
        """
        Generate spectrogram from WAV file

        Args:
            wav_path: Path to input WAV file
            output_path: Path to save spectrogram image (optional)

        Returns:
            dict with spectrogram data and metadata
        """
        wav_path = pathlib.Path(wav_path)

        # Read audio file
        sample_rate, audio_data = wavfile.read(wav_path)

        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        # Normalize audio
        audio_data = audio_data.astype(np.float32)
        audio_data = audio_data / np.max(np.abs(audio_data))

        # Generate spectrogram using STFT
        frequencies, times, spectrogram = signal.spectrogram(
            audio_data,
            fs=sample_rate,
            window='hann',
            nperseg=self.n_fft,
            noverlap=self.n_fft - self.hop_length,
            scaling='density'
        )

        # Convert to dB scale
        spectrogram_db = 10 * np.log10(spectrogram + 1e-10)

        # Filter frequency range
        freq_mask = (frequencies >= self.fmin) & (frequencies <= self.fmax)
        frequencies = frequencies[freq_mask]
        spectrogram_db = spectrogram_db[freq_mask, :]

        # Extract features for analysis
        features = self._extract_features(spectrogram_db, frequencies, times, sample_rate)

        # Generate visualization if output path provided
        if output_path:
            output_path = pathlib.Path(output_path)
            self._save_visualization(
                spectrogram_db,
                frequencies,
                times,
                output_path,
                features
            )

        return {
            "spectrogram": spectrogram_db.tolist(),
            "frequencies": frequencies.tolist(),
            "times": times.tolist(),
            "features": features,
            "metadata": {
                "wav_path": str(wav_path),
                "sample_rate": int(sample_rate),
                "duration": float(len(audio_data) / sample_rate),
                "n_fft": self.n_fft,
                "hop_length": self.hop_length,
                "timestamp": datetime.now().isoformat()
            }
        }

    def _extract_features(self, spectrogram_db, frequencies, times, sample_rate):
        """
        Extract acoustic features relevant for PD voice analysis

        Key features:
        - Fundamental frequency (F0) variation
        - Harmonic-to-noise ratio (HNR)
        - Spectral centroid
        - Tremor frequency bands (4-6 Hz typical for PD)
        """
        features = {}

        # Spectral centroid (weighted mean of frequencies)
        spectral_centroid = np.sum(frequencies[:, np.newaxis] * spectrogram_db, axis=0) / np.sum(spectrogram_db, axis=0)
        features["spectral_centroid_mean"] = float(np.mean(spectral_centroid))
        features["spectral_centroid_std"] = float(np.std(spectral_centroid))

        # Energy concentration in low frequencies (tremor indicator)
        tremor_band = (frequencies >= 4) & (frequencies <= 6)
        total_energy = np.sum(spectrogram_db, axis=0)
        tremor_energy = np.sum(spectrogram_db[tremor_band, :], axis=0)
        features["tremor_band_ratio"] = float(np.mean(tremor_energy / (total_energy + 1e-10)))

        # Spectral flatness (tonality measure)
        spectral_flatness = np.exp(np.mean(np.log(spectrogram_db + 1e-10), axis=0)) / (np.mean(spectrogram_db, axis=0) + 1e-10)
        features["spectral_flatness_mean"] = float(np.mean(spectral_flatness))

        # Frequency stability (variance over time)
        freq_stability = np.std(spectral_centroid)
        features["frequency_stability"] = float(freq_stability)

        # High frequency energy (aspiration/breathiness indicator)
        high_freq_band = frequencies >= 4000
        high_freq_energy = np.sum(spectrogram_db[high_freq_band, :], axis=0)
        features["high_freq_energy_ratio"] = float(np.mean(high_freq_energy / (total_energy + 1e-10)))

        # Temporal features
        features["duration_seconds"] = float(times[-1] - times[0])
        features["num_frames"] = int(len(times))

        return features

    def _save_visualization(self, spectrogram_db, frequencies, times, output_path, features):
        """Generate and save spectrogram visualization with feature annotations"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(12, 6))

        # Plot spectrogram
        im = ax.pcolormesh(
            times,
            frequencies,
            spectrogram_db,
            shading='gouraud',
            cmap='viridis'
        )

        ax.set_ylabel('Frequency [Hz]')
        ax.set_xlabel('Time [sec]')
        ax.set_title('Voice Spectrogram Analysis')

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Intensity [dB]')

        # Annotate key features
        annotation_text = (
            f"Spectral Centroid: {features['spectral_centroid_mean']:.1f} Hz\n"
            f"Tremor Band (4-6 Hz): {features['tremor_band_ratio']:.3f}\n"
            f"Freq Stability: {features['frequency_stability']:.2f}"
        )

        ax.text(
            0.02, 0.98, annotation_text,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"[Spectrogram] Visualization saved to {output_path}")


def generate_spectrogram_from_audio(wav_path, output_dir="spectrograms"):
    """
    Convenience function to generate spectrogram from audio file

    Args:
        wav_path: Path to WAV file
        output_dir: Directory to save spectrogram outputs

    Returns:
        Tuple of (image_path, features_dict, metadata_dict)
    """
    wav_path = pathlib.Path(wav_path)
    output_dir = pathlib.Path(output_dir)

    # Generate unique ID from wav filename
    session_id = wav_path.stem

    # Output paths
    image_path = output_dir / f"{session_id}_spectrogram.png"
    features_path = output_dir / f"{session_id}_features.json"

    # Generate spectrogram
    generator = SpectrogramGenerator()
    result = generator.generate_from_wav(wav_path, output_path=image_path)

    # Save features to JSON
    features_path.parent.mkdir(parents=True, exist_ok=True)
    with open(features_path, 'w') as f:
        json.dump({
            "features": result["features"],
            "metadata": result["metadata"]
        }, f, indent=2)

    print(f"[Spectrogram] Features saved to {features_path}")

    return str(image_path), result["features"], result["metadata"]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate spectrogram from audio file")
    parser.add_argument("wav_path", type=str, help="Path to WAV file")
    parser.add_argument("--output_dir", type=str, default="spectrograms", help="Output directory")
    args = parser.parse_args()

    image_path, features, metadata = generate_spectrogram_from_audio(
        args.wav_path,
        output_dir=args.output_dir
    )

    print(f"\n✓ Spectrogram generation complete!")
    print(f"Image: {image_path}")
    print(f"\nExtracted Features:")
    print(json.dumps(features, indent=2))
