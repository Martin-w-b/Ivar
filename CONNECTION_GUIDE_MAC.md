# Connection Guide: Mac to Raspberry Pi

This guide covers connecting to your Raspberry Pi from a Mac. The workflow is very similar to Windows, with a few differences noted below.

## 1. Connecting on a New Network

If the Pi is not yet on your current Wi-Fi network, you can connect via a direct ethernet cable and configure Wi-Fi from there.

### Direct Ethernet Connection

1. Plug an ethernet cable directly between your Mac and the Pi (you may need a USB-C to Ethernet adapter)
2. Wait a moment, then check if the Pi is reachable:
   ```bash
   ping ivar.local
   ```
   macOS has built-in mDNS support, so this should resolve immediately.

   > **Note:** Use whatever hostname you configured during flashing (e.g. `ivar.local`), not the default `raspberrypi.local`.

3. SSH in:
   ```bash
   ssh <username>@ivar.local
   ```

Both devices will get link-local addresses (`169.254.x.x`) automatically — no router or DHCP needed.

### Configure Wi-Fi from the Pi

Once connected via ethernet and SSH, set up Wi-Fi so the Pi connects wirelessly on future boots.

**Simple WPA/WPA2 network:**

```bash
sudo nmcli dev wifi list
sudo nmcli dev wifi connect "<SSID>" password "<password>"
```

**WPA2-Enterprise network** (corporate networks with username/password login):

```bash
sudo nmcli connection add type wifi con-name "<connection-name>" ssid "<SSID>" wifi-sec.key-mgmt wpa-eap 802-1x.eap peap 802-1x.phase2-auth mschapv2 802-1x.identity "<your-username>" 802-1x.password '<your-password>'
sudo nmcli connection up "<connection-name>"
```

> **Important:** When the Pi switches to Wi-Fi, your ethernet SSH session will drop. This is expected — just reconnect: `ssh <username>@ivar.local`

The Wi-Fi connection is saved and the Pi will reconnect automatically on every boot.

### Reflashing the SD Card

If you can't connect to the Pi at all (forgot credentials, corrupted OS), reflash with Raspberry Pi Imager:

1. In the OS Customisation settings, set your username and hostname
2. Enable SSH — choose **"Allow public-key authentication only"** and paste your public key:
   ```bash
   # View your public key:
   cat ~/.ssh/id_ed25519.pub
   ```
   If you don't have a key yet, generate one: `ssh-keygen -t ed25519`
3. After flashing and booting, clear the old host key:
   ```bash
   ssh-keygen -R ivar.local
   ```
4. Connect: `ssh <username>@ivar.local`

## 2. SSH Config (One-Time Setup)

Open Terminal and edit your SSH config:

```bash
nano ~/.ssh/config
```

Add:

```
Host ivar
  HostName ivar.local
  User <your-pi-username>
```

Save with `Ctrl+X`, `Y`, `Enter`.

If the `~/.ssh` directory doesn't exist:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
```

## 3. Terminal SSH

macOS has SSH built in. Open Terminal (or iTerm2) and run:

```bash
ssh ivar
```

Or without the config shortcut:

```bash
ssh <username>@ivar.local
```

### Passwordless SSH (Recommended)

```bash
# Generate a key (skip if you already have one):
ssh-keygen -t ed25519

# Copy your key to the Pi:
ssh-copy-id ivar
```

After this, `ssh ivar` connects without a password.

> **Note:** `ssh-copy-id` is not installed by default on older macOS versions. Install it with Homebrew: `brew install ssh-copy-id`

## 4. VS Code Remote SSH

### Install VS Code

If you don't have it yet, download from https://code.visualstudio.com/ or install with Homebrew:

```bash
brew install --cask visual-studio-code
```

### Install the Extension

1. Open VS Code
2. Go to Extensions (`Cmd+Shift+X`)
3. Search for **"Remote - SSH"** (by Microsoft)
4. Click **Install**

### Connect to the Pi

1. Press `Cmd+Shift+P` to open the Command Palette
2. Type **"Remote-SSH: Connect to Host"** and select it
3. Choose **ivar** (from your SSH config) or type `<username>@ivar.local`
4. Select **Linux** when asked about the platform
5. Enter your password if prompted

### Open the Project

1. Once connected, click **Open Folder** in the sidebar
2. Type `/home/<your-username>/ivar` and click OK
3. You now have full access to all project files

### Using the Terminal

- Open a terminal with `` Ctrl+` `` (yes, `Ctrl` not `Cmd` — this is a VS Code shortcut)
- This terminal runs **on the Pi**, not your Mac
- Use multiple terminals (click `+`):
  - One for running Ivar: `source venv/bin/activate && python main.py`
  - One for editing, git, or Claude Code

