#!/usr/bin/env python3
"""
Audio Decompressor — Standalone CLI Tool
=========================================
Decompress Opus audio files back to original WAV format.

Usage:
    # Decompress a single file
    python audio_decompressor.py <input.opus> [output.wav]

    # Batch decompress an entire directory
    python audio_decompressor.py --all <directory>

    # Batch decompress into a specific output directory
    python audio_decompressor.py --all <directory> --output-dir <output_directory>

Requirements:
    - ffmpeg must be installed (brew install ffmpeg)
"""

import argparse
import os
import sys
import json
import glob
import shutil
import subprocess
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s │ %(levelname)-7s │ %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def check_ffmpeg():
    """Verify ffmpeg is available."""
    if not shutil.which("ffmpeg"):
        logger.error("❌ ffmpeg is not installed or not on PATH.")
        logger.error("   Install it with: brew install ffmpeg")
        sys.exit(1)


def decompress_file(input_path: str, output_path: str = None,
                    sample_rate: int = 16000) -> str:
    """
    Decompress an Opus file back to WAV (16-bit PCM).

    Args:
        input_path: Path to the .opus (or other compressed) file.
        output_path: Path for the output .wav file. Auto-generated if None.
        sample_rate: Target sample rate for output WAV (default: 16000).

    Returns:
        Path to the decompressed WAV file.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Auto-generate output path if not specified
    if output_path is None:
        output_path = os.path.splitext(input_path)[0] + ".wav"

    # Look for metadata sidecar to get original sample rate
    json_sidecar = os.path.splitext(input_path)[0] + ".json"
    if os.path.exists(json_sidecar):
        try:
            with open(json_sidecar, 'r') as f:
                metadata = json.load(f)
            sample_rate = metadata.get("sample_rate", sample_rate)
            logger.info(f"📋 Metadata found: {metadata.get('duration_seconds', '?')}s, "
                       f"{sample_rate}Hz, recorded at {metadata.get('timestamp', '?')}")
        except Exception:
            pass

    # Run ffmpeg
    cmd = [
        "ffmpeg",
        "-y",                       # Overwrite output
        "-i", input_path,           # Input file
        "-c:a", "pcm_s16le",        # 16-bit PCM (lossless WAV)
        "-ar", str(sample_rate),    # Sample rate
        "-ac", "1",                 # Mono
        output_path
    ]

    logger.info(f"🔧 Decompressing: {os.path.basename(input_path)}")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")

    # Report sizes
    input_size = os.path.getsize(input_path)
    output_size = os.path.getsize(output_path)
    ratio = output_size / input_size if input_size > 0 else 0

    logger.info(f"✅ Decompressed: {os.path.basename(output_path)} "
               f"({input_size:,}B → {output_size:,}B, {ratio:.1f}x expansion)")

    return output_path


def batch_decompress(input_dir: str, output_dir: str = None):
    """
    Decompress all Opus files in a directory.

    Args:
        input_dir: Directory containing .opus files.
        output_dir: Optional output directory for WAV files.
                    If None, WAV files are created alongside the Opus files.
    """
    if not os.path.isdir(input_dir):
        logger.error(f"❌ Not a directory: {input_dir}")
        sys.exit(1)

    # Find all Opus files
    opus_files = sorted(glob.glob(os.path.join(input_dir, "*.opus")))

    if not opus_files:
        # Also check for WAV fallback files (when ffmpeg wasn't available during recording)
        wav_files = sorted(glob.glob(os.path.join(input_dir, "*.wav")))
        if wav_files:
            logger.info(f"ℹ️  Found {len(wav_files)} WAV files (already uncompressed).")
            return
        logger.warning("⚠️  No .opus files found in the directory.")
        return

    # Create output directory if specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    logger.info(f"📂 Found {len(opus_files)} Opus file(s) to decompress")
    logger.info(f"   Source: {input_dir}")
    if output_dir:
        logger.info(f"   Output: {output_dir}")
    logger.info("-" * 50)

    success = 0
    failed = 0

    for opus_file in opus_files:
        try:
            if output_dir:
                base_name = os.path.splitext(os.path.basename(opus_file))[0] + ".wav"
                out_path = os.path.join(output_dir, base_name)
            else:
                out_path = None

            decompress_file(opus_file, out_path)
            success += 1
        except Exception as e:
            logger.error(f"❌ Failed: {os.path.basename(opus_file)} — {e}")
            failed += 1

    logger.info("-" * 50)
    logger.info(f"📊 Done! {success} succeeded, {failed} failed out of {len(opus_files)} files.")


def main():
    parser = argparse.ArgumentParser(
        description="Decompress Opus audio files back to WAV format.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Decompress a single file
  python audio_decompressor.py recording.opus

  # Decompress to a specific output file
  python audio_decompressor.py recording.opus output.wav

  # Batch decompress all files in a directory
  python audio_decompressor.py --all audio_storage/

  # Batch decompress into a separate output folder
  python audio_decompressor.py --all audio_storage/ --output-dir decompressed/
        """
    )

    parser.add_argument(
        "input",
        help="Input .opus file or directory (when used with --all)"
    )
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="Output .wav file path (optional, auto-generated if omitted)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Batch decompress all .opus files in the input directory"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for batch decompression"
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="Target sample rate for output WAV (default: 16000)"
    )

    args = parser.parse_args()

    # Check ffmpeg
    check_ffmpeg()

    print()
    print("=" * 50)
    print("  🔊 Audio Decompressor (Opus → WAV)")
    print("=" * 50)
    print()

    if args.all:
        batch_decompress(args.input, args.output_dir)
    else:
        try:
            result = decompress_file(args.input, args.output, args.sample_rate)
            print(f"\n✅ Output saved to: {result}")
        except FileNotFoundError as e:
            logger.error(str(e))
            sys.exit(1)
        except RuntimeError as e:
            logger.error(str(e))
            sys.exit(1)


if __name__ == "__main__":
    main()
