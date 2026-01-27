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

## Persistent Issues (Solved 2026-01-27)

- **Audio Capture Mismatch**: Bypassed using "Stereo Mix" + Windows "Listen" feature.
- **Silent Signal**: Fixed by correct Windows routing and hardware Hz synchronization.
- **Responsiveness**: Increased gain from 20x to 50x and reduced smoothing to 0.6 for more "aggressive" animations.
- **Dynamic Range Restoration**: Removed experimental AGC and Log-scaling that were causing visual saturation. Reverted to a robust linear gain (x40) with stable normalization.

## Current State

- **Audio Status**: ACTIVE and capturing system sound via AGC.
- **Visuals**: Maximum energy mode (Smoothing 0.5, Log-scaling active).
