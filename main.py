from camera import IvarCamera, CAMERA_AVAILABLE
from brain import IvarBrain
from stream import start_stream_server, update_transcript, update_status
from config import STREAM_PORT, VOICE_MODE, SYSTEM_PROMPT_CAMERA, SYSTEM_PROMPT_NO_CAMERA
from utils import setup_logging, save_frame, print_banner


def main():
    setup_logging()

    # Initialize camera
    camera = None
    if CAMERA_AVAILABLE:
        try:
            camera = IvarCamera()
        except Exception:
            pass

    print_banner(has_camera=camera is not None)

    if camera:
        if camera.detection_enabled:
            print("  Camera: ready (object detection on)")
        else:
            print("  Camera: ready")
    else:
        print("  Camera: off")

    # Initialize brain (Claude API) with appropriate prompt
    system_prompt = SYSTEM_PROMPT_CAMERA if camera else SYSTEM_PROMPT_NO_CAMERA
    try:
        brain = IvarBrain(system_prompt=system_prompt)
    except RuntimeError as e:
        print(f"Error: {e}")
        return

    # Start live stream server
    stream_server = None
    if camera:
        try:
            stream_server = start_stream_server(ivar_camera=camera)
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
        except Exception as e:
            print(f"  Voice: unavailable ({e})")

    print(f"  Brain:  {brain.model}")
    print()

    try:
        if voice:
            _voice_loop(brain, camera, voice)
        else:
            _text_loop(brain, camera)
    except KeyboardInterrupt:
        print("\nGoodbye!")

    if stream_server:
        stream_server.shutdown()
    if camera:
        camera.close()


def _build_prompt(user_input, detections):
    """Add object detection results to the user prompt."""
    if not detections:
        return user_input
    obj_list = ", ".join(
        f"{d['label']} ({d['confidence']:.0%})" for d in detections
    )
    return f"{user_input}\n\n[Objects detected in scene: {obj_list}]"


def _capture_with_detections(camera):
    """Capture frame with detections if available, else plain capture."""
    if camera.detection_enabled:
        image_b64, detections = camera.capture_frame_base64_with_detections()
        if detections:
            print(f"  [Detected: {', '.join(d['label'] for d in detections)}]")
        return image_b64, detections
    return camera.capture_frame_base64(), []


def _voice_loop(brain, camera, voice):
    """Voice conversation loop: listen -> think -> speak."""
    print("Voice mode active. Speak to Ivar! (Ctrl+C to restart)\n")
    while True:
        print("[Listening...]")
        update_status("Listening...")
        user_input = voice.listen()

        if not user_input:
            print("[No speech detected, try again]")
            continue

        print(f"You> {user_input}")
        update_transcript("user", user_input)
        update_status(f"You: {user_input}")

        command = user_input.lower().strip().rstrip(".")

        if command in ("quit", "exit", "stop"):
            print("Goodbye!")
            voice.speak("Goodbye!")
            update_transcript("ivar", "Goodbye!")
            return

        elif command == "reset":
            brain.reset_conversation()
            print("Ivar> Conversation cleared. Fresh start!")
            voice.speak("Conversation cleared. Fresh start!")
            update_transcript("ivar", "Conversation cleared. Fresh start!")

        else:
            if camera:
                image_b64, detections = _capture_with_detections(camera)
                prompt = _build_prompt(user_input, detections)
                sentences = brain.see_and_think_stream(image_b64, prompt)
            else:
                sentences = brain.think_stream(user_input)

            # Speak each sentence as it arrives from the stream
            full_response = []
            for sentence in sentences:
                full_response.append(sentence)
                print(f"Ivar> {sentence}")
                voice.speak(sentence)

            response = " ".join(full_response)
            update_transcript("ivar", response)
            update_status(f"Ivar: {response}")

        print()


def _text_loop(brain, camera):
    """Original text REPL loop."""
    while True:
        try:
            user_input = input("You> ").strip()
        except EOFError:
            return

        if not user_input:
            continue

        command = user_input.lower()

        if command in ("quit", "exit"):
            print("Goodbye!")
            return

        elif command == "help":
            print_banner(has_camera=camera is not None)

        elif command == "reset":
            brain.reset_conversation()
            print("Ivar> Conversation cleared. Fresh start!")
            update_transcript("ivar", "Conversation cleared. Fresh start!")

        elif command == "snap":
            if not camera:
                print("Ivar> I can't take photos without a camera.")
                continue
            frame, detections = camera.capture_frame_with_detections()
            path = save_frame(frame)
            if detections:
                print(f"  [Detected: {', '.join(d['label'] for d in detections)}]")
            print(f"Ivar> Photo saved to {path}")

        elif command == "look":
            if not camera:
                print("Ivar> I can't see without a camera.")
                continue
            print("[Capturing frame...]")
            image_b64, detections = _capture_with_detections(camera)
            prompt = _build_prompt("Describe what you see.", detections)
            response = brain.see_and_think(image_b64, prompt)
            print(f"Ivar> {response}")
            update_transcript("ivar", response)

        else:
            update_transcript("user", user_input)
            if camera:
                print("[Capturing frame...]")
                image_b64, detections = _capture_with_detections(camera)
                prompt = _build_prompt(user_input, detections)
                response = brain.see_and_think(image_b64, prompt)
            else:
                response = brain.think(user_input)
            print(f"Ivar> {response}")
            update_transcript("ivar", response)

        print()


if __name__ == "__main__":
    main()
