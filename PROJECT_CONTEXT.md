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

## Current State (Updated 2026-05-22)

- **Logic**: Fully optimized for NumPy 2.0.
- **Audio Capture**: IMPROVED.
  - Integrated **Weighted Multichannel Downmixing** (inspired by CAVA) to preserve surround audio fidelity on NVIDIA SyncMaster/HDMI drivers.
  - Enhanced **WASAPI Loopback Discovery** with name-matching and "SyncMaster" prioritization.
- **Visuals**: Modernized aesthetics and coherent, high-end retro-neon visuals across core styles:
   - **Synthwave Grid (New)**: Added a premium 3D perspective scrolling neon grid visualizer with a reactive neon mountain range silhouette and an audio-pulsing sun with horizontal cutout lines.
   - **Circular Spectrum**: Upgraded with a rotating tech grid, erupting neon particle sparks on bass impacts, and gradient sweeps with glowing caps.
   - **Spectrum Bars**: Rebuilt as segmented LED columns with a glassmorphic backplate, calibration scale lines, rising embers, and falling neon peak caps.
   - **Radial Bars**: Refactored with an outrun central sun core featuring horizontal cutouts, pulsing dashed concentric rings, and outward erupting neon sparks.
   - **Waveform**: Enhanced with a vector oscilloscope grid, a moving horizontal laser scanline overlay, glowing energy aura fill, and reactive electron sparks shooting from peaks.
   - **Compatibility Fixes**: Fixed PySide6 `QPen` constructor errors by wrapping all gradients in a `QBrush` and providing proper line widths.
- **Testing**: Active verification via `tests/test_visualizers.py` programmatically validating render processes for all 13 styles under the Qt context. All 6/6 tests pass.
- **Calibration**: `NOISE_FLOOR = 0.00020` and `GAIN = 15000` maintained for clean response.

## Advanced Deployment (Frozen App Strategy)

- **Resource Pathing**: Use `sys._MEIPASS` path resolution (implemented in `utils.get_resource_path`) to ensure themes, icons, and QSS are found inside the temporary PyInstaller directory.
- **Windows Identity**: Use `ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID` to detach the app from the generic `python.exe` process, allowing custom taskbar icons.
- **Icon Header**: Windows executables require native `.ico` headers (PNG data wrapped in ICO structure) for explorer-level visibility.
- **Modern UI Patterns**: Right-click context menus replace legacy menu bars for immersive "frameless" designs. Shortcuts must be registered as window actions (`addAction`) to remain active when menus are hidden.