### Viewing Images

Photos saved by Ivar's `snap` command go to the `captures/` folder. Click any `.jpg` in VS Code's file explorer to view it.

## 5. Running Ivar

From any terminal connected to the Pi:

```bash
cd ~/ivar
source venv/bin/activate
python main.py
```

## 6. Development Workflow

### Option A: Edit on Pi via VS Code Remote SSH (Recommended)

1. Connect VS Code to the Pi
2. Edit files directly — saved on the Pi instantly
3. Restart Ivar in the terminal to see changes

### Option B: Edit on Mac, Push via Git

```bash
# On your Mac:
git add . && git commit -m "update" && git push

# On the Pi (via SSH or VS Code terminal):
cd ~/ivar && git pull && python main.py
```

## Key Differences from Windows

| Action | Windows | Mac |
|---|---|---|
| SSH config location | `C:\Users\<you>\.ssh\config` | `~/.ssh/config` |
| Open terminal | PowerShell / CMD | Terminal.app / iTerm2 |
| VS Code Command Palette | `Ctrl+Shift+P` | `Cmd+Shift+P` |
| VS Code Extensions | `Ctrl+Shift+X` | `Cmd+Shift+X` |
| VS Code integrated terminal | `` Ctrl+` `` | `` Ctrl+` `` (same) |
| mDNS (`.local` discovery) | Requires Bonjour (usually pre-installed) | Built-in, works out of the box |

> **Note:** macOS has built-in mDNS support, so `ivar.local` should resolve immediately without any extra software. On Windows, this depends on Bonjour being installed (it comes with iTunes or can be installed separately).

## 7. Bluetooth Speaker/Mic Setup

To enable voice mode, pair a Bluetooth speaker/mic with the Pi.

### Install Bluetooth Packages

```bash
sudo apt install -y bluez pulseaudio-module-bluetooth
```

### Pair Your Device

Put your Bluetooth speaker/mic into pairing mode, then on the Pi (via SSH):

```bash
bluetoothctl
```

Inside the `bluetoothctl` prompt:

```
power on
agent on
default-agent
scan on
```

Wait for your device to appear, note its MAC address (e.g. `AA:BB:CC:DD:EE:FF`), then:

```
pair AA:BB:CC:DD:EE:FF
trust AA:BB:CC:DD:EE:FF
connect AA:BB:CC:DD:EE:FF
quit
```

### Verify Audio

```bash
# Check that the Bluetooth speaker and mic are recognized
pactl list sinks short     # should show a bluetooth sink
pactl list sources short   # should show a bluetooth source

# Set as default
pactl set-default-sink <bluetooth-sink-name>
pactl set-default-source <bluetooth-source-name>

# Test: record 3 seconds, then play back
arecord -d 3 test.wav && aplay test.wav
```

The device will auto-reconnect on future boots (since we used `trust`).

### Run Ivar in Voice Mode

With the Bluetooth device connected and `OPENAI_API_KEY` set in `.env`:

```bash
cd ~/ivar
source venv/bin/activate
python main.py
```

Ivar will detect the audio device and start in voice mode automatically. To disable voice mode, set `VOICE_MODE=false` in `.env`.

## Troubleshooting

### Can't find the Pi

```bash
ping ivar.local
```

If this fails:
- Make sure the Pi is powered on and on the same Wi-Fi network
- Check your router's admin page for the Pi's IP address
- Try: `dns-sd -B _ssh._tcp` to browse for SSH services on the network

### "Remote host identification has changed"

```bash
ssh-keygen -R ivar.local
```

Then try connecting again.

### Ethernet adapter not detecting the Pi

- Make sure the Pi is powered on and the cable is plugged in on both ends
- Try a different cable or USB-C adapter
- Check System Settings → Network — the ethernet interface should show "Connected" or "Self-Assigned IP"

### "Permission denied" on SSH

- Double-check your username and password
- If using public key auth, verify your key was added during flashing
- If you forgot the password, re-flash the SD card

### VS Code can't connect

- Verify SSH works first: `ssh ivar`
- Make sure the Remote-SSH extension is installed
- Reload VS Code: `Cmd+Shift+P` → "Reload Window"
