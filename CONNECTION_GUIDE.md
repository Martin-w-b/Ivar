# Connection Guide: Developing on the Pi from Your PC

This guide covers how to connect to your Raspberry Pi from your PC for development.

## Prerequisites

- Raspberry Pi is powered on and connected to the same network as your PC
- SSH is enabled on the Pi (configured during SD card flashing)
- You know your Pi's username, password, and hostname

## 1. Connecting on a New Network

If the Pi is not yet on your current Wi-Fi network, you can connect via a direct ethernet cable and configure Wi-Fi from there.

### Direct Ethernet Connection

1. Plug an ethernet cable directly between your PC and the Pi
2. Wait a moment, then check the adapter status in PowerShell:
   ```powershell
   Get-NetAdapter
   ```
   The Ethernet adapter should show **Status: Up**. If it shows "Disconnected", try a different cable or check that the Pi is powered on.

3. Try to reach the Pi:
   ```bash
   ping ivar.local
   ```
   > **Note:** `ping raspberrypi.local` won't work if you set a custom hostname during flashing. Use whatever hostname you configured (e.g. `ivar.local`).

4. SSH in:
   ```bash
   ssh <username>@ivar.local
   ```

Both devices will get link-local addresses (`169.254.x.x`) automatically — no router or DHCP needed.

> **Note:** On corporate networks, IT may disable the ethernet port via group policy. If `Get-NetAdapter` shows the adapter as "Disabled" or "Not Present", check with your IT department.

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
   # View your public key on your PC:
   cat ~/.ssh/id_ed25519.pub
   ```
   If you don't have a key yet, generate one: `ssh-keygen -t ed25519`
3. After flashing and booting, clear the old host key:
   ```bash
   ssh-keygen -R ivar.local
   ```
4. Connect: `ssh <username>@ivar.local`

## 2. SSH Config (One-Time Setup)

Create or edit `~/.ssh/config` on your PC (Windows: `C:\Users\<you>\.ssh\config`):

```
Host ivar
  HostName ivar.local
  User <your-pi-username>
```

This lets you type `ssh ivar` instead of the full address every time.

## 3. Terminal SSH

The simplest way to connect:

```bash
ssh ivar
```

Or without the config shortcut:

```bash
ssh <username>@ivar.local
```

Enter your password when prompted.

### Passwordless SSH (Recommended)

Generate a key and copy it to the Pi so you don't have to type your password every time:

```bash
# On your PC (skip if you already have a key):
ssh-keygen -t ed25519

# Copy your key to the Pi:
ssh-copy-id ivar
```

After this, `ssh ivar` will connect without asking for a password.

## 4. VS Code Remote SSH

This is the recommended way to develop. You get full code editing, file browsing, and a terminal — all on the Pi, but from your PC's VS Code.

### Install the Extension

1. Open VS Code on your PC
2. Go to Extensions (`Ctrl+Shift+X`)
3. Search for **"Remote - SSH"** (by Microsoft)
4. Click **Install**

### Connect to the Pi

1. Press `Ctrl+Shift+P` to open the Command Palette
2. Type **"Remote-SSH: Connect to Host"** and select it
3. Choose **ivar** (from your SSH config) or type `<username>@ivar.local`
4. Select **Linux** when asked about the platform
5. Enter your password if prompted

### Open the Project

1. Once connected, click **Open Folder** in the sidebar
2. Type `/home/<your-username>/ivar` and click OK
3. You now have full access to all project files

### Using the Terminal

- Open a terminal with `` Ctrl+` `` — this runs **on the Pi**, not your PC
- You can have multiple terminals open (click the `+` icon):
  - One for running Ivar: `source venv/bin/activate && python main.py`
  - One for editing, git commands, or running Claude Code

### Viewing Images

When Ivar saves a photo (via the `snap` command), it goes to the `captures/` folder. You can click on any `.jpg` file in VS Code's file explorer to view it directly.

## 5. Running Ivar

From any terminal connected to the Pi (SSH or VS Code terminal):

```bash
cd ~/ivar
source venv/bin/activate
python main.py
```

## 6. Development Workflow

### Option A: Edit on Pi via VS Code Remote SSH (Recommended)

1. Connect VS Code to the Pi (see above)
2. Edit files directly — they're saved on the Pi instantly
3. Restart Ivar in the terminal to see changes

### Option B: Edit on PC, Push via Git

1. Edit code on your PC in the local repo
2. Commit and push:
   ```bash
   git add . && git commit -m "update" && git push
   ```
3. On the Pi (via SSH or VS Code terminal), pull and run:
   ```bash
   cd ~/ivar && git pull && python main.py
   ```

## 7. Bluetooth Speaker/Mic Setup

To enable voice mode, pair a Bluetooth speaker/mic with the Pi.

### Install Bluetooth Packages

```bash
sudo apt install -y bluez pulseaudio-module-bluetooth
```

### Pair Your Device

Put your Bluetooth speaker/mic into pairing mode, then on the Pi:

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
- Make sure the Pi is powered on and connected to Wi-Fi
- Check your router's admin page for the Pi's IP address
- Try pinging the IP directly: `ping 192.168.x.x`

### "Remote host identification has changed"

This happens if you re-flashed the SD card. Remove the old key:

```bash
ssh-keygen -R ivar.local
```

Then try connecting again.

### Ethernet adapter shows "Media disconnected"

- Make sure the Pi is powered on and the cable is plugged in on both ends
- Try a different ethernet cable
- Check Device Manager → Network adapters — the ethernet controller may be disabled
- Corporate IT may have disabled the port via group policy

### "Permission denied" on SSH

- Double-check your username and password
- Make sure you're using the credentials set in Raspberry Pi Imager
- If using public key auth, verify your key was added during flashing
- If you forgot the password, re-flash the SD card

### VS Code can't connect

- Make sure regular SSH works first (`ssh ivar` in a terminal)
- Check that the Remote-SSH extension is installed
- Try reloading VS Code (`Ctrl+Shift+P` → "Reload Window")

### Camera not detected

Run on the Pi:

```bash
libcamera-hello --list-cameras
```

If no cameras are listed:
- Re-seat the ribbon cable on both ends
- Try the other CSI port on the Pi 5
- Make sure `imx500-all` is installed: `sudo apt install -y imx500-all`
- Reboot: `sudo reboot`
