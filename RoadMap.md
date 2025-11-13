# QrsTweaks Roadmap
A structured long-term development plan for the full Windows & Game optimization suite.

---

## ✔ Phase 1 — Core Application Setup (Completed)
- Base PySide6 app skeleton  
- Frameless window + sidebar navigation  
- Windows Optimizer page implemented  
- Game Optimizer initial UI created  
- Password vault skeleton created  
- Global theme + QSS foundation  

---

## ✔ Phase 2 — Windows Optimizer Core Features (Completed)
### Implemented:
- System Scan  
- Temp Cleanup  
- Deep Cleanup  
- Power Plan (High Performance)  
- Safety (Restore Point)  
- Memory-Leak Protector  
- Network Optimizer (DNS / CTCP / Nagle / Autotuning)  
- Startup Analyzer  
- Storage Analyzer (Largest files, directories, drive scan)  
- Profiles (gaming/productivity/streaming)  
- System RepairOps (DISM / SFC / Update repair)  
- Safe Debloat module  
- UI tweaks (Explorer, Widgets, Chat, etc.)  
- Backup & Restore system  
- Scrolling, spacing, card layout perfected  

WindowsPage is now 100% feature-complete.

---

## ✔ Phase 3 — Game Optimizer UI Rewrite (Completed)
### Implemented:
- Full rewrite of GamesPage  
- Matching layout to WindowsPage  
- Full scroll wrapper with proper margins  
- Cards for: Target Game, Log, Fortnite Tweaks, Per-Game Tuning, Storage Tweaks, Game Profiles  
- Backend hookups for:
  - Disable Game Bar / DVR  
  - Clean Fortnite Logs + Crash Dumps  
  - Clean Fortnite Shader Cache  
  - Clean DirectX Cache  
- Removed broken dividers  
- Fully aligned & consistent UI  

---
  
## Phase 4 — Game Optimizer Logic (IN PROGRESS)

### ✔ Completed so far:
- Fortnite cleaning fully wired  
- DirectX cleaning wired  
- Crash/Shader logic connected  
- Game profile buttons safe + stubbed  

### 🚧 Next Tasks:
### **A) Per-Game CPU Priority**
- Detect active game process  
- Apply HIGH / ABOVE NORMAL  
- Safe fallback if not running  

### **B) Per-Game Nagle / TCP Latency Mode**
- Game-targeted registry tweaks  
- Log clean results  

### **C) Universal Game Temp Cleaner**
- Clean `%LOCALAPPDATA%/<Game>` logs/crashes  
- Clean `%TEMP%/<Game>*`  
- Fortnite gets special-case logic  

### **D) Reset Game Config**
- Backup configs (`GameUserSettings.ini`, etc.)  
- Restore defaults  
- Add revert option later  

---

## Phase 5 — Game Profile System (Not Started)
- `.qrsgame` export format  
- `.qrsgame` import  
- Store CPU priority, network modes, cleanup behavior, shader behavior, config resets  
- Per-game preset templates  

---

## Phase 6 — Global Profile Manager (Not Started)
- Combine `.qrsp` + `.qrsgame`  
- Multi-level profile application  

---

## Phase 7 — Password Vault Completion
- AES-256 encryption  
- UI improvements  
- Import/export encrypted vault  
- Clipboard auto-clear  
- Security audits  

---

## Phase 8 — MSI Installer + Release Packaging
- PyInstaller EXE (ignored via .gitignore)  
- MSI installer  
- GitHub Releases  
- Auto-update checker (non-AI)  

---

## Phase 9 — Marketing & Branding
- GitHub README polish  
- GIF showcase  
- Feature comparison charts  
- Branding & visual identity  

---

# ✔ Status Summary
| System | Status |
|-------|--------|
| Windows Optimizer | 100% COMPLETE |
| Game Optimizer UI | 100% COMPLETE |
| Game Optimizer Logic | IN PROGRESS |
| Passwords | 20% |
| Backup System | ✓ |
| Installer | Not started |
