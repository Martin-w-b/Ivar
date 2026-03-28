from camera import IvarCamera, CAMERA_AVAILABLE
from brain import IvarBrain
from utils import setup_logging, save_frame, print_banner


def main():
    setup_logging()
    print_banner()

    # Initialize brain (Claude API)
    try:
        brain = IvarBrain()
    except RuntimeError as e:
        print(f"Error: {e}")
        return

    # Initialize camera
    camera = None
    if CAMERA_AVAILABLE:
        try:
            camera = IvarCamera()
            print("  Camera: ready")
        except Exception as e:
            print(f"  Camera: unavailable ({e})")
    else:
        print("  Camera: not available (not on Raspberry Pi?)")

    print(f"  Brain:  {brain.model}")
    print()

    try:
        while True:
            try:
                user_input = input("You> ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            command = user_input.lower()

            if command in ("quit", "exit"):
                print("Goodbye!")
                break

            elif command == "help":
                print_banner()

            elif command == "reset":
                brain.reset_conversation()
                print("Ivar> Conversation cleared. Fresh start!")

            elif command == "snap":
                if not camera:
                    print("Ivar> I can't take photos without a camera.")
                    continue
                frame = camera.capture_frame()
                path = save_frame(frame)
                print(f"Ivar> Photo saved to {path}")

            elif command == "look":
                if not camera:
                    print("Ivar> I can't see without a camera.")
                    continue
                print("[Capturing frame...]")
                image_b64 = camera.capture_frame_base64()
                response = brain.see_and_think(
                    image_b64, "Describe what you see."
                )
                print(f"Ivar> {response}")

            else:
                # Any other input: capture frame + ask question
                if camera:
                    print("[Capturing frame...]")
                    image_b64 = camera.capture_frame_base64()
                    response = brain.see_and_think(image_b64, user_input)
                else:
                    # No camera — text-only conversation
                    response = brain.think(user_input)
                print(f"Ivar> {response}")

            print()

    except KeyboardInterrupt:
        print("\nGoodbye!")
    finally:
        if camera:
            camera.close()


if __name__ == "__main__":
    main()
