# 🔒 SecureCam: IoT-Based Threat Detection System

**SecureCam** is an advanced IoT-based Smart Surveillance System designed to detect **weapons, criminals, and suspicious individuals** in real time using AI, and instantly trigger alerts through both **email notifications** and **ESP32-based hardware (buzzer + servo)** responses.

This project integrates:
- **YOLOv8** for weapon detection  
- **FaceNet** for facial recognition  
- **Flask** for backend + dashboard  
- **ESP32-CAM** for live video streaming  
- **IoT alerts** using buzzer & servo  
- **Cloudinary** for cloud image storage
- **PostgreSQL** for meta data
- **Gmail SMTP** for instant alert emails

---

## Features

**Weapon Detection (YOLOv8)**  
Detects firearms, knives, and other real weapons in real time.

**Criminal Recognition (FaceNet)**  
Identifies known criminals from a local or cloud-stored watchlist.

**Suspicious Detection (Masked/Hidden Faces)**  
Detects occluded or masked faces using Laplacian variance-based analysis.

**IoT Integration with ESP32**  
- Sends HTTP alert signals (`/alert?alert=weapon`) to ESP32.
- ESP32 triggers buzzer alerts and servo rotation to indicate detection.

**Email Notifications**  
Automatically sends email alerts with annotated detection images.

**Cloud Integration (Cloudinary)**  
All annotated frames are uploaded to Cloudinary for remote access.

**Web Dashboard (Flask)**  
Live feed preview, recent detection logs, and system health monitoring.

---

## System Architecture

```
          ┌─────────────────────┐
          │    ESP32-CAM (IoT)  │
          │  Live Stream Server │
          │  /alert endpoint    │
          └─────────┬───────────┘
                    │  (HTTP Stream)
                    ▼
          ┌─────────────────────┐
          │  Flask Backend API  │
          │  /api/frame upload  │
          │  YOLOv8 + FaceNet   │
          │  Threat Detection   │
          └─────────┬───────────┘
                    │  (HTTP Alert)
                    ▼
          ┌─────────────────────┐
          │  ESP32 Hardware     │
          │  Buzzer + Servo     │
          │  Local Alarm Signal │
          └─────────┬───────────┘
                    │
                    ▼
          ┌─────────────────────┐
          │  Email + Cloud Logs │
          │  (SMTP + Cloudinary)│
          └─────────────────────┘
```

---

## Installation & Setup

### Clone Repository
```bash
git clone https://github.com/your-username/SecureCam.git
cd SecureCam
```

### Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # (Windows)
# or
source venv/bin/activate  # (Linux/Mac)
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Environment Configuration

Create a file named `.env` in the project root:

```
FLASK_ENV=development
SECRET_KEY=supersecretkey
DATABASE_URL=sqlite:///data.db

# ESP32 Camera Stream
ESP32_URL=http://192.168.137.231

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_key
CLOUDINARY_API_SECRET=your_secret

# Email (Gmail App Password Required)
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
ALERT_EMAIL_TO=recipient_email@gmail.com

# YOLO + Face Settings
WEAPON_CONF_THRESHOLD=0.4
FACENET_THRESHOLD=0.45

# Cooldown Config
EMAIL_COOLDOWN_SECONDS=30
EMAIL_COOLDOWN_SCOPE=global
```

---

## ESP32-CAM Firmware Setup

### Required Hardware
- **ESP32-S3-CAM** or **AI Thinker ESP32-CAM**
- **OV2640 camera module**
- **Servo motor (SG90 / MG90S)**
- **Active buzzer**
- **Power source (5V)**

### Upload Code
Flash the provided ESP32 sketch (in `/esp32/securecam.ino`) using Arduino IDE or PlatformIO.

### Update Wi-Fi Credentials
In the ESP32 code:
```cpp
const char* ssid = "YourWiFiName";
const char* password = "YourWiFiPassword";
```

### Stream + Alert Endpoints
- Live stream: `http://<ESP32_IP>/`
- Buzzer alert: `http://<ESP32_IP>/alert?alert=weapon`

When the backend detects a weapon or known criminal, it automatically sends an HTTP request to `/alert`.

---

## Running the Backend

### Start Flask Server
```bash
python app.py
```

The server starts at:
```
http://127.0.0.1:5000
```

### Start Camera Capture
(Optional if using ESP32 stream auto-feed)
```bash
python capture_and_post.py
```

---

## Key Modules

| Module | Description |
|--------|--------------|
| `services/inference.py` | Main detection pipeline (YOLO + FaceNet + ESP alert) |
| `services/camera_controller.py` | Manages ESP32 stream capture |
| `ml/yolo_wrapper.py` | Loads YOLOv8 model (ONNX version) |
| `ml/facenet_wrapper.py` | Handles face embeddings |
| `services/email_alerts.py` | Sends email notifications |
| `services/db_ops.py` | Logs detections to the database |
| `services/storage.py` | Uploads annotated frames to Cloudinary |
| `templates/index.html` | Web dashboard UI |

---

## Alert Workflow

| Event | Hardware Action | Email Alert |
|--------|------------------|--------------|
| Weapon detected | Buzzer (3 short beeps) | “Weapon Detected” |
| Known criminal detected | Buzzer (2 long beeps) | “Criminal Identified” |
| Suspicious masked face | 1 long beep | “Suspicious Activity” |
| No threat | No action | — |

---

## Tech Stack

| Layer | Technology |
|--------|-------------|
| **Frontend** | HTML + JS + Bootstrap |
| **Backend** | Flask (Python) |
| **AI Models** | YOLOv8 (ONNX), FaceNet |
| **Database** | SQLite / PostgreSQL |
| **IoT** | ESP32 (C++ / Arduino) |
| **Cloud Storage** | Cloudinary |
| **Email Service** | Gmail SMTP |

---

## Future Improvements
- Add **MQTT** or **WebSocket** support for real-time event streaming.  
- Integrate **license plate detection** for vehicles.  
- Add **user management dashboard** for admins.  
- Include **offline fallback mode** for local-only alerts.  

---

## Author
**Hanzala Salaheen**  
Full-Stack & AI Developer  
Contact: salaheenhanzala624@gmail.com
GitHub: [github.com/Hanzi448](https://github.com/Hanzi448)

---

## License
This project is released under the **MIT License**.  
You are free to use, modify, and distribute it for educational or research purposes.

---

**SecureCam** — “Because smart surveillance should not just watch, but *protect*.”
