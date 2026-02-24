#!/usr/bin/env python3
"""
Audio Storage Server — Flask API
==================================
Receives compressed audio files from the mic backend over the local network,
stores them with metadata, and provides decompression on demand.

Endpoints:
    POST   /upload              — Upload compressed audio + metadata
    GET    /files               — List all stored audio files
    GET    /files/<filename>    — Download a specific audio file
    POST   /decompress/<filename> — Decompress Opus → WAV, return WAV
    GET    /health              — Server health check
"""

import os
import sys
import json
import shutil
import subprocess
import logging
from datetime import datetime

from flask import Flask, request, jsonify, send_file, send_from_directory

# ─── Configuration ────────────────────────────────────────────────────────────

STORAGE_PORT = int(os.getenv("STORAGE_PORT", "5050"))
STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join(os.path.dirname(__file__), "audio_storage"))
DECOMPRESS_DIR = os.path.join(STORAGE_DIR, "decompressed")

# ─── Setup ────────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

# Ensure storage directories exist
os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(DECOMPRESS_DIR, exist_ok=True)

# Check ffmpeg
FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    file_count = len([f for f in os.listdir(STORAGE_DIR)
                      if os.path.isfile(os.path.join(STORAGE_DIR, f))])
    return jsonify({
        "status": "ok",
        "server": "Audio Storage Server",
        "storage_dir": STORAGE_DIR,
        "file_count": file_count,
        "ffmpeg_available": FFMPEG_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/upload', methods=['POST'])
def upload():
    """
    Receive a compressed audio file and its metadata.

    Expects multipart form data:
        - file: the compressed audio file (.opus or .wav)
        - metadata: JSON string with recording metadata
    """
    # Validate file
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    audio_file = request.files['file']
    if audio_file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    # Save audio file
    filename = audio_file.filename
    filepath = os.path.join(STORAGE_DIR, filename)

    # Prevent overwriting — append suffix if exists
    base, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(filepath):
        filename = f"{base}_{counter}{ext}"
        filepath = os.path.join(STORAGE_DIR, filename)
        counter += 1

    audio_file.save(filepath)
    file_size = os.path.getsize(filepath)

    # Save metadata if provided
    metadata_json = request.form.get('metadata', None)
    if metadata_json:
        try:
            metadata = json.loads(metadata_json)
        except json.JSONDecodeError:
            metadata = {}
    else:
        metadata = {}

    # Enrich metadata with server-side info
    metadata.update({
        "received_at": datetime.now().isoformat(),
        "stored_filename": filename,
        "stored_size_bytes": file_size,
        "source_ip": request.remote_addr
    })

    json_path = os.path.splitext(filepath)[0] + ".json"
    with open(json_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"📥 Received: {filename} ({file_size:,}B) from {request.remote_addr}")

    return jsonify({
        "status": "ok",
        "filename": filename,
        "size_bytes": file_size,
        "metadata_saved": True
    }), 201


@app.route('/files', methods=['GET'])
def list_files():
    """List all stored audio files with their metadata."""
    files = []

    for entry in sorted(os.listdir(STORAGE_DIR)):
        filepath = os.path.join(STORAGE_DIR, entry)

        # Skip directories and JSON sidecars
        if os.path.isdir(filepath) or entry.endswith('.json'):
            continue

        file_info = {
            "filename": entry,
            "size_bytes": os.path.getsize(filepath),
            "modified": datetime.fromtimestamp(
                os.path.getmtime(filepath)
            ).isoformat()
        }

        # Load metadata sidecar if available
        json_path = os.path.splitext(filepath)[0] + ".json"
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    file_info["metadata"] = json.load(f)
            except Exception:
                pass

        files.append(file_info)

    return jsonify({
        "count": len(files),
        "files": files
    })


@app.route('/files/<filename>', methods=['GET'])
def download_file(filename):
    """Download a specific audio file."""
    filepath = os.path.join(STORAGE_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": f"File not found: {filename}"}), 404

    return send_from_directory(STORAGE_DIR, filename, as_attachment=True)


@app.route('/decompress/<filename>', methods=['POST'])
def decompress(filename):
    """
    Decompress an Opus file to WAV and return it.

    Query params:
        download (bool): If true, return the file. If false, just save and confirm.
    """
    if not FFMPEG_AVAILABLE:
        return jsonify({"error": "ffmpeg is not installed on the storage server"}), 500

    input_path = os.path.join(STORAGE_DIR, filename)
    if not os.path.exists(input_path):
        return jsonify({"error": f"File not found: {filename}"}), 404

    # Generate output path
    wav_name = os.path.splitext(filename)[0] + ".wav"
    output_path = os.path.join(DECOMPRESS_DIR, wav_name)

    # Read metadata for sample rate
    sample_rate = 16000
    json_path = os.path.splitext(input_path)[0] + ".json"
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                meta = json.load(f)
            sample_rate = meta.get("sample_rate", sample_rate)
        except Exception:
            pass

    # Decompress via ffmpeg
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-c:a", "pcm_s16le",
        "-ar", str(sample_rate),
        "-ac", "1",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return jsonify({"error": f"Decompression failed: {result.stderr}"}), 500

    input_size = os.path.getsize(input_path)
    output_size = os.path.getsize(output_path)

    logger.info(f"📂 Decompressed: {filename} → {wav_name} "
                f"({input_size:,}B → {output_size:,}B)")

    # Check if client wants to download the file
    want_download = request.args.get('download', 'false').lower() == 'true'
    if want_download:
        return send_file(output_path, as_attachment=True, download_name=wav_name)

    return jsonify({
        "status": "ok",
        "input": filename,
        "output": wav_name,
        "input_size": input_size,
        "output_size": output_size,
        "expansion_ratio": round(output_size / input_size, 1) if input_size > 0 else 0
    })


# ─── Main ─────────────────────────────────────────────────────────────────────

def create_app():
    """Factory function for the Flask app."""
    return app


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s │ %(levelname)-7s │ %(message)s',
        datefmt='%H:%M:%S'
    )

    print("=" * 60)
    print("  📦 Audio Storage Server")
    print(f"  🌐 Listening on 0.0.0.0:{STORAGE_PORT}")
    print(f"  💾 Storage: {STORAGE_DIR}")
    print(f"  🔧 ffmpeg: {'✅ available' if FFMPEG_AVAILABLE else '❌ not found'}")
    print("=" * 60)
    print()

    app.run(host='0.0.0.0', port=STORAGE_PORT, debug=False)
