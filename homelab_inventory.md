# Complete Homelab System & Device Inventory

## **Core Systems**

### **Sanctum (Precision Laptop - Control Hub)**
- **Hardware:** Dell Precision 5520 laptop
  - **CPU:** Intel Core i7-7820HQ (4C/8T, 2.90-3.90 GHz, 8MB cache, 45W TDP)
  - **GPU:** NVIDIA Quadro M1200 4GB GDDR5 (backup AI tasks)
  - **RAM:** 16GB DDR4-2400MHz (1x16GB, Non-ECC)
  - **Storage:** 512GB M.2 PCIe NVMe SSD (Toshiba XG4, Class 40)
  - **Display:** 15.6" UltraSharp UHD (3840x2160) Touchscreen IGZO Panel
  - **Connectivity:** Thunderbolt 3 (USB-C), HDMI, 2x USB 3.0, SD Card Reader
  - **Network:** Intel 8265 Wi-Fi (802.11ac, 2x2) + Bluetooth 4.2 + **TP-Link USB-C Gigabit Ethernet Adapter**
  - **Power:** 97Wh 6-cell Li-Ion battery + 130W AC adapter
- **OS:** Ubuntu Server + CasaOS frontend - **DEPLOYED**
- **Role:** Central control and orchestration hub
- **Status:** **ACTIVE - Primary control plane (services need configuration)**
- **Services (deployed):**
  - **Home Assistant OS** (smart home hub) - **DEPLOYED as KVM VM**
  - **Tailscale** (VPN mesh networking) - **DEPLOYED & CONFIGURED**
- **Services (installed but not configured):**
  - **AdGuard Home** (DNS filtering/ad blocking) - **INSTALLED**
  - **Prometheus** (monitoring) - **INSTALLED** 
  - **Grafana** (visualization) - **INSTALLED**
- **Access:** http://sanctum.local (CasaOS dashboard)

### **Fathom (Custom Build - AI/Gaming Workhorse)**
- **Hardware:**
  - **Case:** Dell Inspiron 3847 case (reused ATX mid-tower)
  - **Motherboard:** ASRock B550M Phantom Gaming 4 (AMD) - **Gigabit Ethernet**
  - **CPU:** AMD Ryzen 7 3700X (8C/16T, 95W TDP) with AMD Stealth Cooler
  - **Thermal Paste:** Corsair TM50 High Performance Thermal Paste
  - **GPU:** RTX 3060 12GB (primary AI inference & gaming)
  - **RAM:** **16GB Corsair Vengeance DDR4-3200MHz (2x8GB) - XMP Profile Enabled**
    - **Configuration Note:** Manual speed setting required (auto settings cause bootloop)
    - **Running Speed:** 3200MHz as rated
    - **Planned Upgrade:** 32GB DDR4-3200MHz (for Oracle AI Research System)
  - **PSU:** 700W 80+ (adequate for current workload)
  - **Storage:** 
    - 256GB NVMe SSD (boot drive)
    - 1TB HDD + 2TB HDD (LVM group for data storage)
- **OS:** Ubuntu Server - **DEPLOYED**
- **Role:** AI processing, Minecraft hosting, heavy compute tasks, system intelligence, future Oracle AI research platform
- **Status:** **ACTIVE - AI and Gaming Server**
- **Services (deployed):**
  - **Crafty Controller** - Homestead modpack server (~350 mods) - **DEPLOYED**
  - **Ollama** - Llama 3.1 8B model for system analysis - **DEPLOYED**
  - **Spider Intelligence System** - Comprehensive homelab monitoring - **DEPLOYED**
- **Future Services (planned):**
  - **Oracle AI Research Framework** - Autonomous AI research system - **IN PLANNING**
- **Performance:** Single player optimized, multiplayer capable

### **Haven (Future Storage/Media Server)** 
- **Hardware:** Dell XPS 8900 desktop
  - **CPU:** Intel Core i5-6400 (6th Gen Skylake, 2.7-3.3 GHz, 4C/4T, 65W)
  - **GPU:** NVIDIA GeForce GTX 745 4GB DDR3 (hardware transcoding)
  - **RAM:** 8GB DDR4-2133MHz (2x4GB) - *upgrade recommended*
  - **Storage:** 1TB HDD 7200 RPM + expansion bays available
  - **Network:** Dell DW1801 WiFi + Bluetooth 4.0 + **Integrated Gigabit Ethernet**
- **OS:** Not yet deployed
- **Role:** Future media server, NAS expansion, backup services, Spider remote monitoring target
- **Status:** **Available but not currently deployed**

## **Spider Intelligence System Integration**

