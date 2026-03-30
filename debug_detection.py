"""Quick debug script to check if IMX500 detection is working."""
from picamera2 import Picamera2
from picamera2.devices.imx500 import IMX500
import time

MODEL = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"

imx500 = IMX500(MODEL)
picam2 = Picamera2(imx500.camera_num)

# Use preview config for continuous streaming (needed for IMX500 inference)
config = picam2.create_preview_configuration(main={"size": (1280, 720)})
picam2.configure(config)
picam2.start()

print("Camera started. Waiting 10s for firmware upload + warmup...")
time.sleep(10)

for i in range(10):
    md = picam2.capture_metadata()
    has_tensor = "CnnOutputTensor" in md
    print(f"{i}: CnnOutputTensor present={has_tensor}")
    if has_tensor:
        out = imx500.get_outputs(md, add_batch=True)
        if out is not None:
            print(f"   shapes={[x.shape for x in out]}")
            scores = out[1][0]
            above = sum(1 for s in scores if s > 0.3)
            print(f"   {above} detections above 0.3 threshold")
    time.sleep(1)

picam2.stop()
picam2.close()
