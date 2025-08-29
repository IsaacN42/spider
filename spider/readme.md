# Spider - Homelab Intelligence System

Spider is a comprehensive homelab auditing AI that continuously monitors your infrastructure with root-level visibility. It scans filesystems, network configurations, Docker containers, and system logs to provide intelligent analysis and actionable recommendations.

## Features

- **Full System Visibility**: Root-level access to scan all system components
- **Modular Scanners**: Filesystem, network, Docker, disk usage, logs
- **LLM Analysis**: Intelligent interpretation of system data
- **Historical Tracking**: Compare snapshots over time
- **Safe Operation**: Read-only with whitelisted commands only
- **Continuous Monitoring**: Systemd service for automated scanning

## Architecture

```
Spider Core
├── Scanners (data collection)
│   ├── filesystem_scanner.py    # Config files, logs
│   ├── disk_scanner.py          # Storage, partitions
│   ├── network_scanner.py       # Interfaces, routing
│   └── docker_scanner.py        # Containers, images
├── Executor (safe command execution)
│   └── command_executor.py      # Whitelisted root commands
├── LLM (analysis)
│   └── llm_analyzer.py          # System health analysis
└── Reports (output)
    ├── snapshots/               # JSON scan data
    └── reports/                 # Human-readable analyses
```

## Installation

1. **Run setup script:**
   ```bash
   sudo ./setup_spider.sh
   ```

2. **Copy Python files to `/opt/spider/spider/`:**
   ```bash
   sudo cp -r spider/* /opt/spider/spider/
   ```

3. **Test installation:**
   ```bash
   sudo -u spider /opt/spider/test_spider.sh
   ```

4. **Run manual scan:**
   ```bash
   sudo -u spider /opt/spider/venv/bin/python /opt/spider/spider/main.py --scan
   ```

## Usage

### Manual Scans

```bash
cd /opt/spider

# full system scan
venv/bin/python spider/main.py --scan

# scan specific filesystem path
venv/bin/python spider/main.py --filesystem /etc

# disk usage only
venv/bin/python spider/main.py --disk

# network config only  
venv/bin/python spider/main.py --network

# docker environment only
venv/bin/python spider/main.py --docker

# analyze latest snapshot
venv/bin/python spider/main.py --analyze

# scan and analyze in one command
venv/bin/python spider/main.py --scan --analyze
```

### Systemd Service

```bash
# enable spider service
sudo systemctl enable spider

# start spider service
sudo systemctl start spider

# check status
sudo systemctl status spider

# view logs
journalctl -u spider -f
```

### Output Locations

- **Snapshots**: `/opt/spider/logs/snapshots/` (JSON data)
- **Reports**: `/opt/spider/logs/reports/` (Markdown analyses)
- **Service Logs**: `journalctl -u spider`

## Configuration

Edit `/opt/spider/config/spider_config.yml`:

```yaml
scan_paths:
  - "/etc"
  - "/opt" 
  - "/var/log"

scan_settings:
  max_files_per_path: 1000
  max_file_size: 50000

schedule:
  full_scan_interval: "6h"
  quick_scan_interval: "30m"
```

## Security

Spider operates with these safety measures:

- **Read-only**: Never modifies system files
- **Whitelisted commands**: Only approved commands via sudo
- **Isolated user**: Runs as dedicated `spider` user
- **Limited scope**: Skips dangerous directories (/proc, /sys, /dev)

## Whitelisted Commands

Spider can execute these commands with sudo:
- `df`, `lsblk`, `fdisk` (disk info)
- `journalctl`, `systemctl` (logs/services)
- `docker` (container management)
- `iptables`, `ufw` (firewall)
- `lshw`, `dmidecode` (hardware)
- `powertop`, `lsof` (system analysis)

## Example Output

### CLI Summary
```
[*] running full system scan...
[*] scanning filesystem...
  -> scanning /etc
  -> scanning /opt
[*] scanning disk usage...
[*] scanning network configuration...
[*] scanning docker environment...
[*] snapshot saved: /opt/spider/logs/snapshots/full_scan_20250818_143022.json
[*] analyzing system snapshot...
[*] analysis saved: /opt/spider/logs/reports/analysis_20250818_143022.md

==================================================
SPIDER ANALYSIS
==================================================
# Spider Analysis Report
**Host:** fathom
**Scan Time:** 2025-08-18T14:30:22

**Storage:** 3 filesystems scanned
**Config Files:** 247 configuration files found
**Docker:** 8 containers

## Health Assessment
**Severity:** low
**Issues Found:** 1

### Issues Detected
- moderate disk usage on /: 78%

### Recommendations
- monitor disk usage on /
```

## Development

To extend Spider with new scanners:

1. Create scanner module in `spider/scanners/`
2. Follow the pattern of returning structured dictionaries
3. Add to `__init__.py` imports
4. Update `main.py` to use new scanner
5. Test with `test_spider.sh`

## Troubleshooting

**Permission errors:**
```bash
# check sudoers file
sudo visudo -c
cat /etc/sudoers.d/spider-audit
```

**Module import errors:**
```bash
# check python path and virtual env
/opt/spider/venv/bin/python -c "import sys; print(sys.path)"
```

**Service issues:**
```bash
# check service status
sudo systemctl status spider
journalctl -u spider --no-pager
```

## Integration

Spider can be integrated with:
- **Home Assistant**: For notifications and dashboards
- **Grafana**: Historical metrics and alerting  
- **Discord/Slack**: Alert notifications
- **Email**: Automated reports

## Future Features

- LLM integration (Ollama, GPT-4o) for advanced analysis
- Voice interface via Echo Dot repurposing
- Trend analysis and anomaly detection
- Custom rule engine for specific homelab configs
- API endpoint for external integrations