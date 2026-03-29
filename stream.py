"""
Live camera stream for Ivar.

Run this to start a web server that streams the camera feed
with real-time object detection overlays and live conversation transcript.
Open http://ivar.local:8080 in any browser to watch.
"""

import io
import json
import time
import logging
from collections import deque
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread, Lock

from config import CAMERA_RESOLUTION, JPEG_QUALITY, STREAM_PORT

logger = logging.getLogger(__name__)

try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False

# Global reference to the camera for the request handler
_ivar_camera = None
_picam2 = None

# Transcript: shared conversation log
_transcript = deque(maxlen=50)
_transcript_lock = Lock()
_transcript_version = 0


def update_transcript(role: str, text: str):
    """Add a message to the transcript. Called from main.py."""
    global _transcript_version
    with _transcript_lock:
        _transcript.append({"role": role, "text": text})
        _transcript_version += 1


class StreamHandler(BaseHTTPRequestHandler):
    """HTTP handler that serves an MJPEG stream, transcript, and viewer page."""

    def do_GET(self):
        if self.path == "/":
            self._serve_page()
        elif self.path == "/stream":
            self._serve_stream()
        elif self.path.startswith("/transcript"):
            self._serve_transcript()
        else:
            self.send_error(404)

    def _serve_page(self):
        """Serve a simple HTML page with camera feed and live transcript."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Ivar - Live</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: #111;
            color: #fff;
            font-family: 'Segoe UI', system-ui, sans-serif;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        header {{
            text-align: center;
            padding: 15px;
            background: #1a1a1a;
            border-bottom: 1px solid #333;
        }}
        header h1 {{
            font-size: 20px;
            font-weight: 600;
            letter-spacing: 2px;
        }}
        header p {{
            color: #666;
            font-size: 12px;
            margin-top: 4px;
        }}
        .container {{
            display: flex;
            flex: 1;
            overflow: hidden;
        }}
        .camera {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #000;
            min-width: 0;
        }}
        .camera img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }}
        .transcript {{
            width: 350px;
            background: #1a1a1a;
            border-left: 1px solid #333;
            display: flex;
            flex-direction: column;
        }}
        .transcript-header {{
            padding: 12px 16px;
            border-bottom: 1px solid #333;
            font-size: 13px;
            color: #888;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .transcript-messages {{
            flex: 1;
            overflow-y: auto;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .msg {{
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.5;
            max-width: 90%;
            animation: fadeIn 0.3s ease;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(8px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .msg.user {{
            background: #2a2a3a;
            color: #aab;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }}
        .msg.ivar {{
            background: #1a3a2a;
            color: #adc;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
        }}
        .msg.system {{
            background: #2a2a2a;
            color: #666;
            align-self: center;
            font-size: 12px;
            font-style: italic;
        }}
        .msg .role {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
            opacity: 0.6;
        }}
        .listening {{
            text-align: center;
            padding: 8px;
            color: #4a8;
            font-size: 12px;
            animation: pulse 1.5s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 0.4; }}
            50% {{ opacity: 1; }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>IVAR</h1>
        <p>Knowit Management Consulting &middot; AI Agent CEO</p>
    </header>
    <div class="container">
        <div class="camera">
            <img src="/stream" alt="Camera Feed" />
        </div>
        <div class="transcript">
            <div class="transcript-header">Conversation</div>
            <div class="transcript-messages" id="messages">
                <div class="listening" id="listening">Listening...</div>
            </div>
        </div>
    </div>
    <script>
        let lastVersion = 0;
        const messagesDiv = document.getElementById('messages');
        const listeningDiv = document.getElementById('listening');

        async function pollTranscript() {{
            try {{
                const res = await fetch('/transcript?since=' + lastVersion);
                const data = await res.json();
                if (data.messages.length > 0) {{
                    for (const msg of data.messages) {{
                        const div = document.createElement('div');
                        div.className = 'msg ' + msg.role;
                        const roleLabel = msg.role === 'user' ? 'You' : msg.role === 'ivar' ? 'Ivar' : '';
                        div.innerHTML = (roleLabel ? '<div class="role">' + roleLabel + '</div>' : '') + msg.text;
                        messagesDiv.insertBefore(div, listeningDiv);
                    }}
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }}
                lastVersion = data.version;
            }} catch(e) {{}}
            setTimeout(pollTranscript, 500);
        }}
        pollTranscript();
    </script>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def _serve_stream(self):
        """Serve an MJPEG stream with object detection overlays."""
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.end_headers()

        try:
            while True:
                if _ivar_camera:
                    frame, _ = _ivar_camera.capture_frame_with_detections()
                elif _picam2:
                    frame = _picam2.capture_image("main")
                else:
                    break

                buffer = io.BytesIO()
                frame.save(buffer, format="JPEG", quality=JPEG_QUALITY)
                jpeg_bytes = buffer.getvalue()

                self.wfile.write(b"--frame\r\n")
                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                self.wfile.write(f"Content-Length: {len(jpeg_bytes)}\r\n\r\n".encode())
                self.wfile.write(jpeg_bytes)
                self.wfile.write(b"\r\n")

                time.sleep(0.1)  # ~10 fps
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _serve_transcript(self):
        """Serve transcript messages as JSON, with polling support."""
        # Parse ?since=N parameter
        since = 0
        if "?" in self.path:
            params = self.path.split("?")[1]
            for param in params.split("&"):
                if param.startswith("since="):
                    try:
                        since = int(param.split("=")[1])
                    except ValueError:
                        pass

        with _transcript_lock:
            current_version = _transcript_version
            total = len(_transcript)
            new_count = current_version - since
            if new_count > 0 and new_count <= total:
                messages = list(_transcript)[-new_count:]
            elif new_count > total:
                messages = list(_transcript)
            else:
                messages = []

        data = {"version": current_version, "messages": messages}
        body = json.dumps(data).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """Suppress default HTTP logging."""
        pass


def start_stream_server(camera=None, ivar_camera=None):
    """Start the stream server in a background thread.

    Args:
        camera: raw picamera2 instance (legacy, used if ivar_camera not provided)
        ivar_camera: IvarCamera instance with detection support (preferred)

    Returns the server.
    """
    global _ivar_camera, _picam2

    if ivar_camera is not None:
        _ivar_camera = ivar_camera
    elif camera is not None:
        _picam2 = camera
    elif CAMERA_AVAILABLE:
        _picam2 = Picamera2()
        config = _picam2.create_still_configuration(main={"size": CAMERA_RESOLUTION})
        _picam2.configure(config)
        _picam2.start()

    server = HTTPServer(("0.0.0.0", STREAM_PORT), StreamHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("Stream server started on port %d", STREAM_PORT)
    return server


def main():
    """Run the stream server standalone."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    if not CAMERA_AVAILABLE:
        print("Error: picamera2 not available. Run this on the Raspberry Pi.")
        return

    print(f"Starting Ivar camera stream...")
    print(f"Open http://ivar.local:{STREAM_PORT} in your browser")
    print("Press Ctrl+C to stop")
    print()

    # Try to use IvarCamera with detection
    try:
        from camera import IvarCamera
        ivar_cam = IvarCamera()
        server = start_stream_server(ivar_camera=ivar_cam)
    except Exception:
        camera = Picamera2()
        config = camera.create_still_configuration(main={"size": CAMERA_RESOLUTION})
        camera.configure(config)
        camera.start()
        server = start_stream_server(camera=camera)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping stream...")
        server.shutdown()


if __name__ == "__main__":
    main()
