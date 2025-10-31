# 🐺 grizGPT — Autonomous AI Pentester & Dev Companion

> **"An AI that doesn’t just respond—it thinks, scans, rewrites itself, and delivers actionable insight."**  
> **Built for white-hat hackers, dev warriors, and AI testers who demand clean code & zero fluff.**

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Groq](https://img.shields.io/badge/Groq-API-black.svg)
![Status](https://img.shields.io/badge/Status-Beta-orange.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Codespaces-informational.svg)

---

## 🌟 **Why grizGPT?**

Forget generic chatbots. grizGPT is an **autonomous AI** that **executes real scans**, **rewrites its own logic**, and **delivers professional-grade insights** — all while staying 100% **white-hat** and **modular**.

It's not just a tool — **it's your AI ally.**

---

## ✨ **Core Features**

### 🔁 **Autonomous Scanning Loop**
- Run `!scan example.com` → AI performs initial Nmap scan
- Analyzes results for vulnerabilities or risks
- **Dynamically rewrites its own `scan.py`** to target detected services
- Re-scans with refined logic (up to 3 rounds)
- Returns a **concise, professional security summary**
---

---

## 🚀 **Quick Start**

### 1. Clone & Install
```bash
git clone https://github.com/redzskid/grizgpt.git
cd grizgpt
pip install groq rich requests beautifulsoup4
sudo apt install nmap  # required for active scanning
#get Free Groq API Key Sign up at https://console.groq.com/ (no credit card)
python grizzai.py
