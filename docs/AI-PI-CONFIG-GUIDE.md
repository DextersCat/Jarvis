# AI-Pi Configuration Helper

## Quick Setup Instructions

### Step 1: Get AI-Pi Information

You'll need to know:
1. **IP Address** - Find it on AI-Pi by running: `hostname -I`
2. **Username** - Usually `pi` for Raspberry Pi
3. **Password or SSH Key** - Your authentication method

### Step 2: Test Connection from PowerShell

Try connecting manually first:
```powershell
# Basic connection (will prompt for password)
ssh pi@YOUR-IP-ADDRESS

# Example:
ssh pi@192.168.1.100
```

### Step 3: Update launch-ai-pi.ps1

Once you confirm connection works, edit `launch-ai-pi.ps1`:

**Find this section (around line 16):**
```powershell
# Uncomment and modify the line below with your actual AI-Pi connection
# ssh user@ai-pi-hostname
```

**Replace with your actual command:**
```powershell
# Uncomment and modify the line below with your actual AI-Pi connection
ssh pi@192.168.1.100
```

### Step 4: Optional - Setup SSH Key (No Password)

For seamless connection without password prompts:

```powershell
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "jarvis-workspace"

# Copy key to AI-Pi (enter password one last time)
ssh-copy-id pi@YOUR-IP-ADDRESS

# Test passwordless connection
ssh pi@YOUR-IP-ADDRESS
```

---

## Common AI-Pi Connection Methods

### Method 1: Direct IP (Basic)
```powershell
ssh pi@192.168.1.100
```

### Method 2: With Custom Port
```powershell
ssh -p 2222 pi@192.168.1.100
```

### Method 3: With SSH Key
```powershell
ssh -i ~/.ssh/ai-pi-key pi@ai-pi.local
```

### Method 4: With Hostname (if configured)
```powershell
ssh pi@ai-pi.local
```

---

## Troubleshooting

### Can't find AI-Pi IP address?
On your network router, look for a device named "raspberrypi" or similar.

### Connection refused?
- Ensure SSH is enabled on AI-Pi
- Check if AI-Pi is powered on and connected to network
- Verify firewall settings

### Permission denied?
- Double-check username (usually `pi`)
- Verify password or SSH key is correct

---

## After Configuration

Once `launch-ai-pi.ps1` is configured, you can:

1. **Launch AI-Pi only:**
   ```powershell
   .\launch-ai-pi.ps1
   ```

2. **Launch both systems:**
   ```powershell
   .\launch-both.ps1
   ```

3. **Check JARVIS status on AI-Pi:**
   ```bash
   # After connecting to AI-Pi
   systemctl --user status jarvis
   # Or wherever JARVIS is running
   ```

---

**Need help?** Ask Nexus or Astra for assistance with AI-Pi connection configuration.
