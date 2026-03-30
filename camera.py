import io
import base64
import logging

import numpy as np
from PIL import ImageDraw
from config import CAMERA_RESOLUTION, JPEG_QUALITY

logger = logging.getLogger(__name__)

CAMERA_AVAILABLE = False
IMX500_AVAILABLE = False

try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
except ImportError:
    logger.warning("picamera2 not available — camera features disabled")

try:
    from picamera2.devices.imx500 import IMX500, NetworkIntrinsics
    IMX500_AVAILABLE = True
except ImportError:
    logger.warning("IMX500 module not available — object detection disabled")

# Default object detection model and labels
DETECTION_MODEL = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"
DETECTION_THRESHOLD = 0.55

COCO_LABELS = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train",
    "truck", "boat", "traffic light", "fire hydrant", "stop sign",
    "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep",
    "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
    "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard",
    "sports ball", "kite", "baseball bat", "baseball glove", "skateboard",
    "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork",
    "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv",
    "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave",
    "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase",
    "scissors", "teddy bear", "hair drier", "toothbrush",
]


class IvarCamera:
    """Wrapper around the Raspberry Pi AI Camera (IMX500) via picamera2."""

    def __init__(self):
        if not CAMERA_AVAILABLE:
            raise RuntimeError(
                "picamera2 is not installed. Run this on a Raspberry Pi "
                "with picamera2 installed, or use setup.sh to install it."
            )

        self.imx500 = None
        self.intrinsics = None
        self.detection_enabled = False

        # Load object detection model if available
        if IMX500_AVAILABLE:
            try:
                self.imx500 = IMX500(DETECTION_MODEL)
                self.intrinsics = self.imx500.network_intrinsics
                if not self.intrinsics:
                    self.intrinsics = NetworkIntrinsics()
                self.detection_enabled = True
                logger.info("Object detection model loaded")
            except Exception as e:
                logger.warning("Could not load detection model: %s", e)

        self.picam2 = Picamera2()
        config = self.picam2.create_still_configuration(
            main={"size": CAMERA_RESOLUTION}
        )
        self.picam2.configure(config)
        self.picam2.start()
        logger.info("Camera initialized at %s (detection: %s)",
                     CAMERA_RESOLUTION, self.detection_enabled)

    def capture_frame(self):
        """Capture a single frame and return as a PIL Image."""
        return self.picam2.capture_image("main")

    def capture_frame_and_metadata(self):
        """Capture a frame and its metadata together.

        Returns (PIL Image, metadata dict) from the same capture request,
        ensuring detection results correspond to the returned frame.
        """
        request = self.picam2.capture_request()
        try:
            metadata = request.get_metadata()
            frame = request.make_image("main")
        finally:
            request.release()
        return frame, metadata

    def detect_objects(self, metadata=None):
        """Run object detection and return list of detected objects."""
        if not self.detection_enabled:
            return []

        if metadata is None:
            metadata = self.picam2.capture_metadata()

        try:
            np_outputs = self.imx500.get_outputs(metadata, add_batch=True)
        except Exception:
            return []

        if np_outputs is None:
            return []

        input_w, input_h = self.imx500.get_input_size()
        boxes, scores, classes = np_outputs[0][0], np_outputs[1][0], np_outputs[2][0]

        # Normalize boxes if needed
        bbox_normalization = getattr(self.intrinsics, 'bbox_normalization', False)
        bbox_order = getattr(self.intrinsics, 'bbox_order', '')

        if bbox_normalization:
            boxes = boxes / input_h

        if bbox_order == "xy":
            boxes = boxes[:, [1, 0, 3, 2]]

        detections = []
        for i in range(len(scores)):
            if scores[i] < DETECTION_THRESHOLD:
                continue
            class_idx = int(classes[i])
            label = COCO_LABELS[class_idx] if class_idx < len(COCO_LABELS) else f"class_{class_idx}"

            # Convert from inference coords to image coords
            box = boxes[i]
            coords = self.imx500.convert_inference_coords(
                tuple(box), metadata, self.picam2
            )

            detections.append({
                "label": label,
                "confidence": float(scores[i]),
                "bbox": coords,  # (x, y, w, h) in image space
            })

        logger.info("Detected %d objects", len(detections))
        return detections

    def capture_frame_with_detections(self):
        """Capture a frame, run detection, and annotate the image.

        Returns (annotated PIL Image, list of detections).
        Uses synchronized frame+metadata to ensure boxes match the frame.
        """
        if self.detection_enabled:
            frame, metadata = self.capture_frame_and_metadata()
            detections = self.detect_objects(metadata)
        else:
            frame = self.capture_frame()
            detections = []

        if detections:
            draw = ImageDraw.Draw(frame)
            for det in detections:
                x, y, w, h = det["bbox"]
                label = f"{det['label']} {det['confidence']:.0%}"
                draw.rectangle([x, y, x + w, y + h], outline="lime", width=3)
                # Draw label background
                text_bbox = draw.textbbox((x, y - 15), label)
                draw.rectangle(text_bbox, fill="lime")
                draw.text((x, y - 15), label, fill="black")

        return frame, detections

    def capture_frame_base64(self) -> str:
        """Capture a frame and return as a base64-encoded JPEG string."""
        frame = self.capture_frame()
        buffer = io.BytesIO()
        frame.save(buffer, format="JPEG", quality=JPEG_QUALITY)
        encoded = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")
        logger.info("Captured frame: %d bytes encoded", len(encoded))
        return encoded

    def capture_frame_base64_with_detections(self) -> tuple[str, list]:
        """Capture a frame with detection annotations, return (base64 JPEG, detections)."""
        frame, detections = self.capture_frame_with_detections()
        buffer = io.BytesIO()
        frame.save(buffer, format="JPEG", quality=JPEG_QUALITY)
        encoded = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")
        return encoded, detections

    def close(self):
        """Release camera resources."""
        if hasattr(self, "picam2"):
            self.picam2.stop()
            self.picam2.close()
            logger.info("Camera closed")
