# Spider Intelligence System - Homelab Integration

## 📖 Overview

This repository documents the **Spider Intelligence System** and its integration into a multi-system homelab. Spider provides **AI-powered monitoring, diagnostics, and predictive analysis** across all deployed systems, delivering expert-level insights and automation.

The homelab consists of three core systems (**Sanctum**, **Fathom**, **Haven**) and multiple smart devices. Spider serves as the central intelligence layer, monitoring both local and remote systems while providing actionable diagnostics.

---

## 🖥️ Core Systems

### **Sanctum (Precision Laptop - Control Hub)**

* **Hardware:** Dell Precision 5520 (Intel i7-7820HQ, 16GB RAM, Quadro M1200)
* **OS:** Ubuntu Server + CasaOS frontend
* **Role:** Central orchestration hub
* **Status:** **Active**
* **Key Services:**

  * Home Assistant OS (VM)
  * Tailscale (VPN)
  * AdGuard Home (installed, not configured)
  * Prometheus + Grafana (installed, not configured)

### **Fathom (Custom Build - AI/Gaming Workhorse)**

* **Hardware:** Ryzen 7 3700X, RTX 3060 12GB, 16GB DDR4-3200MHz
* **OS:** Ubuntu Server
* **Role:** AI processing + gaming + Spider host
* **Status:** **Active**
* **Key Services:**

  * Crafty Controller (Minecraft server)
  * Ollama (Llama 3.1 8B)
  * Spider Intelligence System

### **Haven (Future Storage/Media Server)**

* **Hardware:** Dell XPS 8900 (Intel i5-6400, GTX 745, 8GB RAM)
* **Role:** Planned media server & NAS
* **Status:** **Available, not deployed**

---

## 🕷️ Spider Intelligence System

### **Deployment**

* **Primary Host:** Fathom
* **Path:** `/opt/spider/`
* **Python Env:** `/opt/spider/venv/`
* **User:** `spider`

### **Capabilities**

* Local + remote system scanning (SSH integration)
* Filesystem, network, Docker, and VM monitoring
* AI-powered system analysis via Llama 3.1 8B
* JSON snapshots + Markdown reports
* Snapshot comparison & change detection

### **Execution Modes**

```bash
# Local system analysis
/opt/spider/spider/main.py --scan --analyze

# Remote + local analysis
/opt/spider/spider/main.py --scan --remote --analyze

# Continuous monitoring daemon
/opt/spider/spider/main.py --daemon

# Snapshot comparison
/opt/spider/spider/main.py --compare
```

---

## 🏠 Smart Home Devices

* **Ecobee Smart Thermostat Essential** – Integrated with HA
* **GE Cync A19 Matter Light (porch)** – Integrated with HA
* **Wyze Smart Outlet (night light)** – Integrated with HA
* **Reolink Battery Doorbell 2K** – Installed, integration pending

Planned: **ESP32-C3 + RF transmitters** for Jofois ceiling fans.

---

## 🌐 Network Infrastructure

* **ISP:** Google Fiber (1 Gigabit)
* **Topology:** Fiber Jack → Google Fiber Router → TP-Link Omada Switch
* **Current Hardware:**

  * TP-Link Omada 5-port Gigabit switch (default config)
  * TP-Link USB-C Gigabit adapter (Sanctum)
* **Planned:** Cat-6 cabling (6x), VLAN segmentation

---

## 📊 Monitoring & AI Stack

* **Ollama (Llama 3.1 8B)** – AI-powered analysis
* **Spider Intelligence** – System monitoring & diagnostics
* **Prometheus + Grafana** – Installed, pending configuration
* **AdGuard Home** – Installed, pending configuration

---

## 🧠 Spider Development Roadmap (1 Month)

### **Week 1: System Memory Integration**

* OSQuery integration
* Full file crawling & indexing
* Knowledge graph storage (JSON/SQLite)

### **Week 2: Natural Language Interface**

* Gradio web UI (chat interface)
* Context-aware query processing
* Conversational memory & history

### **Week 3: Expert Diagnostics**

* Pattern recognition for homelab issues
* Cross-system correlation (Sanctum ↔ Fathom)
* Step-by-step fix generation

### **Week 4: Learning & Optimization**

* Solution success/failure tracking
* Performance tuning & caching
* Final UI polish + testing

---

## ✅ Current Status Summary

* **Sanctum:** Control hub w/ HA, VPN, monitoring (partially configured)
* **Fathom:** Active AI server w/ Spider + Minecraft
* **Haven:** Available for future NAS/media deployment
* **Smart Home:** 3/4 devices integrated into HA
* **Network:** Gigabit with mesh VPN (Tailscale)
* **Spider:** Active monitoring with AI insights

---

## 🛠️ Known Issues

* **Fathom RAM:** Manual XMP config required (bootloop on auto)
* **Reolink Doorbell:** Login/setup issues with HA

---

## 🛒 Shopping List (Priority)

1. Troubleshoot Reolink integration
2. ESP32-C3 + RF modules (\~\$20)
3. Cat-6 Ethernet cables (\~\$25)
4. 32GB DDR4 RAM for Fathom (\~\$120)
5. RAM upgrade for Haven (\~\$60–120)
6. Storage drives for Haven expansion

---

## 📈 Benefits of Spider Integration

* Centralized AI-powered monitoring
* Predictive analytics & capacity planning
* Automated system health reports
* Expert-level diagnostics & solutions
* Cross-system correlation for deeper insights

---

## 📌 Access Dashboard

| Service             | URL                                                        | System  | Status       |
| ------------------- | ---------------------------------------------------------- | ------- | ------------ |
| CasaOS Dashboard    | [http://sanctum.local](http://sanctum.local)               | Sanctum | Active       |
| Home Assistant      | [http://sanctum.local:8123](http://sanctum.local:8123)     | Sanctum | Active       |
| AdGuard Home        | [http://sanctum.local:\[port](http://sanctum.local:[port)] | Sanctum | Needs Config |
| Grafana             | [http://sanctum.local:\[port](http://sanctum.local:[port)] | Sanctum | Needs Config |
| Crafty Controller   | [http://fathom.local:8080](http://fathom.local:8080)       | Fathom  | Active       |
| Spider Intelligence | Terminal / SSH Access                                      | Fathom  | Active       |

---

## 🚀 End Goal

In 4 weeks, Spider will evolve into a **production-ready expert sysadmin**, capable of:

* Perfect memory of all files & relationships
* Natural language conversation about system health
* Automated diagnostics & solutions for 80%+ of issues
* Continuous learning from past fixes
* Optimized performance & intelligent monitoring
