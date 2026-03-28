# Ivar

A Raspberry Pi 5 vision robot that uses the Pi AI Camera to see and Claude API to think.

## Hardware

- Raspberry Pi 5 (8GB RAM)
- 64GB SD card with Raspberry Pi OS Bookworm (64-bit)
- Raspberry Pi AI Camera (Sony IMX500)

## Setup

### 1. Flash the SD card

Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash **Raspberry Pi OS (64-bit, Bookworm)**.

In the imager settings (gear icon), configure:
- **Enable SSH** (use password authentication)
- **Set username and password** (e.g., `pi` / your password)
- **Configure Wi-Fi** (your network SSID and password)
- **Set hostname** (e.g., `ivar`)

### 2. Connect the AI Camera

Connect the Pi AI Camera to the CSI port on the Pi 5. Make sure the ribbon cable is firmly seated with the contacts facing the right direction.

### 3. SSH into the Pi

From your PC:

```bash
# Find your Pi (use the hostname you set, or check your router)
ssh pi@ivar.local

# For passwordless SSH (recommended):
ssh-copy-id pi@ivar.local
```

### 4. Clone and set up

On the Pi:

```bash
cd ~
git clone <your-repo-url> ivar
cd ivar
bash setup.sh
```

### 5. Add your API key

Edit `~/.env` (or `~/ivar/.env`) and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

### 6. Reboot and run

```bash
sudo reboot

# After reboot:
cd ~/ivar
source venv/bin/activate
python main.py
```

## Development Workflow

Edit code on your PC, push to Git, then pull and run on the Pi:

```bash
# On your PC:
git add . && git commit -m "update feature" && git push

# On the Pi (via SSH):
cd ~/ivar && git pull && source venv/bin/activate && python main.py
```

**Tip:** Use the [VS Code Remote-SSH extension](https://code.visualstudio.com/docs/remote/ssh) to edit files on the Pi directly from VS Code on your PC.

## Usage

```
  ╔══════════════════════════════════════╗
  ║            === IVAR ===               ║
  ║   Your AI-powered vision robot        ║
  ║                                       ║
  ║   Commands:                           ║
  ║     look  - describe what I see        ║
  ║     snap  - save a photo              ║
  ║     reset - clear conversation        ║
  ║     help  - show this message         ║
  ║     quit  - exit                      ║
  ║                                       ║
  ║   Or just type a question!            ║
  ╚══════════════════════════════════════╝

You> look
[Capturing frame...]
Ivar> I can see a desk with a laptop, a coffee mug, and some electronics.

You> what color is the mug?
[Capturing frame...]
Ivar> The mug appears to be dark blue with a white logo on it.
```

## Project Structure

```
ivar/
├── main.py           # Terminal REPL entry point
├── camera.py         # Pi AI Camera wrapper (picamera2)
├── brain.py          # Claude API vision integration
├── config.py         # Configuration (loads .env)
├── utils.py          # Helpers (logging, frame saving)
├── setup.sh          # Pi setup script
├── requirements.txt  # Python dependencies
├── .env.example      # API key template
└── .gitignore
```

## Cost

Using `claude-haiku-4-5` (default): ~$0.003 per interaction. A session of 100 interactions costs roughly $0.30.

You can switch to a more capable model by setting `MODEL=claude-sonnet-4-6-20250514` in your `.env` file.
