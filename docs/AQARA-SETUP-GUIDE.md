# Aqara M2 Hub Setup Guide for Home Assistant

## Method 1: Official Aqara Integration (RECOMMENDED - Easiest)

### Prerequisites
- Aqara M2 Hub connected to your network
- Aqara Home app installed on your phone
- Aqara account created

### Steps:

1. **Open Home Assistant**
   - Go to: http://192.168.1.3:8123

2. **Add Aqara Integration**
   - Click: **Settings** → **Devices & Services**
   - Click: **+ ADD INTEGRATION** (bottom right)
   - Search for: **Aqara**
   - Select: **Aqara** (official integration)

3. **Authentication**
   - Select region: **China**, **Europe**, **USA**, etc. (where your Aqara account is registered)
   - Enter your **Aqara account username/email**
   - Enter your **Aqara account password**
   - Click **Submit**

4. **Hub Discovery**
   - HA will automatically discover your M2 Hub
   - Select your M2 Hub from the list
   - All devices should import automatically

5. **Verify**
   - Go to: **Settings** → **Devices & Services** → **Aqara**
   - You should see: M2 Hub + all connected devices

---

## Method 2: HomeKit Controller (LOCAL - No Cloud)

⚠️ **Only works if your M2 Hub is exposed to HomeKit**

### Prerequisites
- M2 Hub must be added to Apple Home app first
- M2 Hub firmware must support HomeKit

### Steps:

1. **Add M2 Hub to Apple Home (if not already done)**
   - Open Apple Home app on iPhone
   - Add M2 Hub using HomeKit code

2. **In Home Assistant**
   - Settings → Devices & Services → **+ ADD INTEGRATION**
   - Search: **HomeKit Controller**
   - HA should auto-discover the M2 Hub
   - Enter the **HomeKit pairing code** (same as on M2 Hub sticker/screen)

3. **Import Devices**
   - Select which devices to import
   - All Aqara devices connected to M2 Hub should appear

---

## Method 3: Xiaomi Gateway 3 Integration (Alternative)

If Aqara integration doesn't work, try:

1. **Add Integration**
   - Search for: **Xiaomi Gateway 3**
   - Enter M2 Hub IP address: (find it in your router or Aqara app)

2. **Enable Developer Mode on M2 Hub**
   - In Aqara Home app:
   - Go to M2 Hub settings
   - Enable "LAN Control" or "Developer Mode"
   - Get the hub token/key

---

## Troubleshooting

### If Aqara integration fails:
```
Check if your Aqara account region matches the server region
Try logging out/in from Aqara Home app
Ensure M2 Hub firmware is updated
```

### If HomeKit Controller fails:
```
Ensure M2 Hub is HomeKit-compatible (check model number)
Reset HomeKit pairing on M2 Hub
Try removing from Apple Home and re-adding
```

### If nothing works:
```
Check M2 Hub is online and reachable on network
Verify HA can reach M2 Hub IP: ssh spencer@ai-pi.local "ping -c 3 <M2_HUB_IP>"
Check HA logs: docker logs homeassistant
```

---

## Quick Commands to Help Diagnose

**Find M2 Hub IP address:**
```bash
ssh spencer@ai-pi.local "sudo arp-scan --localnet | grep -i 'aqara\|lumi'"
```

**Check if HA can reach M2 Hub:**
```bash
ssh spencer@ai-pi.local "ping -c 3 <M2_HUB_IP>"
```

**Check HA logs for integration errors:**
```bash
ssh spencer@ai-pi.local "docker logs homeassistant 2>&1 | grep -i 'aqara\|homekit' | tail -20"
```

---

## What I Need to Know

To help you further, please tell me:

1. **Do you have an Aqara account?** (yes/no)
2. **Is your M2 Hub in Apple Home app?** (yes/no)
3. **Which method do you want to try?**
   - Option A: Aqara cloud integration (easiest)
   - Option B: HomeKit Controller (local, no cloud)
   - Option C: Need help finding M2 Hub IP address

4. **Error message you're seeing** (if any)

---

## Expected Device List After Setup

Once connected, you should see:

**Cameras:**
- Aqara G100 (Front Door)
- Aqara E1 (Teddy Cam)

**Sensors:**
- Motion sensors
- Door/Window contact sensors
- Temperature/Humidity sensors

**Lights:**
- All Aqara smart lights

**Switches:**
- Aqara smart plugs/switches

**Scenes:**
- Automations from Aqara app
