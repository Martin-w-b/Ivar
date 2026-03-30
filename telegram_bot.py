import asyncio
import base64
import logging
import threading

from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from brain import IvarBrain
from config import SYSTEM_PROMPT_CAMERA, SYSTEM_PROMPT_NO_CAMERA

logger = logging.getLogger(__name__)

# Try to import camera
try:
    from camera import IvarCamera, CAMERA_AVAILABLE
except ImportError:
    CAMERA_AVAILABLE = False


def _build_prompt(user_input, detections):
    if not detections:
        return user_input
    obj_list = ", ".join(
        f"{d['label']} ({d['confidence']:.0%})" for d in detections
    )
    return f"{user_input}\n\n[Objects detected in scene: {obj_list}]"


class IvarTelegramBot:
    """Telegram bot that runs in the background and can also receive messages."""

    def __init__(self, token: str, brain: IvarBrain, camera=None, chat_id=None):
        self.token = token
        self.brain = brain
        self.camera = camera
        self.chat_id = chat_id
        self._bot = Bot(token)
        self._loop = None
        self._thread = None

        self.app = Application.builder().token(token).build()
        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("reset", self._cmd_reset))
        self.app.add_handler(CommandHandler("look", self._cmd_look))
        self.app.add_handler(MessageHandler(filters.PHOTO, self._handle_photo))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text))

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._remember_chat(update)
        await update.message.reply_text(
            "Hey, I'm Ivar — CEO of all KMC AI agents. Send me a message or a photo."
        )

    async def _cmd_reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._remember_chat(update)
        self.brain.reset_conversation()
        await update.message.reply_text("Conversation cleared. Fresh start!")

    async def _cmd_look(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._remember_chat(update)
        if not self.camera:
            await update.message.reply_text("I can't see right now — no camera connected.")
            return

        image_b64, detections = self._capture()
        prompt = _build_prompt("Describe what you see.", detections)
        response = self.brain.see_and_think(image_b64, prompt)
        await update.message.reply_text(response)

    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._remember_chat(update)
        user_input = update.message.text.strip()
        if not user_input:
            return

        if self.camera:
            image_b64, detections = self._capture()
            prompt = _build_prompt(user_input, detections)
            response = self.brain.see_and_think(image_b64, prompt)
        else:
            response = self.brain.think(user_input)

        await update.message.reply_text(response)

    async def _handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._remember_chat(update)
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()
        image_b64 = base64.b64encode(photo_bytes).decode("utf-8")

        caption = update.message.caption or "What do you see in this photo?"
        response = self.brain.see_and_think(image_b64, caption)
        await update.message.reply_text(response)

    def _remember_chat(self, update: Update):
        """Auto-capture chat_id from incoming messages."""
        if not self.chat_id:
            self.chat_id = update.message.chat_id
            logger.info("Telegram chat_id set to %s", self.chat_id)

    def _capture(self):
        if self.camera and self.camera.detection_enabled:
            image_b64, detections = self.camera.capture_frame_base64_with_detections()
            return image_b64, detections
        if self.camera:
            return self.camera.capture_frame_base64(), []
        return None, []

    def send_message(self, text: str):
        """Send a message to the user from any thread (voice loop, text loop, etc.)."""
        if not self.chat_id:
            logger.warning("Cannot send Telegram message — no chat_id yet. "
                           "Send a message to the bot first.")
            return
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._bot.send_message(chat_id=self.chat_id, text=text),
                self._loop,
            )
        else:
            # Fallback: create a new event loop for sending
            asyncio.run(self._bot.send_message(chat_id=self.chat_id, text=text))

    def start_background(self):
        """Start the Telegram bot polling in a background thread."""
        self._thread = threading.Thread(target=self._run_polling, daemon=True)
        self._thread.start()
        logger.info("Telegram bot polling started in background")

    def _run_polling(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self.app.initialize())
        self._loop.run_until_complete(self.app.updater.start_polling())
        self._loop.run_until_complete(self.app.start())
        self._loop.run_forever()

    def run(self):
        """Start polling for Telegram messages (blocking)."""
        logger.info("Telegram bot starting...")
        self.app.run_polling()
