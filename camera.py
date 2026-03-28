import io
import base64
import logging

from config import CAMERA_RESOLUTION, JPEG_QUALITY

logger = logging.getLogger(__name__)

try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False
    logger.warning("picamera2 not available — camera features disabled")


class IvarCamera:
    """Wrapper around the Raspberry Pi AI Camera (IMX500) via picamera2."""

    def __init__(self):
        if not CAMERA_AVAILABLE:
            raise RuntimeError(
                "picamera2 is not installed. Run this on a Raspberry Pi "
                "with picamera2 installed, or use setup.sh to install it."
            )

        self.picam2 = Picamera2()
        config = self.picam2.create_still_configuration(
            main={"size": CAMERA_RESOLUTION}
        )
        self.picam2.configure(config)
        self.picam2.start()
        logger.info("Camera initialized at %s", CAMERA_RESOLUTION)

    def capture_frame(self):
        """Capture a single frame and return as a PIL Image."""
        return self.picam2.capture_image("main")

    def capture_frame_base64(self) -> str:
        """Capture a frame and return as a base64-encoded JPEG string."""
        frame = self.capture_frame()
        buffer = io.BytesIO()
        frame.save(buffer, format="JPEG", quality=JPEG_QUALITY)
        encoded = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")
        logger.info("Captured frame: %d bytes encoded", len(encoded))
        return encoded

    def close(self):
        """Release camera resources."""
        if hasattr(self, "picam2"):
            self.picam2.stop()
            self.picam2.close()
            logger.info("Camera closed")