### **Deployment Architecture**
- **Primary Host:** Fathom (spider host)
- **Installation Path:** `/opt/spider/`
- **User:** `spider` (dedicated system user with sudo privileges)
- **Python Environment:** Virtual environment at `/opt/spider/venv/`

### **Spider Services (Fathom) - DEPLOYED**
- **Core Engine:** `/opt/spider/spider/main.py` - **ACTIVE**
  - **Local Scanning:** Filesystem, disk, network, Docker monitoring
  - **Remote Scanning:** SSH-based monitoring of Sanctum and future Haven
  - **Command Execution:** Whitelisted sudo commands for system analysis
  - **Data Storage:** JSON snapshots in `/opt/spider/logs/snapshots/`

- **AI Analysis Engine:** Ollama + Llama 3.1 8B integration - **ACTIVE**
  - **ZimaOS Intelligence:** Domain-specific knowledge for Sanctum analysis
  - **Health Assessment:** Rule-based + AI-powered system analysis
  - **Report Generation:** Markdown reports in `/opt/spider/logs/reports/`
  - **Snapshot Comparison:** Change detection and trend analysis

- **Monitoring Capabilities:**
  - **Sanctum (ZimaOS):** Remote SSH scanning with ZimaOS-specific awareness
  - **Fathom (Local):** Comprehensive local system analysis
  - **Haven (Future):** Ready for deployment when Haven comes online

### **Spider Remote Targets**
- **Sanctum:** SSH-based remote scanning - **CONFIGURED**
  - **Detection:** Ubuntu Server + CasaOS frontend
  - **Monitoring:** System health, service status, KVM VM monitoring
  - **Services:** Docker container analysis, system metrics
  - **Access:** SSH key authentication via `spider` user

- **Haven:** Future remote scanning target - **READY**
  - **Preparation:** SSH access configured for when Haven is deployed
  - **Detection:** Will auto-detect Ubuntu/Debian server type
  - **Monitoring:** Storage analysis, media server health, NAS metrics

## **Smart Home Devices**

### **Currently Deployed & Integrated**
- **(1x) Ecobee Smart Thermostat Essential** - **INSTALLED & INTEGRATED**
  - **Status:** Connected to Home Assistant, using Ecobee app scheduling
  - **Integration:** Home Assistant + native Ecobee eco schedule
  - **Power Management:** Eco+ features enabled for reduced power usage
  - **Spider Monitoring:** Indirectly monitored via Home Assistant container analysis

- **(1x) GE Cync A19 Matter Light** - **INSTALLED & INTEGRATED**
  - **Location:** Front porch
  - **Status:** Connected to Home Assistant via Matter
  - **Automation:** Front porch light automation active

- **(1x) Wyze Smart Outlet** - **INSTALLED & INTEGRATED**
  - **Connected Device:** Night light
  - **Status:** Connected to Home Assistant
  - **Automation:** Night light automation active

- **(1x) Reolink Battery Doorbell Smart 2K** - **INSTALLED - INTEGRATION PENDING**
  - **Status:** Hardware installed, login/setup issues preventing HA integration
  - **Features:** 2K resolution, battery powered
  - **Integration:** Troubleshooting in progress

## **AI & Intelligence Services**

### **Current AI Stack (Fathom) - DEPLOYED**
- **Ollama:** Local LLM hosting - **ACTIVE**
  - **Model:** Llama 3.1 8B (optimized for system analysis)
  - **Integration:** Spider Intelligence System + legacy system crawler
  - **Purpose:** Comprehensive homelab monitoring and analysis

### **Spider AI Capabilities - ACTIVE**
- **System Health Analysis:** AI-powered assessment of system metrics
- **ZimaOS Expertise:** Domain knowledge for Sanctum's unique filesystem behavior
- **Predictive Analytics:** Storage capacity planning and performance trends
- **Change Detection:** Snapshot comparison with intelligent change analysis
- **Security Assessment:** Network and service security posture evaluation
- **Optimization Recommendations:** AI-generated system improvement suggestions

### **Gaming Server (Fathom) - DEPLOYED**
- **Crafty Controller:** Minecraft server management - **ACTIVE**
  - **Server:** Homestead modpack (~350 mods)
  - **Configuration:** Single player optimized, multiplayer ready
  - **Performance:** Heavy modpack running smoothly on Ryzen 7 3700X + 16GB RAM
  - **Spider Integration:** Docker containers monitored by Spider system

## **Network Services Architecture**

### **DNS & Security (Sanctum) - NEEDS CONFIGURATION**
- **AdGuard Home:** Network-wide ad blocking and DNS filtering - **INSTALLED**
  - **Status:** Service installed via CasaOS but not configured
  - **Next Step:** Configure DNS settings and filtering rules

