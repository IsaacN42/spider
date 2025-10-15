# Spider Homelab Intelligence System

## Overview
Spider is an AI-powered homelab monitoring and diagnostic system that provides comprehensive visibility, automated analysis, and intelligent recommendations across your distributed home infrastructure.

## Core Purpose
- **System monitoring**: real-time health tracking across all homelab nodes
- **AI diagnostics**: intelligent problem detection and solution recommendations
- **Automated reporting**: structured health reports and trend analysis
- **Cross-system intelligence**: understand relationships between services and systems

## Key Features
- Multi-system remote scanning via SSH (Sanctum, Fathom, Haven)
- Domain-specific knowledge (CasaOS, KVM, Docker environments)
- AI-powered health assessment using Ollama + Llama 3.1 8B
- Snapshot comparison and change detection
- Predictive analytics (storage capacity, performance trends)
- JSON data storage with markdown report generation

## Quick Start

### Installation
```bash
# clone repository
git clone https://github.com/yourusername/spider.git
cd spider

# create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

### Basic Usage
```bash
# local system scan
./bin/spider --scan --analyze

# include remote systems
./bin/spider --scan --remote --analyze

# continuous monitoring
./bin/spider --daemon

# compare snapshots
./bin/spider --compare
```

## Monitored Systems
- **Sanctum**: Dell Precision 5520 laptop (Ubuntu 24.04.3 LTS + CasaOS)
- **Fathom**: Ryzen 7 3700X + RTX 3060 (Ubuntu Server, AI workstation)
- **Haven**: Dell XPS 8900 (future deployment, ready for monitoring)

## Architecture
Spider uses a three-layer architecture:
1. **Scanning layer**: filesystem, docker, network, system metrics
2. **Analysis layer**: AI-powered health assessment and diagnostics
3. **Reporting layer**: JSON snapshots + markdown reports

## Integration
- **Prometheus metrics**: exports for Grafana dashboards on Sanctum
- **SSH remote access**: secure key-based authentication
- **Ollama AI**: local LLM for intelligent analysis
- **Docker awareness**: container health and performance monitoring

## Data Storage
```
spider/
├── logs/
│   ├── snapshots/     # JSON system state captures
│   └── reports/       # AI-generated markdown reports
└── config/
    └── spider_config.yml  # system configuration
```

## Access
- **Primary host**: Fathom (`/home/abidan/spider/`)
- **User**: `spider` (dedicated system user with sudo privileges)
- **Remote targets**: Sanctum, Haven (via SSH)

## Status
**Production**: Active monitoring on Fathom + Sanctum
**Development**: Continuous improvement (see IMPROVEMENT_PLAN.md)

## Documentation
- `ARCHITECTURE.md` - technical implementation details
- `HOMELAB_INVENTORY.md` - complete hardware and service inventory
- `IMPROVEMENT_PLAN.md` - 1-month intensive development roadmap

## Philosophy
Spider is a **silent observer** - it monitors, analyzes, and reports without requiring conversation or interaction. It provides the factual foundation that Oracle (the conversational AI assistant) can query when needed.
