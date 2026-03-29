from camera import IvarCamera, CAMERA_AVAILABLE
from brain import IvarBrain
from stream import start_stream_server
from config import STREAM_PORT, VOICE_MODE
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

    # Start live stream server
    stream_server = None
    if camera:
        try:
            stream_server = start_stream_server(camera.picam2)
            print(f"  Stream: http://ivar.local:{STREAM_PORT}")
        except Exception as e:
            print(f"  Stream: failed ({e})")

    # Initialize voice
    voice = None
    if VOICE_MODE:
        try:
            from voice import IvarVoice, VOICE_AVAILABLE
            if VOICE_AVAILABLE:
                voice = IvarVoice()
                print("  Voice: ready (say 'quit' to exit)")
            else:
                print("  Voice: no audio device found, falling back to text")
        except RuntimeError as e:
            print(f"  Voice: disabled ({e})")
        except ImportError as e:
            print(f"  Voice: missing dependencies ({e})")

    print(f"  Brain:  {brain.model}")
    print()

    if voice:
        _voice_loop(brain, camera, voice)
    else:
        _text_loop(brain, camera)

    if stream_server:
        stream_server.shutdown()
    if camera:
        camera.close()


def _voice_loop(brain, camera, voice):
    """Voice conversation loop: listen -> think -> speak."""
    print("Voice mode active. Speak to Ivar! (Ctrl+C to quit)\n")
    try:
        while True:
            print("[Listening...]")
            user_input = voice.listen()

            if not user_input:
                print("[No speech detected, try again]")
                continue

            print(f"You> {user_input}")

            command = user_input.lower().strip().rstrip(".")

            if command in ("quit", "exit", "stop"):
                print("Goodbye!")
                voice.speak("Goodbye!")
                break

            elif command == "reset":
                brain.reset_conversation()
                print("Ivar> Conversation cleared. Fresh start!")
                voice.speak("Conversation cleared. Fresh start!")

            else:
                if camera:
                    image_b64 = camera.capture_frame_base64()
                    response = brain.see_and_think(image_b64, user_input)
                else:
                    response = brain.think(user_input)
                print(f"Ivar> {response}")
                voice.speak(response)

            print()

    except KeyboardInterrupt:
        print("\nGoodbye!")


def _text_loop(brain, camera):
    """Original text REPL loop."""
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
                if camera:
                    print("[Capturing frame...]")
                    image_b64 = camera.capture_frame_base64()
                    response = brain.see_and_think(image_b64, user_input)
                else:
                    response = brain.think(user_input)
                print(f"Ivar> {response}")

            print()

    except KeyboardInterrupt:
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
