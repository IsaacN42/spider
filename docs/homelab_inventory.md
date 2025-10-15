# Complete Homelab System & Device Inventory

## Core Systems

### Sanctum (Dell Precision 5520 - Control Hub)
**Role**: Central control and orchestration hub, smart home coordination

**Hardware**:
- **CPU**: Intel Core i7-7820HQ (4C/8T, 2.90-3.90 GHz, 8MB cache, 45W TDP)
- **GPU**: NVIDIA Quadro M1200 4GB GDDR5 (backup AI tasks)
- **RAM**: 16GB DDR4-2400MHz (1x16GB, Non-ECC)
- **Storage**: 512GB M.2 PCIe NVMe SSD (Toshiba XG4, Class 40)
- **Display**: 15.6" UltraSharp UHD (3840x2160) Touchscreen IGZO Panel
- **Network**: 
  - Intel 8265 Wi-Fi (802.11ac, 2x2) + Bluetooth 4.2
  - TP-Link USB-C Gigabit Ethernet Adapter → Omada Switch
- **Power**: 97Wh 6-cell Li-Ion battery + 130W AC adapter

**Operating System**: Ubuntu 24.04.3 LTS + CasaOS frontend

**Services (Active)**:
- Home Assistant OS (KVM VM) - smart home hub
- AdGuard Home (port 3001) - DNS filtering/ad blocking
- Grafana (port 3003) - visualization and dashboards
- Tailscale - VPN mesh networking
- Prometheus - system monitoring (needs configuration)

**Access**: http://192.168.1.254 (CasaOS dashboard)

**Spider Monitoring**: Remote scanning via SSH (CasaOS-aware)

---

### Fathom (Custom Build - AI/Gaming Workhorse)
**Role**: AI processing, Oracle research system, Minecraft hosting, Spider primary host

**Hardware**:
- **Case**: Dell Inspiron 3847 (reused ATX mid-tower)
- **Motherboard**: ASRock B550M Phantom Gaming 4 (AMD, Gigabit Ethernet)
- **CPU**: AMD Ryzen 7 3700X (8C/16T, 3.6-4.4 GHz, 95W TDP, AMD Stealth Cooler)
- **Thermal Paste**: Corsair TM50 High Performance
- **GPU**: NVIDIA RTX 3060 12GB GDDR6 (AI inference + gaming)
- **RAM**: 16GB Corsair Vengeance DDR4-3200MHz (2x8GB, XMP enabled)
  - **Note**: Requires manual XMP configuration (auto settings cause bootloop)
  - **Planned**: Upgrade to 32GB DDR4-3200MHz for Oracle expansion
- **PSU**: 700W 80+ (adequate for current workload)
- **Storage**:
  - 256GB Samsung PM981a NVMe M.2 SSD (boot drive)
  - 1TB HDD + 2TB HDD (LVM group for data storage)

**Operating System**: Ubuntu Server 24.04

**Services (Active)**:
- **Spider Intelligence System** - comprehensive homelab monitoring
- **Ollama** - Llama 3.1 8B model for AI analysis
- **Crafty Controller** - Minecraft server (Homestead modpack, ~350 mods)
- **Oracle Research System** (in development) - autonomous AI researcher

**Access**: 
- SSH: `fathom.local`
- Crafty: http://fathom.local:8080

**Spider Monitoring**: Primary host (local scanning + remote coordination)

---

### Haven (Dell XPS 8900 - Future Storage/Media Server)
**Role**: Future NAS expansion, media server, backup services

**Hardware**:
- **CPU**: Intel Core i5-6400 (6th Gen Skylake, 2.7-3.3 GHz, 4C/4T, 65W)
- **GPU**: NVIDIA GeForce GTX 745 4GB DDR3 (hardware transcoding)
- **RAM**: 8GB DDR4-2133MHz (2x4GB) - *upgrade recommended to 16-32GB*
- **Storage**: 1TB HDD 7200 RPM + expansion bays available
- **Network**: Dell DW1801 WiFi + Bluetooth 4.0 + Integrated Gigabit Ethernet

**Operating System**: Not yet deployed

**Planned Services**:
- TrueNAS or similar NAS solution
- Plex/Jellyfin media server
- Backup target for Sanctum and Fathom

**Spider Monitoring**: Ready for deployment (SSH access configured)

---

## Smart Home Devices

### Integrated Devices (Home Assistant)
- **(1x) Ecobee Smart Thermostat Essential** - **ACTIVE**
  - Connected to Home Assistant + native Ecobee app
  - Eco+ features enabled for power management
  - Smart scheduling operational
  
- **(1x) GE Cync A19 Matter Light** - **ACTIVE**
  - Location: Front porch
  - Matter protocol integration
  - Automation: front porch light schedule
  
- **(1x) Wyze Smart Outlet** - **ACTIVE**
  - Connected device: Night light
  - Automation: night light schedule

### Pending Integration
- **(1x) Reolink Battery Doorbell Smart 2K** - **INSTALLED**
  - Hardware installed, integration troubleshooting in progress
  - 2K resolution, battery powered

### Planned Smart Control
- **(5x) Jofois Ceiling Fans** - **INSTALLED**
  - Current: Battery-powered RF remotes
  - Planned: ESP32-C3 with RF transmitter for unified control
  - Will preserve physical remote functionality
  - Future Home Assistant integration

---

## Network Infrastructure

