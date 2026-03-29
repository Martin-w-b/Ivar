"""
Live camera stream for Ivar.

Run this to start a web server that streams the camera feed
with real-time object detection overlays.
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
_ivar_camera = None
_picam2 = None


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
    <p>Live Camera Feed (with object detection)</p>
    <img src="/stream" alt="Camera Feed" />
    <p class="info">Resolution: {CAMERA_RESOLUTION[0]}x{CAMERA_RESOLUTION[1]}</p>
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
