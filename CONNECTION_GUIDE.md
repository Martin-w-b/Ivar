# Connection Guide: Developing on the Pi from Your PC

This guide covers how to connect to your Raspberry Pi from your PC for development.

## Prerequisites

- Raspberry Pi is powered on and connected to the same network as your PC
- SSH is enabled on the Pi (configured during SD card flashing)
- You know your Pi's username, password, and hostname

## 1. SSH Config (One-Time Setup)

Create or edit `~/.ssh/config` on your PC (Windows: `C:\Users\<you>\.ssh\config`):

```
Host ivar
  HostName ivar.local
  User <your-pi-username>
```

This lets you type `ssh ivar` instead of the full address every time.

## 2. Terminal SSH

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

## 3. VS Code Remote SSH

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

## 4. Running Ivar

From any terminal connected to the Pi (SSH or VS Code terminal):

```bash
cd ~/ivar
source venv/bin/activate
python main.py
```

## 5. Development Workflow

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

### "Permission denied" on SSH

- Double-check your username and password
- Make sure you're using the credentials set in Raspberry Pi Imager
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
