#  QrsTweaks Roadmap

Welcome to the development roadmap for **QrsTweaks**, the all-in-one Windows optimization suite built in Python + PySide6.  
This document outlines every major planned feature, milestone, and enhancement — from technical infrastructure to user experience.

---

##  Phase 1 — Foundation ( Completed)
**Goal:** Establish a stable, safe, and transparent optimization core.

- [x] Frameless, translucent PySide6 GUI (Suite layout)
- [x] Scrollable, animated cards for all pages
- [x] System Scan (real cleanable-space detection)
- [x] Power, Network, Memory, Startup optimizers
- [x] Windows Game Mode + High-Perf toggle logic
- [x] Safe Registry + PowerShell tweak handling
- [x] Restore defaults + Log exporter
- [x] Profile loader / applier (JSON)

---

##  Phase 2 — Power-User Expansion *(in progress)*
**Goal:** Add advanced but still safe performance enhancements.

- [ ] Deep Cleanup: browser caches, prefetch, Windows.old
- [ ] Disk analysis: SSD TRIM, defrag, large/duplicate file finder
- [ ] Service optimization: disable SysMain, telemetry, Xbox tasks
- [ ] Network repair + adaptive DNS auto-test
- [ ] "Apply Gaming Profile" (one-click performance preset)
- [ ] Log changelog of each tweak
- [ ] Scrollbar polish + visual refinements

---

##  Phase 3 — Profiles & Automation
**Goal:** Empower users to customize and share their own performance styles.

- [ ] **Profile System v2**
  - Load / save / edit tweak sets (`.json`)
  - Built-in presets: *Gaming*, *Creator*, *Minimal*, *Balanced*
  - "Apply Profile" and "Revert Profile" confirmation
- [ ] **Profile Store**
  - Integrate GitHub-hosted community profiles
  - Download, rate, and fork configs
  - Offline profile caching
- [ ] Scheduler
  - Schedule profile switching (Gaming at 6 PM, Productivity at 8 AM)
  - Built via Task Scheduler integration
- [ ] Portable mode (self-contained settings/logs)
- [ ] Auto-update check (compares latest GitHub Release)

---

##  Phase 4 — Insight & Visualization
**Goal:** Give users clear, visual feedback on their system’s performance.

- [ ] **Performance Score**
  - Before/After system scan comparison
  - FPS delta tracker (manual entry)
  - "Performance Index" summary card
- [ ] **Storage Heatmap**
  - Top 10 largest directories (with bar visualization)
- [ ] **Resource Overview**
  - CPU, RAM, Disk utilization snapshot (non-monitoring)
  - Graphical meters using `PySide6.QtCharts`
- [ ] Animated cleaning progress bars + success glow indicators
- [ ] Theme switcher (Cyber Red, Neon Blue, Stealth Black)

---

##  Phase 5 — Quality, Community & Distribution
**Goal:** Make QrsTweaks the top-rated open-source optimizer on GitHub.

- [ ] Code cleanup & modular structure (`src/qrs/modules/*`)
- [ ] Type hints and docstrings for all modules
- [ ] Tests for safety (simulate tweak execution)
- [ ] GitHub Actions build/test pipeline
- [ ] Windows `.exe` packaging via PyInstaller
- [ ] Version tags for each stable milestone
- [ ] README showcase:
  - Screenshots, GIFs, demo video
  - “Safe Tweaks Only” transparency badge
- [ ] Contributor Guide + Issue Templates
- [ ] Optional Discord community link

---

##  Vision
QrsTweaks aims to be the **cleanest, most transparent, and most effective** Windows optimization tool on GitHub —  
no telemetry, no ads, no shady scripts. 100 % local execution, fully open-source, and user-controllable.

---

###  Suggestions?
Open a [GitHub Issue](https://github.com/qrslmaoo/QrsTweaks/issues/new/choose) with the label **feature-request**,  
or discuss in the community thread once the Discord launches.

---

> **QrsTweaks** — Built for performance. Designed for clarity. Loved by power users.
