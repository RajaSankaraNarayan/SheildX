# ShieldX Project - Changes & Enhancements

This document outlines the state of the project when I first started, and the sweeping improvements made to upgrade the entire system into a functional, secure, and modern Voice AI Banking Platform.

---

## 1. The Frontend UI
### What it had originally:
- A rudimentary "high-school level" HTML file (`index.html`) with basic inline styles and zero visual appeal.
- Hardcoded JavaScript (`app.js`) that did not successfully capture or stream microphone audio.
- A basic red fraud warning box that popped up instantly without any dynamic interaction.

### What we changed it to:
- **Web3 Premium Neobank Dashboard**: Completely rewrote the UI with ultra-modern glassmorphism (1px transparent borders, deep blurs, responsive grids).
- **Ambient Glow Backgrounds**: Built a dynamic, slow-moving radial mesh gradient background (`styles.css`).
- **Sentinel Dynamic Island Overlay**: Converted the ugly red alert box into an Apple-style "FaceTime/Dynamic Island" overlay that elegantly blurs the screen and pulses when the AI intercepts a transaction.
- **Walkie-Talkie Voice Assistant**: Built a complex `MediaRecorder` client directly into `app.js`. You can now hold a glowing microphone Floating Action Button (FAB) at any time to ask the AI questions natively in the browser.

---

## 2. The Voice AI Backend (FastAPI & Pipecat)
### What it had originally:
- The Pipecat Voice engine (`agent.py` and `pipeline.py`) was deeply broken due to misconfigured pip packages, dependency conflicts (Pydantic V1 vs V2), and deprecated Google AI models.
- The Python virtual environment was missing critical libraries like `python-dotenv` and `python-multipart`.
- The system was relying on `gemini-1.5-flash` which Google completely removed in 2026, causing the Voice AI to crash silently.

### What we changed it to:
- **Dependency Overhaul**: Stripped out bloatware, manually bypassed conflicting Google Speech packages, and successfully built a working Python environment.
- **Model Upgrades (The 2026 Shift)**:
  - Upgraded Google Gemini from the deprecated `1.5-flash` to the state-of-the-art **`gemini-3.5-flash`** across both `main.py` and `pipeline.py`.
  - Upgraded Sarvam Speech-to-Text from `saaras:v1` (deprecated) to **`saaras:v2.5`** to restore hearing capabilities.
  - Upgraded Sarvam Text-to-Speech to the **`bulbul:v1`** model using the `shubh` speaker profile to restore voice generation.
- **New Walkie-Talkie Endpoint**: Created a brand new route `/api/v1/support_voice` in `main.py` that handles the incoming browser audio, chains STT -> LLM -> TTS, and streams the synthesized audio file back to the browser.
- **Fixing the Crash**: Solved the `python-multipart` crash which was preventing the FastAPI server from even booting up when you clicked `start_all.bat`.

---

## Current Status
The platform is fully operational. 
- You can route a fraudulent transaction (by clicking "Enable Tor Routing"), which triggers the dynamic island AI interception.
- You can press and hold the **Hold to Ask AI** button at any time to ask general doubts (like SMS phishing questions) and it will reply back in real-time.
