# EchoPy Project Context

## Overview

EchoPy is a real-time music visualizer built with Python, PySide6, and NumPy. It captures system audio and renders various artistic visualizations.

## Core Stack

- **Framework**: PySide6 (Qt for Python)
- **Audio Core**: sounddevice (PortAudio wrapper)
- **Math/Signal Processing**: NumPy (FFT, Windowing)
- **Aesthetics**: Custom QSS (Glassmorphism), Vanilla CSS/HTML for About dialog.

## Architectural State (Refactored)

- **SOLID Principles**: Applied (SRP for visualizers, DIP for audio processing).
- **VisualizerFactory**: Centralized management of visualization styles (OCP).
- **AudioProcessor**: Decoupled from UI, supports dependency injection for smoothing buffers.
- **Resource Management**: Externalized QSS and image resources.

- **Hardware Driver Conflict**: NVIDIA SyncMaster (HDMI/DP).
  - **Status**: ✅ SOLVED (2026-01-28)
  - **Solution**: Integrated native WASAPI Loopback via `PyAudioWPatch`. The engine now automatically detects and utilizes the correct loopback device even on graphics card outputs.
- **NumPy 2.0 Compatibility**: The system uses NumPy 2.4.1.
  - **Optimization**: `AudioProcessor` callback has been refactored for vectorized Boolean masking to avoid performance bottlenecks (Input Overflow).

## Current State (Updated 2026-01-28)

- **Logic**: Fully optimized for NumPy 2.0.
- **Audio Capture**: IMPROVED.
  - Integrated **Weighted Multichannel Downmixing** (inspired by CAVA) to preserve surround audio fidelity on NVIDIA SyncMaster/HDMI drivers.
  - Enhanced **WASAPI Loopback Discovery** with name-matching and "SyncMaster" prioritization.
- **Visuals**: Superior 'liquid' movement achieved via **CavaFilter** (Integral + Fall-off filters), replacing simple EMA smoothing.
- **Calibration**: `NOISE_FLOOR = 0.00020` and `GAIN = 15000` maintained for clean response.
