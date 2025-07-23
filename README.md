
# Qonur AI Marionette Bear (Qonur)

An interactive AI-driven animatronic bear that listens, thinks, and speaks in any language (include Azerbaijani). The project integrates:

* **ESP32 firmware** for servo control (eyes, mouth, limbs), LED animations, and Blynk cloud connectivity.
* **Python application** using GenAI for conversational AI, TTS, and coordinating servo animations through serial commands.

---

## Table of Contents

1. [Features](#features)
2. [Hardware Requirements](#hardware-requirements)
3. [Software Requirements](#software-requirements)
4. [Repository Structure](#repository-structure)
5. [Setup & Installation](#setup--installation)

   * [ESP32 Firmware](#esp32-firmware)
   * [Python Application](#python-application)
6. [Configuration](#configuration)
7. [Wiring & Pinout](#wiring--pinout)
8. [Usage](#usage)
9. [Customization](#customization)
10. [Troubleshooting](#troubleshooting)
11. [License](#license)
12. [Contact](#contact)

---

## Features

* **Voice interaction**: Press Enter to record; AI responds and moves the bear’s mouth.
* **Eye & mouth servos**: Blink and animate in sync with speech.
* **LED animations**: Breathing green LEDs while listening, rainbow when idle.
* **Blynk integration**: Control additional servos remotely via smartphone app.

---

## Hardware Requirements

* **ESP32 dev board** (e.g., ESP32-WROOM)
* Raspberry Pi
* **Adafruit PCA9685** PWM servo driver
* **9–10 standard servos** (2 eyes, mouth, arms, head)
* **WS2812B LED strip** (8 LEDs)
* **Power supply** (5–6 V for servos and LEDs)
* **USB cable** for serial (ESP32 ↔ PC)

---

## Software Requirements

* **Python 3.8+**
* **pip** for Python dependencies
* **Arduino IDE** or PlatformIO for ESP32
* **Blynk mobile app** (for remote control)
* **Raspberry Pi OS** (if using a Raspberry Pi for the Python controller)
* **System libraries** on Raspberry Pi: libasound2-dev, portaudio19-dev, libsndfile1, ffmpeg, libsdl2-dev, libsdl2-mixer-dev, libsdl2-image-dev

---

## Repository Structure

```
/Qonur
├── control.ino         # ESP32 Arduino sketch
├── main.py             # Python AI controller
├── requirements.txt    # Python dependencies
├── README.md           # Project documentation
└── LICENSE             # Apache-2.0 license
```

---

## Setup & Installation

### ESP32 Firmware

1. Open **`Qonur.ino`** in Arduino IDE or PlatformIO.
2. Install libraries via Library Manager:

   * **Adafruit PWM Servo Driver**
   * **Adafruit NeoPixel**
   * **ArduinoJson**
   * **Blynk**
3. Update Wi‑Fi and Blynk credentials at the top of the sketch:

   ```cpp
   char ssid[] = "YOUR_SSID";
   char pass[] = "YOUR_PASSWORD";
   #define BLYNK_AUTH_TOKEN "YOUR_TOKEN"
   ```
4. Connect ESP32 to your PC via USB and flash.

### Python Application

#### Raspberry Pi Prerequisites

On a Raspberry Pi, install system dependencies before setting up the Python application:

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv libasound2-dev portaudio19-dev libsndfile1 ffmpeg libsdl2-dev libsdl2-mixer-dev libsdl2-image-dev
```

1. Create a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
3. Set your Google Gemini API key:

   ```bash
   export GEMINI_API_KEY="YOUR_GOOGLE_API_KEY"
   ```
4. Update serial port if needed (`/dev/ttyUSB0` default).

---

## Configuration

* **Google API Key**: Stored in `GEMINI_API_KEY` environment variable.
* **ESP32 Serial Port**: Modify `ESP32_PORT` in `main.py` if different.
* **Servo mappings**: Adjust pin numbers in `SERVO_MAPPINGS` (Python) and channel order in `servoNames` (ESP32).

---

## Wiring & Pinout

| Component          | ESP32 Pin | PCA9685 Channel |
| ------------------ | --------- | --------------- |
| Eye Right Servo    | SDA/SCL   | 7               |
| Eye Left Servo     | SDA/SCL   | 8               |
| Mouth Servo        | SDA/SCL   | 9               |
| Left Arm Shoulder  | SDA/SCL   | 0               |
| Left Arm Elbow     | SDA/SCL   | 1               |
| Left Arm Wrist     | SDA/SCL   | 2               |
| Head Servo         | SDA/SCL   | 3               |
| Right Arm Wrist    | SDA/SCL   | 4               |
| Right Arm Elbow    | SDA/SCL   | 5               |
| Right Arm Shoulder | SDA/SCL   | 6               |
| WS2812 LED Strip   | GPIO4     | N/A             |

*Use common ground between ESP32, PCA9685, servos, and power supply.*

---

## Usage

1. **Power on** the ESP32 and servos.
2. **Run** the Python script:

   ```bash
   python main.py
   ```
3. **Press Enter** to start/stop recording.
4. The bear will **respond in detected or specified language**, moving its mouth and blinking.
5. Use the **Blynk app** to trigger additional gestures via virtual pins.

---

## Customization

* **Voice & language**: Modify `actor_prompt` in `main.py`.
* **Servos & timings**: Tweak `mouthPattern`, blink interval, and servo speeds.
* **LED effects**: Change colors or patterns in `updateLEDs()` (ESP32 code).

---

## Troubleshooting

* **No serial connection**: Verify `ESP32_PORT` and permissions (`chmod a+rw /dev/ttyUSB0`).
* **API rate limits**: Handle `ResourceExhausted` exceptions or increase quotas.
* **Servo jitter**: Ensure a stable power supply with adequate current.

---

## License

This project is released under the **Apache-2.0 license**.

You are free to use, copy, modify, and distribute this code in both open and proprietary projects, provided you **retain the original copyright notice and this attribution** in all copies or substantial portions of the Software.

**Copyright © 2025 Jameel Hamzayev & Ritual Theater**

---

## Contact

For support, feature requests, or contributions, please open an issue at [GitHub Issues](https://github.com/jameelhamzayev/Qonur/issues) or reach out via email at `jamellhamzayev@gmail.com`.
