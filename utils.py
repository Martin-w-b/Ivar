import os
import logging
from datetime import datetime

from config import CAPTURE_DIR


def setup_logging():
    """Configure logging for Ivar."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def save_frame(image, directory=None) -> str:
    """Save a PIL Image to disk with a timestamp filename. Returns the path."""
    directory = directory or CAPTURE_DIR
    os.makedirs(directory, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(directory, f"ivar_{timestamp}.jpg")
    image.save(path, format="JPEG", quality=90)
    return path


def print_banner(has_camera=True):
    """Print the Ivar welcome banner."""
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║            === IVAR ===               ║")
    if has_camera:
        print("  ║   Your AI-powered vision robot        ║")
    else:
        print("  ║   Your AI-powered assistant            ║")
    print("  ║                                       ║")
    print("  ║   Commands:                           ║")
    if has_camera:
        print("  ║     look  - describe what I see        ║")
        print("  ║     snap  - save a photo              ║")
    print("  ║     reset - clear conversation        ║")
    print("  ║     help  - show this message         ║")
    print("  ║     quit  - exit                      ║")
    print("  ║                                       ║")
    print("  ║   Or just type/say a question!        ║")
    print("  ╚══════════════════════════════════════╝")
    print()
