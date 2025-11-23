# JARVIS Quick Reference Commands

## Ubuntu WSL2 Commands

### Access Ubuntu
```powershell
wsl -d Ubuntu-22.04
```

### Activate JARVIS Environment
```bash
source ~/jarvis_env/bin/activate
```

### Check GPU
```bash
nvidia-smi
```

### Python Version
```bash
python3 --version
```

---

## WSL Management

### List all WSL distributions
```powershell
wsl -l -v
```

### Set Ubuntu as default
```powershell
wsl --set-default Ubuntu-22.04
```

### Shutdown Ubuntu
```powershell
wsl --terminate Ubuntu-22.04
```

### Shutdown all WSL instances
```powershell
wsl --shutdown
```

---

## Useful Paths

### Ubuntu Home (from Windows)
```
\\wsl$\Ubuntu-22.04\root
```

### JARVIS Environment
```
\\wsl$\Ubuntu-22.04\root\jarvis_env
```

### Access from File Explorer
- Press `Win + R`
- Type: `\\wsl$`
- Navigate to Ubuntu-22.04

---

## Workspace Location

### Windows Path
```
C:\Users\spenc\JARVIS-Workspace
```

### Quick Access
```powershell
cd C:\Users\spenc\JARVIS-Workspace
```

---

## Launch Scripts

### Ubuntu Only
```powershell
.\launch-ubuntu-jarvis.ps1
```

### AI-Pi Only
```powershell
.\launch-ai-pi.ps1
```

### Both Systems
```powershell
.\launch-both.ps1
```