### Internet & Core Networking
- **ISP**: Google Fiber (1 Gigabit)
- **Router**: Google Fiber Router
- **Managed Switch**: TP-Link Omada 5-Port Gigabit
  - Connected: Sanctum (via USB-C adapter), Fathom (direct)
  - Status: Hardware deployed, default configuration
  - Planned: VLAN segmentation, monitoring config

### Network Topology
```
Fiber Jack → Google Fiber Router → TP-Link Omada Switch
                                        ├── Sanctum (USB-C Ethernet)
                                        ├── Fathom (direct Gigabit)
                                        └── Haven (future)
```

### Network Services
- **DNS Filtering**: AdGuard Home (Sanctum)
- **VPN**: Tailscale mesh network (all systems)
- **Monitoring**: Prometheus + Grafana (Sanctum)

### Planned Network Hardware
- Cat-6 Ethernet Cables (6x) for permanent cable runs

---

## Spider Integration Architecture

### Deployment
- **Primary Host**: Fathom
- **Installation Path**: `/home/abidan/spider/`
- **User**: `spider` (dedicated system user with sudo privileges)
- **Python Environment**: `/home/abidan/.venv/`

### Monitoring Coverage

**Fathom (Local)**:
- Complete filesystem and system scanning
- Docker container health monitoring
- GPU utilization (RTX 3060)
- Ollama service status
- Crafty/Minecraft server performance

**Sanctum (Remote via SSH)**:
- CasaOS-aware monitoring
- KVM VM health (Home Assistant)
- Docker container analysis
- System metrics and service status

**Haven (Remote via SSH - Future)**:
- Storage analysis and capacity planning
- Media server health monitoring
- NAS metrics and performance

### Spider Capabilities
- **AI-Powered Analysis**: Llama 3.1 8B health assessments
- **Predictive Analytics**: Storage trends, capacity planning
- **Change Detection**: Snapshot comparison and anomaly identification
- **Security Assessment**: Network and service posture evaluation
- **Cross-System Correlation**: Understanding Sanctum ↔ Fathom interactions

### Data Storage
```
spider/
├── logs/
│   ├── snapshots/     # JSON system state captures
│   │   └── fathom_YYYYMMDD_HHMMSS.json
│   │   └── sanctum_YYYYMMDD_HHMMSS.json
│   └── reports/       # AI-generated markdown reports
│       └── health_report_YYYYMMDD.md
└── config/
    └── spider_config.yml
```

---

## Service Access Dashboard

| Service | URL | System | Status |
|---------|-----|--------|--------|
| CasaOS Dashboard | http://192.168.1.254 | Sanctum | **ACTIVE** |
| Home Assistant | http://192.168.1.254:8123 | Sanctum | **ACTIVE** |
| AdGuard Home | http://192.168.1.254:3001 | Sanctum | **ACTIVE** |
| Grafana | http://192.168.1.254:3003 | Sanctum | **ACTIVE** |
| Crafty Controller | http://fathom.local:8080 | Fathom | **ACTIVE** |
| Spider Intelligence | Terminal/SSH | Fathom | **ACTIVE** |

---

## Current Issues & Notes

### Hardware Issues
- **Fathom RAM**: XMP profile requires manual BIOS configuration to avoid bootloop
- **Reolink Doorbell**: Login/setup issues preventing Home Assistant integration

### Integration Status
- ✅ **Spider**: Production monitoring on Fathom + Sanctum
- ✅ **Smart Home**: 3/4 devices integrated with Home Assistant
- ✅ **Network Services**: DNS, VPN, monitoring operational
- 🔧 **Prometheus/Grafana**: Installed but needs configuration
- 🔧 **TP-Link Omada**: Default config, needs VLAN setup
- ⏳ **Haven**: Hardware available, deployment pending

---

## Shopping List - Priority Order

### Immediate Needs
1. Troubleshoot Reolink doorbell integration (no purchase)
2. ESP32-C3 + RF transmitter modules for ceiling fan control (~$20)

### Network Infrastructure
3. Configure TP-Link Omada switch (VLANs, monitoring)
4. Cat-6 Ethernet Cables (6x 10ft) (~$25)

### System Expansion
5. 32GB DDR4-3200MHz RAM for Fathom (~$120) - Oracle research expansion
6. RAM upgrade for Haven 16-32GB (~$60-120) - when deployed
7. Additional storage drives for Haven NAS expansion

---

## Workload Distribution

### Current State
- **Sanctum**: Control hub + monitoring + smart home (optimal load)
- **Fathom**: Spider + AI analysis + Minecraft server (good utilization)
- **Haven**: Available for future deployment

### Resource Allocation Philosophy
Spider and Oracle systems are designed to be **resource-aware**:
- Idle time: Full AI research and system analysis
- Gaming active: Prioritize Minecraft, minimal monitoring
- Voice commands: Real-time priority, instant response

---

## Intelligence Benefits

Spider provides:
- **Centralized Monitoring**: Single AI-powered view of entire homelab
- **Proactive Detection**: Identify issues before they become critical
- **Automated Documentation**: Self-updating system inventory
- **Predictive Maintenance**: Capacity planning and trend analysis
- **Cross-System Intelligence**: Understand how systems interact
- **Oracle Integration**: Factual foundation for conversational AI queries

This homelab features comprehensive AI-powered intelligence with Spider providing deep system insights and Oracle (in development) adding conversational interaction and autonomous research capabilities.
