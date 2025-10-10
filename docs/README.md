# Spider Homelab Intelligence System

## Overview

Spider is an AI-powered homelab monitoring and diagnostic system designed to intelligently manage, scan, analyze, and report on the state of a distributed home infrastructure. It provides expert diagnostics, recommendations, and visibility into system health across compute, networking, and storage nodes.

## Features

* Real-time monitoring of system health
* Automated scanning and anomaly detection
* AI-driven diagnostic recommendations
* Log collection and structured reporting
* Homelab resource inventory tracking
* Configurable alerts and notifications

## Installation

```bash
# clone repository
git clone https://github.com/yourusername/spider.git
cd spider

# create virtual environment
uv venv python3.10

# activate venv
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

## Homelab Hardware

* **Sanctum**: Dell Precision 5520 laptop running Linux (Home Assistant hub)
* **Fathom**: Ryzen 7 3700X / RTX 3060 AI workstation for compute-intensive tasks
* **Haven**: planned TrueNAS storage server

## Usage

Run Spider via the CLI orchestrator:

```bash
python orchestrate.py --scan all
```

Example scan options:

* `--scan network`
* `--scan storage`
* `--scan compute`

## Roadmap

* [ ] System integration with Home Assistant
* [ ] Expanded AI diagnostics
* [ ] Grafana dashboard support
* [ ] Automated remediation routines
* [ ] Discord/Matrix bot notifications

## Integrations

* **Grafana**: for data visualization and dashboards
* **Home Assistant**: for smart home integration
* **Discord/Matrix**: for alerting and notifications

## Shopping List (Upcoming Hardware)

* TrueNAS components for Haven storage node
* Additional network switches/APs
* Smart sensors for environment monitoring
