"""Quick debug script to check if IMX500 detection is working."""
from camera import IvarCamera
import time

cam = IvarCamera()
print("Waiting 5s for model warmup...")
time.sleep(5)

for i in range(10):
    md = cam.picam2.capture_metadata()
    try:
        out = cam.imx500.get_outputs(md, add_batch=True)
        if out is None:
            print(f"{i}: get_outputs returned None")
        else:
            print(f"{i}: shapes={[x.shape for x in out]}")
            boxes, scores, classes = out[0][0], out[1][0], out[2][0]
            above = sum(1 for s in scores if s > 0.3)
            print(f"   {above} detections above 0.3 threshold")
    except Exception as e:
        print(f"{i}: error: {e}")
    time.sleep(1)

cam.close()
