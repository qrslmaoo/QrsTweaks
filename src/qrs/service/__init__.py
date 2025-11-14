# src/qrs/service/__init__.py

"""
Service / daemon helpers for QrsTweaks.

Contains:
  - controller: start/stop/status for the background daemon
  - autostart:  Windows "Run" entry for daemon-on-login
  - daemon_main: simple heartbeat loop used by the controller
"""
