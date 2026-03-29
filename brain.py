import logging

import anthropic

from config import ANTHROPIC_API_KEY, MODEL, MAX_TOKENS, SYSTEM_PROMPT_CAMERA, MAX_HISTORY_TURNS

logger = logging.getLogger(__name__)


class IvarBrain:
    """Claude API integration for Ivar's vision and conversation."""

    def __init__(self, system_prompt=None):
        if not ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Copy .env.example to .env "
                "and add your API key."
            )

        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = MODEL
        self.max_tokens = MAX_TOKENS
        self.system_prompt = system_prompt or SYSTEM_PROMPT_CAMERA
        self.conversation_history = []
        logger.info("Brain initialized with model %s", self.model)

    def see_and_think(self, image_base64: str, prompt: str) -> str:
        """Send an image + text prompt to Claude and return the response."""
        message = {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_base64,
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }
        self.conversation_history.append(message)
        self._trim_history()

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            messages=self.conversation_history,
        )

        assistant_text = response.content[0].text
        self.conversation_history.append(
            {"role": "assistant", "content": assistant_text}
        )
        return assistant_text

    def think(self, prompt: str) -> str:
        """Text-only query — no image."""
        self.conversation_history.append({"role": "user", "content": prompt})
        self._trim_history()

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            messages=self.conversation_history,
        )

        assistant_text = response.content[0].text
        self.conversation_history.append(
            {"role": "assistant", "content": assistant_text}
        )
        return assistant_text

    def reset_conversation(self):
        """Clear conversation history."""
        self.conversation_history.clear()
        logger.info("Conversation history cleared")

    def _trim_history(self):
        """Keep history within limits. Strip images from older turns."""
        max_messages = MAX_HISTORY_TURNS * 2  # user + assistant per turn

        if len(self.conversation_history) <= max_messages:
            return

        # Strip image data from older messages to save tokens
        cutoff = len(self.conversation_history) - max_messages
        for i in range(cutoff):
            msg = self.conversation_history[i]
            if isinstance(msg.get("content"), list):
                # Replace image+text content with just the text
                texts = [
                    block["text"]
                    for block in msg["content"]
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                if texts:
                    self.conversation_history[i] = {
                        "role": msg["role"],
                        "content": " ".join(texts),
                    }

        # Drop the oldest turns if history is way too long
        if len(self.conversation_history) > max_messages * 2:
            self.conversation_history = self.conversation_history[-max_messages:]
