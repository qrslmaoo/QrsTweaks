# QrsTweaks

![QrsTweaks Logo](https://github.com/user-attachments/assets/PLACEHOLDER_LOGO_PNG)  
**A comprehensive local Windows optimization suite**  
Built with **Python** and **PySide6** – 100% offline, no APIs, no telemetry.

[![GitHub stars](https://img.shields.io/github/stars/qrslmaoo/QrsTweaks?style=flat-square)](https://github.com/qrslmaoo/QrsTweaks/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/qrslmaoo/QrsTweaks?style=flat-square)](https://github.com/qrslmaoo/QrsTweaks/network/members)
[![GitHub issues](https://img.shields.io/github/issues/qrslmaoo/QrsTweaks?style=flat-square)](https://github.com/qrslmaoo/QrsTweaks/issues)
[![GitHub license](https://img.shields.io/github/license/qrslmaoo/QrsTweaks?style=flat-square)](https://github.com/qrslmaoo/QrsTweaks/blob/main/LICENSE)
[![Python version](https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-lightgrey?style=flat-square)](https://www.microsoft.com/windows)

---

## 📖 Overview

**QrsTweaks** is a modern, open-source Windows optimization tool designed to run completely locally. It combines system performance enhancements, gaming optimizations, and a built-in password manager into a single, easy-to-use desktop application.

- No internet connection required  
- No data collection  
- No third-party dependencies beyond Python  

---

##  Features

### Windows Optimizer
- Remove unnecessary background processes
- Optimize startup programs and services
- Reduce system resource usage
- Improve overall responsiveness

### Game Optimizer
- Apply gaming-focused performance profiles
- Prioritize CPU and GPU resources
- Reduce input lag and stuttering
- One-click game mode activation

### Password Manager
- Secure local storage of credentials
- Encrypted database with strong default settings
- Simple and intuitive interface
- Auto-fill ready (future update)

---

##  Screenshots

<div align="center">
  <img src="https://github.com/qrslmaoo/QrsTweaks/blob/main/screenshots/ss1.png?raw=true" width="48%" alt="Main Dashboard" />
  <img src="https://github.com/qrslmaoo/QrsTweaks/blob/main/screenshots/ss2.png?raw=true" width="48%" alt="Game Optimizer" />
  <br><br>
  <img src="https://github.com/qrslmaoo/QrsTweaks/blob/main/screenshots/ss3.png?raw=true" width="48%" alt="Password Manager" />
</div>

*Screenshots will be updated as the UI evolves.*

---

##  Getting Started

### Prerequisites
- Windows 10 or Windows 11 (64-bit)
- Python 3.11 or newer
- pip (Python package manager)

### Installation from Source

git clone https://github.com/qrslmaoo/QrsTweaks.git
cd QrsTweaks
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app/main.py
Building a Standalone Executable (Optional)
bashpip install pyinstaller
pyinstaller --onefile --windowed --icon=assets/icon.ico app/main.py
The executable will be created in the dist/ folder.

##  Development
bash# Clone and set up
git clone https://github.com/qrslmaoo/QrsTweaks.git
cd QrsTweaks

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app/main.py

##  Releases
No pre-built releases yet.
Automated builds and one-click installers are in development.
👉 Star the repository to get notified when the first release drops!

##  Contributing
Contributions are welcome and encouraged!

Fork the repository
Create a feature branch (git checkout -b feature/amazing-thing)
Commit your changes (git commit -m 'Add amazing thing')
Push to the branch (git push origin feature/amazing-thing)
Open a Pull Request

Please update tests and documentation as appropriate.
Code Style

PEP 8 compliant
Type hints recommended
Clear, descriptive commit messages


##  License
This project is licensed under the GNU General Public License v3.0 – see the LICENSE file for details.
textQrsTweaks - A local Windows optimization suite
Copyright (C) 2025 qrslmaoo

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

##  Support the Project
If QrsTweaks helps you, please give it a star ⭐ – it helps others discover the project!
Found a bug? Have a feature request?
Open an issue or start a discussion.


Made with ❤️ for a faster, cleaner Windows experience
