"""
Audio Recording Module for Voice Analysis
Captures audio input from microphone with metadata tracking
"""

import pyaudio
import wave
import time
import json
import pathlib
from datetime import datetime


class AudioRecorder:
    """
    Records audio from microphone and saves to WAV files.
    Tracks metadata including duration, sample rate, and timestamps.
    """

    def __init__(
        self,
        sample_rate=44100,
        channels=1,
        chunk_size=1024,
        audio_format=pyaudio.paInt16
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.audio_format = audio_format
        self.frames = []
        self.is_recording = False
        self.pyaudio_instance = None
        self.stream = None

    def start_recording(self):
        """Initialize PyAudio and start recording"""
        self.frames = []
        self.pyaudio_instance = pyaudio.PyAudio()

        self.stream = self.pyaudio_instance.open(
            format=self.audio_format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )

        self.is_recording = True
        self.start_time = time.time()
        print(f"[AudioRecorder] Recording started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def record_chunk(self):
        """Record a single chunk of audio"""
        if not self.is_recording:
            raise RuntimeError("Recording not started. Call start_recording() first.")

        data = self.stream.read(self.chunk_size, exception_on_overflow=False)
        self.frames.append(data)

    def record_duration(self, duration_seconds):
        """Record for a specific duration"""
        if not self.is_recording:
            self.start_recording()

        chunks_needed = int(self.sample_rate / self.chunk_size * duration_seconds)

        for _ in range(chunks_needed):
            self.record_chunk()

        self.stop_recording()

    def stop_recording(self):
        """Stop recording and cleanup"""
        if not self.is_recording:
            return

        self.is_recording = False
        self.end_time = time.time()

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()

        duration = self.end_time - self.start_time
        print(f"[AudioRecorder] Recording stopped. Duration: {duration:.2f}s")

    def save_wav(self, output_path):
        """Save recorded audio to WAV file"""
        output_path = pathlib.Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with wave.open(str(output_path), 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.pyaudio_instance.get_sample_size(self.audio_format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))

        print(f"[AudioRecorder] Audio saved to {output_path}")
        return output_path

    def get_metadata(self):
        """Return recording metadata"""
        return {
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "duration": self.end_time - self.start_time if hasattr(self, 'end_time') else None,
            "timestamp": datetime.fromtimestamp(self.start_time).isoformat() if hasattr(self, 'start_time') else None,
            "num_frames": len(self.frames)
        }


def record_session(duration_seconds=10, output_dir="audio_sessions"):
    """
    Convenience function to record a single audio session

    Args:
        duration_seconds: Length of recording in seconds
        output_dir: Directory to save audio files

    Returns:
        Tuple of (audio_path, metadata_dict)
    """
    recorder = AudioRecorder()

    print(f"\n[Session] Starting {duration_seconds}s audio recording...")
    print("[Session] Speak naturally into your microphone.")

    recorder.start_recording()
    recorder.record_duration(duration_seconds)

    # Generate output paths
    session_id = int(time.time())
    output_dir = pathlib.Path(output_dir)
    audio_path = output_dir / f"audio_{session_id}.wav"
    metadata_path = output_dir / f"audio_{session_id}_metadata.json"

    # Save audio and metadata
    recorder.save_wav(audio_path)
    metadata = recorder.get_metadata()

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"[Session] Metadata saved to {metadata_path}")

    return str(audio_path), metadata


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Record audio from microphone")
    parser.add_argument("--duration", type=int, default=10, help="Recording duration in seconds")
    parser.add_argument("--output_dir", type=str, default="audio_sessions", help="Output directory")
    args = parser.parse_args()

    audio_path, metadata = record_session(
        duration_seconds=args.duration,
        output_dir=args.output_dir
    )

    print(f"\n✓ Recording complete!")
    print(f"Audio file: {audio_path}")
    print(f"Metadata: {json.dumps(metadata, indent=2)}")
