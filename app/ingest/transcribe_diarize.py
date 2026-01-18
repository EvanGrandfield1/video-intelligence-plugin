#!/usr/bin/env python3
"""
Transcription + Speaker Diarization using WhisperX and pyannote.
Outputs JSON transcript with speaker labels and timestamps.
"""
import argparse
import json
import os
import sys

def transcribe_and_diarize(audio_path: str, output_path: str, hf_token: str = None):
    """
    Transcribe audio and perform speaker diarization.
    Falls back to basic whisper if whisperx/pyannote unavailable.
    """
    # Try whisperx first (best quality)
    try:
        import whisperx
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        print(f"🎙️ Loading WhisperX model on {device}...")
        model = whisperx.load_model("large-v2", device, compute_type=compute_type)

        print(f"🎙️ Transcribing: {audio_path}")
        audio = whisperx.load_audio(audio_path)
        result = model.transcribe(audio, batch_size=16)

        # Align whisper output
        print("🎙️ Aligning transcript...")
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
        result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

        # Diarize (requires HF token for pyannote)
        if hf_token:
            print("🎙️ Performing speaker diarization...")
            diarize_model = whisperx.DiarizationPipeline(use_auth_token=hf_token, device=device)
            diarize_segments = diarize_model(audio)
            result = whisperx.assign_word_speakers(diarize_segments, result)

        # Format output
        transcript = []
        for seg in result.get("segments", []):
            transcript.append({
                "start": round(seg.get("start", 0), 2),
                "end": round(seg.get("end", 0), 2),
                "speaker": seg.get("speaker", "SPEAKER_00"),
                "text": seg.get("text", "").strip()
            })

        with open(output_path, "w") as f:
            json.dump({"segments": transcript}, f, indent=2)

        print(f"✅ Transcript saved to: {output_path}")
        return transcript

    except ImportError:
        print("⚠️ WhisperX not available, falling back to basic whisper...")

    # Fallback to basic whisper
    try:
        import whisper

        print(f"🎙️ Loading Whisper model...")
        model = whisper.load_model("base")

        print(f"🎙️ Transcribing: {audio_path}")
        result = model.transcribe(audio_path)

        transcript = []
        for seg in result.get("segments", []):
            transcript.append({
                "start": round(seg.get("start", 0), 2),
                "end": round(seg.get("end", 0), 2),
                "speaker": "SPEAKER_00",  # No diarization in basic whisper
                "text": seg.get("text", "").strip()
            })

        with open(output_path, "w") as f:
            json.dump({"segments": transcript}, f, indent=2)

        print(f"✅ Transcript saved to: {output_path}")
        return transcript

    except ImportError:
        print("❌ Neither whisperx nor whisper is installed.")
        print("   Install with: pip install openai-whisper  OR  pip install whisperx")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcribe and diarize audio")
    parser.add_argument("audio_path", help="Path to audio file (wav)")
    parser.add_argument("--output", "-o", required=True, help="Output JSON path")
    parser.add_argument("--hf_token", help="HuggingFace token for pyannote diarization")

    args = parser.parse_args()

    # Try to get HF token from env if not provided
    hf_token = args.hf_token or os.environ.get("HF_TOKEN")

    if not os.path.exists(args.audio_path):
        print(f"❌ Audio file not found: {args.audio_path}")
        sys.exit(1)

    transcribe_and_diarize(args.audio_path, args.output, hf_token)
