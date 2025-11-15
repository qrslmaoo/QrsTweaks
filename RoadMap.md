# QrsTweaks – Roadmap

This roadmap reflects the current architecture of QrsTweaks as a **manual-only Windows optimization suite**.
There are **no background services**, **no telemetry**, and **no automated monitoring**. All optimizations run
only when the user triggers them.

---

##  Phase 1 — Core UI & Navigation (Completed)
- Frameless window
- Sidebar navigation
- Dashboard, Windows, Games, Passwords pages
- QDark stylesheet
- Smooth layout updates

---

##  Phase 2 — Windows Optimizer Foundation (Completed)
- Temp file cleanup
- Deep cleanup
- Power plan creation
- Restore point creation
- Startup entry listing
- Basic networking tools
- DNS switching
- CTCP toggles
- Autotuning controls
- Nagle toggle
- Latency test utility

---

##  Phase 3 — Game Optimizer Module (Completed)
- Fortnite shader/log cleanup
- DirectX cache cleanup
- Xbox Game Bar / Game DVR disable
- Game process detection (manual)
- Priority & CPU affinity controls
- Safe preset builder (Fortnite)

---

##  Phase 4 — Profile Manager (Completed)
- Gaming preset
- Productivity preset
- Streaming preset
- Save/export .qrsp profiles
- Load/import profiles

---

##  Phase 5 — UI Expansion (Completed)
- RepairOps card
- Debloat card
- Taskbar & Explorer UI Tweaks card
- Backup & Restore card
- Full WindowsPage redesign

---

##  Phase 6 — Windows Fix Tools (In Progress)
Add new safe, manual-only repair tools:
- Re-register ShellExperienceHost
- Rebuild Taskbar
- Re-register UWP apps
- Reset Explorer & start menu
- Reset Windows Search index
- Reset icon cache
- Additional DISM / SFC helpers

---

##  Phase 7 — UI Fix Tools (In Progress)
Focus on visible system/UI problems:
- Restore missing taskbar icons
- Clear Explorer thumbnail/index caches
- Toggle immersive menus
- Disable/restore rounded corners
- Reset personalization cache

---

##  Phase 8 — Expanded Profiles
Introduce additional one-click presets:
- Competitive Gaming
- Streaming + Gaming Hybrid
- Media Creation / Editing
- Windows Lite Mode
- Laptop Battery Mode

Each preset applies a curated set of tweaks.

---

##  Phase 9 — Game Optimizer Addons
Add per-game optimization modules:
- Fortnite config templates (optional)
- Minecraft JVM tuning helper
- COD shader/reset utilities
- Valorant config cleanup
- Universal DX shader reset module

---

##  Phase 10 — General UI Polish
- Card hover/press effects
- Improved spacing & padding
- Animated transitions
- More icons
- Cleaner scroll behavior

---

##  Phase 11 — Packaging & Release Prep
- Build with PyInstaller
- No-console EXE
- Custom app icon
- Optional NSIS / MSI installer
- Versioning & release tags
