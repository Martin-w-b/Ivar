# Connection Guide: Mac to Raspberry Pi

This guide covers connecting to your Raspberry Pi from a Mac. The workflow is very similar to Windows, with a few differences noted below.

## 1. SSH Config (One-Time Setup)

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

## 2. Terminal SSH

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

## 3. VS Code Remote SSH

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

## 4. Running Ivar

From any terminal connected to the Pi:

```bash
cd ~/ivar
source venv/bin/activate
python main.py
```

## 5. Development Workflow

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

### "Permission denied" on SSH

- Double-check your username and password
- If you forgot the password, re-flash the SD card

### VS Code can't connect

- Verify SSH works first: `ssh ivar`
- Make sure the Remote-SSH extension is installed
- Reload VS Code: `Cmd+Shift+P` → "Reload Window"