### **VPN & Remote Access (Sanctum) - DEPLOYED**
- **Tailscale:** Zero-config VPN mesh networking - **ACTIVE**
  - **Status:** Configured and operational
  - **Integration:** Also installed on Home Assistant OS VM
  - **Network:** Mesh network operational

### **Monitoring (Sanctum) - NEEDS CONFIGURATION**
- **Prometheus:** System monitoring - **INSTALLED**
  - **Status:** Service installed via CasaOS but not configured
  - **Next Step:** Configure data sources and retention
- **Grafana:** Visualization and dashboards - **INSTALLED**
  - **Status:** Service installed via CasaOS but not configured  
  - **Next Step:** Configure dashboards and Prometheus integration

### **Smart Home Control (Sanctum) - DEPLOYED**
- **Home Assistant OS:** Smart home automation hub - **ACTIVE**
  - **Deployment:** KVM VM on Ubuntu Server
  - **Integrated Devices:** Ecobee thermostat, GE Cync light, Wyze outlet
  - **Pending Integration:** Reolink doorbell (technical issues)
  - **Automations:** Front porch light, night light
  - **Network:** Tailscale integration for remote access
  - **Spider Monitoring:** VM monitored via remote scanning

## **System Intelligence & Monitoring**

### **Spider Execution Modes - AVAILABLE**
```bash
# Local system analysis
/opt/spider/spider/main.py --scan --analyze

# Remote + local comprehensive scan
/opt/spider/spider/main.py --scan --remote --analyze

# Continuous monitoring daemon
/opt/spider/spider/main.py --daemon

# Snapshot comparison
/opt/spider/spider/main.py --compare

# Component testing
/opt/spider/test_spider.sh
```

### **Spider Data Architecture**
- **Snapshots:** `/opt/spider/logs/snapshots/` - Raw JSON system data
- **Reports:** `/opt/spider/logs/reports/` - AI-generated analysis reports
- **Configuration:** `/opt/spider/config/spider_config.yml`

### **Monitoring Coverage**
- **Fathom (Local):** Complete system scanning and analysis
- **Sanctum (Remote):** ZimaOS-aware monitoring via SSH
- **Network Services:** Docker container health and performance
- **Storage Systems:** Disk usage trends and capacity planning
- **AI Health:** Ollama service monitoring and model performance

## **Network Infrastructure**

### **Current Network Setup**
- **Primary Internet:** Google Fiber (1 Gigabit) → Fiber Jack → Google Fiber Router
- **Network Topology:**
  ```
  Fiber Jack → Google Fiber Router → TP-Link Omada Switch
                                          ├── Sanctum (via TP-Link USB-C Ethernet Adapter)
                                          └── Fathom (direct Gigabit Ethernet)
  ```
- **Managed Switch:** TP-Link Omada 5-Port Gigabit (default configuration)
- **Mesh VPN:** Tailscale connecting all services and enabling Spider remote access
- **DNS Filtering:** AdGuard Home providing network-wide ad blocking
- **SSH Access:** Secure key-based authentication for Spider remote monitoring

### **Current Network Hardware**
- **(1x) TP-Link Omada 5-Port Gigabit Managed Switch** - **DEPLOYED**
  - **Status:** Hardware installed, running default configuration
  - **Connected Devices:** Sanctum (via USB-C adapter), Fathom (direct), uplink to Google Fiber router
  - **Management:** Not yet configured (using default settings)
  - **Next Step:** Configure VLANs, monitoring, and network segmentation
- **(1x) TP-Link USB-C Gigabit Ethernet Adapter** - **DEPLOYED**
  - **Connected to:** Sanctum (Precision 5520 laptop)
  - **Purpose:** Provides wired Gigabit connectivity for control hub
  - **Performance:** Full Gigabit speeds to managed switch

### **Future Network Hardware (Not Yet Purchased)**
- **(6x) Cat-6 Ethernet Cables** - **PLANNED**

## **Ceiling Fan Smart Control System**

### **Existing Hardware**
- **(5x) Jofois Ceiling Fans** - **INSTALLED**
  - **Current Control:** Battery-powered RF remotes
  - **Features:** Multiple speeds, light dimming, directional control, timers

### **Smart Control Implementation (Planned)**
- **Approach:** Single ESP32-C3 with RF transmitter modules
- **Method:** Reverse engineer RF protocol, broadcast to all fans
- **Benefits:** 
  - Preserve all existing remote functionality
  - Physical remotes continue to work
  - Central control via Home Assistant
  - Cost-effective solution (~$20 total hardware)
- **Spider Integration:** ESP32 device will be monitored once deployed

## **Access Dashboard Summary**

