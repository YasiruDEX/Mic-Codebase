#!/usr/bin/env python3
"""
Generate a simple project overview PDF for the Classroom Whisper Monitor.
Run: python generate_pdf.py
Output: Classroom_Whisper_Monitor_Report.pdf
"""

from fpdf import FPDF
from datetime import datetime


class ProjectPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, 'Classroom Whisper Monitor', align='L')
        self.cell(0, 8, 'Project Report', align='R', new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(41, 128, 185)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

    def section_title(self, title):
        self.ln(4)
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(41, 128, 185)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(41, 128, 185)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(3)

    def sub_title(self, title):
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")

    def body_text(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def bullet(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(60, 60, 60)
        x = self.get_x()
        self.set_x(x + 8)
        self.multi_cell(0, 5.5, '- ' + text)
        self.set_x(x)

    def tech_table(self, data):
        self.set_font('Helvetica', 'B', 10)
        self.set_fill_color(41, 128, 185)
        self.set_text_color(255, 255, 255)
        self.cell(60, 8, 'Technology', border=1, fill=True, align='C')
        self.cell(60, 8, 'Purpose', border=1, fill=True, align='C')
        self.cell(65, 8, 'Details', border=1, fill=True, align='C',
                  new_x="LMARGIN", new_y="NEXT")

        self.set_font('Helvetica', '', 9)
        self.set_text_color(50, 50, 50)
        fill = False
        for row in data:
            if fill:
                self.set_fill_color(235, 245, 252)
            else:
                self.set_fill_color(255, 255, 255)
            self.cell(60, 7, row[0], border=1, fill=True)
            self.cell(60, 7, row[1], border=1, fill=True)
            self.cell(65, 7, row[2], border=1, fill=True,
                      new_x="LMARGIN", new_y="NEXT")
            fill = not fill


def generate():
    pdf = ProjectPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ─── Page 1: Title + Overview ─────────────────────────────────────
    pdf.add_page()

    pdf.ln(20)
    pdf.set_font('Helvetica', 'B', 28)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 15, 'Classroom Whisper Monitor', align='C', new_x="LMARGIN", new_y="NEXT")

    pdf.set_font('Helvetica', '', 14)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 10, 'Real-time Voice Activity Detection & Audio Storage System',
             align='C', new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    pdf.ln(15)

    pdf.section_title('1. Project Overview')
    pdf.body_text(
        'The Classroom Whisper Monitor is a real-time voice activity detection system '
        'designed for classroom environments. It uses a ReSpeaker USB Mic Array for '
        'Direction of Arrival (DOA) estimation and a deep learning model (Silero VAD) '
        'for voice activity detection. The system streams live data to a React dashboard '
        'via Firebase Realtime Database, and records audio segments with Opus compression '
        'to a separate networked storage server.'
    )

    pdf.section_title('2. System Architecture')
    pdf.body_text(
        'The system consists of three main components that communicate over the network:'
    )
    pdf.ln(2)

    pdf.sub_title('Component 1: Mic Backend (Machine A)')
    pdf.bullet('Captures audio from system microphone at 16kHz mono')
    pdf.bullet('Runs Silero VAD deep learning model for voice detection')
    pdf.bullet('Reads DOA from ReSpeaker Mic Array hardware')
    pdf.bullet('Pushes live DOA + VAD data to Firebase Realtime Database')
    pdf.bullet('Compresses audio into 30-second Opus segments')
    pdf.bullet('Uploads compressed segments to Storage Server via HTTP POST')
    pdf.ln(3)

    pdf.sub_title('Component 2: Storage Server (Machine B)')
    pdf.bullet('Flask REST API server listening on port 5050')
    pdf.bullet('Receives compressed audio uploads from Mic Backend')
    pdf.bullet('Stores .opus files with JSON metadata sidecars')
    pdf.bullet('Provides on-demand decompression (Opus to WAV via ffmpeg)')
    pdf.bullet('Exposes endpoints: /upload, /files, /decompress, /health')
    pdf.ln(3)

    pdf.sub_title('Component 3: React Frontend')
    pdf.bullet('Real-time dashboard showing DOA and voice activity')
    pdf.bullet('Connects to Firebase Realtime Database for live updates')
    pdf.bullet('Whisper detection alerts with browser notifications')
    pdf.bullet('Voice activity tracker chart and student statistics')

    # ─── Page 2: Technologies ─────────────────────────────────────────
    pdf.add_page()

    pdf.section_title('3. Technologies Used')
    pdf.ln(2)

    tech_data = [
        ['Python 3.13', 'Backend language', 'Mic backend + Storage server'],
        ['Silero VAD', 'Voice detection', 'PyTorch deep learning model'],
        ['ReSpeaker Mic Array', 'Audio hardware', 'USB 4-mic array, DOA + VAD'],
        ['sounddevice', 'Audio capture', '16kHz mono, float32 stream'],
        ['Opus Codec', 'Audio compression', '~10:1 ratio via ffmpeg'],
        ['ffmpeg 8.0', 'Audio encoding', 'Opus encode/decode, WAV convert'],
        ['Flask', 'Storage server API', 'REST endpoints, file handling'],
        ['Firebase Admin SDK', 'Real-time database', 'Live DOA/VAD data push'],
        ['Firebase RTDB', 'Cloud database', 'Real-time sync to frontend'],
        ['React (Vite)', 'Frontend framework', 'Dashboard UI, live charts'],
        ['NumPy', 'Audio processing', 'Float32 array manipulation'],
        ['PyTorch', 'Deep learning', 'Silero VAD model inference'],
        ['requests', 'HTTP client', 'Audio upload to storage server'],
    ]

    pdf.tech_table(tech_data)

    pdf.ln(6)
    pdf.section_title('4. Audio Compression')
    pdf.body_text(
        'The system uses the Opus codec for audio compression, which is the '
        'state-of-the-art codec for speech audio. Key characteristics:'
    )
    pdf.bullet('Compression ratio: approximately 9:1 for 16kHz speech audio')
    pdf.bullet('Encoding bitrate: 32 kbps (configurable)')
    pdf.bullet('Application mode: VoIP (optimized for speech)')
    pdf.bullet('Frame duration: 20ms')
    pdf.bullet('Open standard, royalty-free (RFC 6716)')
    pdf.bullet('Fallback: saves as uncompressed WAV if ffmpeg is unavailable')
    pdf.ln(2)
    pdf.body_text(
        'A standalone decompression script (audio_decompressor.py) recovers the '
        'original WAV audio from compressed Opus files, supporting both single-file '
        'and batch decompression modes.'
    )

    # ─── Page 3: API + File Structure ─────────────────────────────────
    pdf.add_page()

    pdf.section_title('5. Storage Server API Endpoints')
    pdf.ln(2)

    api_data = [
        ['GET  /health', 'Health check', 'Returns server status and file count'],
        ['POST /upload', 'Upload audio', 'Multipart: file + metadata JSON'],
        ['GET  /files', 'List files', 'Returns all stored files with metadata'],
        ['GET  /files/<name>', 'Download file', 'Returns the audio file'],
        ['POST /decompress/<name>', 'Decompress', 'Opus to WAV conversion'],
    ]

    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_fill_color(41, 128, 185)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(45, 8, 'Endpoint', border=1, fill=True, align='C')
    pdf.cell(40, 8, 'Description', border=1, fill=True, align='C')
    pdf.cell(100, 8, 'Details', border=1, fill=True, align='C',
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(50, 50, 50)
    fill = False
    for row in api_data:
        if fill:
            pdf.set_fill_color(235, 245, 252)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.cell(45, 7, row[0], border=1, fill=True)
        pdf.cell(40, 7, row[1], border=1, fill=True)
        pdf.cell(100, 7, row[2], border=1, fill=True,
                 new_x="LMARGIN", new_y="NEXT")
        fill = not fill

    pdf.ln(6)
    
    pdf.section_title('7. Configuration')
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.body_text('Environment variables (.env file):')
    pdf.bullet('FIREBASE_DATABASE_URL - Firebase Realtime Database URL')
    pdf.bullet('FIREBASE_CREDENTIALS - Path to Firebase admin SDK JSON')
    pdf.bullet('STORAGE_SERVER_URL - Storage server address (default: http://localhost:5050)')
    pdf.bullet('AUDIO_SEGMENT_SECONDS - Segment duration in seconds (default: 30)')
    pdf.bullet('VOICE_THRESHOLD - VAD confidence threshold (default: 0.5)')
    pdf.bullet('UPDATE_INTERVAL - Firebase update interval (default: 0.1s)')
    pdf.bullet('STORAGE_PORT - Storage server port (default: 5050)')

    # ─── Save ─────────────────────────────────────────────────────────
    output_path = 'Classroom_Whisper_Monitor_Report.pdf'
    pdf.output(output_path)
    print(f"PDF generated: {output_path}")
    return output_path


if __name__ == '__main__':
    generate()
