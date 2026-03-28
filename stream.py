"""
Live camera stream for Ivar.

Run this to start a web server that streams the camera feed.
Open http://ivar.local:8080 in any browser to watch.
"""

import io
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

from config import CAMERA_RESOLUTION, JPEG_QUALITY, STREAM_PORT

logger = logging.getLogger(__name__)

try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False

# Global reference to the camera for the request handler
_camera = None


class StreamHandler(BaseHTTPRequestHandler):
    """HTTP handler that serves an MJPEG stream and a simple viewer page."""

    def do_GET(self):
        if self.path == "/":
            self._serve_page()
        elif self.path == "/stream":
            self._serve_stream()
        else:
            self.send_error(404)

    def _serve_page(self):
        """Serve a simple HTML page with the camera feed."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Ivar - Live Camera</title>
    <style>
        body {{
            background: #1a1a1a;
            color: #fff;
            font-family: monospace;
            display: flex;
            flex-direction: column;
            align-items: center;
            margin: 0;
            padding: 20px;
        }}
        h1 {{ margin-bottom: 10px; }}
        img {{
            max-width: 100%;
            border: 2px solid #333;
            border-radius: 8px;
        }}
        .info {{
            color: #888;
            margin-top: 10px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <h1>=== IVAR ===</h1>
    <p>Live Camera Feed</p>
    <img src="/stream" alt="Camera Feed" />
    <p class="info">Resolution: {CAMERA_RESOLUTION[0]}x{CAMERA_RESOLUTION[1]}</p>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def _serve_stream(self):
        """Serve an MJPEG stream."""
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.end_headers()

        try:
            while True:
                frame = _camera.capture_image("main")
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

    def log_message(self, format, *args):
        """Suppress default HTTP logging."""
        pass


def start_stream_server(camera=None):
    """Start the stream server in a background thread. Returns the server."""
    global _camera

    if camera is not None:
        _camera = camera
    elif CAMERA_AVAILABLE:
        _camera = Picamera2()
        config = _camera.create_still_configuration(main={"size": CAMERA_RESOLUTION})
        _camera.configure(config)
        _camera.start()

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

    camera = Picamera2()
    config = camera.create_still_configuration(main={"size": CAMERA_RESOLUTION})
    camera.configure(config)
    camera.start()

    server = start_stream_server(camera)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping stream...")
        server.shutdown()
        camera.stop()
        camera.close()


if __name__ == "__main__":
    main()