| Service | URL | System | Purpose | Status |
|---------|-----|---------|---------|---------|
| CasaOS Dashboard | http://sanctum.local | Sanctum | System management | **ACTIVE** |
| **Home Assistant** | **http://sanctum.local:8123** | **Sanctum** | **Smart home control** | **ACTIVE** |
| **AdGuard Home** | **http://sanctum.local:[port]** | **Sanctum** | **DNS filtering** | **INSTALLED - NEEDS CONFIG** |
| **Grafana** | **http://sanctum.local:[port]** | **Sanctum** | **System monitoring** | **INSTALLED - NEEDS CONFIG** |
| **Crafty Controller** | **http://fathom.local:8080** | **Fathom** | **Minecraft management** | **ACTIVE** |
| **Spider Intelligence** | **Terminal/SSH Access** | **Fathom** | **AI system monitoring** | **ACTIVE** |

## **System Issues & Notes**

### **🔧 Current Hardware Issues:**
- **Fathom RAM:** Corsair Vengeance DDR4-3200 requires manual speed setting
  - **Issue:** Auto memory settings cause bootloop
  - **Solution:** XMP profile manually enabled, running at rated 3200MHz
  - **Status:** Stable operation with manual configuration

### **🔧 Current Integration Issues:**
- **Reolink Doorbell:** Login/setup issues preventing Home Assistant integration

## **Current Status Summary**

### **✅ Successfully Deployed & Operational:**
- **Sanctum:** ZimaOS with full service stack + Spider remote monitoring
- **Fathom:** AI stack (Ollama + Spider Intelligence), Minecraft server, 16GB @ 3200MHz
- **Spider System:** Comprehensive homelab intelligence with AI analysis
- **Smart Home:** 3/4 devices integrated with Home Assistant
- **Automations:** Front porch light and night light automations active
- **Network Services:** DNS filtering, monitoring, VPN mesh, intelligent system analysis

### **🧠 Intelligence Capabilities:**
- **AI-Powered Analysis:** Llama 3.1 8B model analyzing system health
- **ZimaOS Expertise:** Domain knowledge for Sanctum's unique behavior
- **Multi-System Monitoring:** Local + remote scanning via SSH
- **Predictive Analytics:** Storage trends, performance analysis, failure prediction
- **Automated Reports:** Markdown reports with health status and recommendations

### **🛒 Shopping List - Priority Order:**

#### **Immediate (Fix Current Issues):**
1. **Troubleshoot Reolink doorbell integration** - no purchase needed
2. **ESP32-C3 + RF transmitter modules** - ~$20 (for fan control)

#### **Network Infrastructure:**
3. **Configure TP-Link Omada switch** - VLANs, monitoring, network segmentation
4. **Cat-6 Ethernet Cables (6x 10ft)** - ~$25

#### **System Expansion:**
5. **32GB DDR4-3200MHz RAM upgrade for Fathom** - ~$120 (for Oracle AI Research Framework)
6. **RAM upgrade for Haven** - 16-32GB DDR4 - ~$60-120
7. **Additional storage drives** - for NAS expansion on Haven

### **🎯 Current Workload Distribution:**
- **Sanctum:** Control hub + monitoring + smart home coordination (optimal load)
- **Fathom:** AI processing + Spider Intelligence + heavy modded Minecraft (good utilization)
- **Haven:** Available for future deployment (will be Spider remote target)

### **⚡ Next Steps:**
1. **Resolve Reolink doorbell integration** with Home Assistant
2. **Design and build RF fan control system** for 5 Jofois fans  
3. **Configure TP-Link Omada switch** for proper network segmentation
4. **Deploy network infrastructure** (ethernet cable runs)
4. **Plan Haven deployment** for media server with Spider monitoring
5. **Expand Spider capabilities** with additional AI models or analysis features

## **Spider Integration Benefits**

### **Enhanced Homelab Intelligence:**
- **Centralized Monitoring:** Single AI-powered system monitoring entire homelab
- **Proactive Issue Detection:** AI analysis identifies problems before they become critical
- **ZimaOS Expertise:** Specialized knowledge prevents false alarms on Sanctum
- **Automated Documentation:** Self-updating system inventory and health reports
- **Predictive Maintenance:** Capacity planning and performance trend analysis

### **Operational Improvements:**
- **Reduced Manual Monitoring:** Spider automates routine system checks
- **Intelligent Alerting:** AI-powered analysis reduces noise, highlights real issues
- **Cross-System Correlation:** Understanding how Sanctum and Fathom interact
- **Future-Ready:** Haven integration ready for when deployed
- **Extensible Architecture:** Easy to add new systems and analysis capabilities

This homelab now features comprehensive AI-powered intelligence with the Spider system providing deep insights into system health, predictive analytics, and automated monitoring across all deployed systems. The integration creates a truly intelligent infrastructure that can self-monitor and provide actionable insights for optimization and maintenance.