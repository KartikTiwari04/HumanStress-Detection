# 🧠 Human Stress Detection System

<div align="center">

![GitHub License](https://img.shields.io/github/license/KartikTiwari04/HumanStress-Detection)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-blue)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6%2B-yellow)
![GitHub Stars](https://img.shields.io/github/stars/KartikTiwari04/HumanStress-Detection)
![GitHub Issues](https://img.shields.io/github/issues/KartikTiwari04/HumanStress-Detection)

**Real-time stress detection using keyboard & mouse patterns with machine learning**

[🚀 Live Demo](#live-demo) • [📖 Documentation](#documentation) • [🛠️ Installation](#installation) • [🎮 Usage](#usage) • [🤝 Contributing](#contributing)

</div>

## 📌 Overview

**StressSense AI** is an innovative system that detects human stress levels by analyzing keyboard and mouse interaction patterns in real-time. Using machine learning, it predicts stress levels (Calm → Extreme) without cameras, microphones, or personal data collection.

### ✨ Key Features
- **🎯 Real-time Stress Analysis** - Monitors typing speed, mouse patterns, click frequency
- **🖥️ Application Tracking** - Identifies which apps cause most stress
- **🌿 Wellness Recommendations** - Smart break suggestions based on stress levels
- **🔒 Privacy First** - All processing happens locally, no data leaves your computer
- **📊 Interactive Dashboard** - Beautiful visualizations and real-time analytics

## 🚀 Live Demo

**Try it without installation!** [Click here for Online Demo](https://htmlpreview.github.io/?https://github.com/KartikTiwari04/HumanStress-Detection/blob/main/frontend/index.html)

**Or run locally in 3 steps:**

```bash
# 1. Clone repository
git clone https://github.com/KartikTiwari04/HumanStress-Detection.git
cd HumanStress-Detection

# 2. Install & run backend
cd backend
pip install -r requirements.txt
python main.py

# 3. In new terminal, serve frontend
cd ../frontend
python -m http.server 8080

# Open: http://localhost:8080
