#!/usr/bin/env python3
# comprehensive spider scan with ai analysis

from spider.scanners.disk import scan_disks
from spider.scanners.docker import scan_docker_containers
from spider.scanners.filesystem import scan_important_configs
import json
import requests
from datetime import datetime

print("\n" + "="*60)
print("RUNNING FULL SPIDER SCAN WITH AI ANALYSIS")
print("="*60 + "\n")

# gather all data
print("scanning system...")
disks = scan_disks()
docker = scan_docker_containers()
configs = scan_important_configs()

# prepare scan data
scan_data = {
    'timestamp': str(datetime.now()),
    'disks': disks,
    'docker': docker,
    'configs': configs
}

# calculate summary
containers = docker.get('containers', [])
running = [c for c in containers if 'Up' in c.get('status', '')]

summary = {
    'total_disks': len(disks.get('usage', [])),
    'total_containers': len(containers),
    'running_containers': len(running),
    'total_images': len(docker.get('images', [])),
    'config_files': len(configs) if isinstance(configs, dict) else 1
}

print(json.dumps(summary, indent=2))
print()

# build dynamic container list for prompt
container_list = []
for c in containers:
    name = c.get('name', 'unknown')
    image = c.get('image', 'unknown')
    status = c.get('status', 'unknown')
    container_list.append(f"  - {name}: {image} ({status})")

container_summary = "\n".join(container_list) if container_list else "  - no containers found"

# ai analysis
print("running ai analysis...")

analysis_prompt = f"""analyze this homelab system scan data. only reference what you see in the data below.

SUMMARY:
- disks: {summary['total_disks']} detected
- containers: {summary['running_containers']}/{summary['total_containers']} running
- docker images: {summary['total_images']}

CONTAINERS FOUND:
{container_summary}

FULL SCAN DATA:
{json.dumps(scan_data, indent=2)}

provide:
1. system health assessment
2. any issues or concerns (only if found in data)
3. optimization recommendations
4. security considerations

be specific and only reference resources present in the scan data."""

try:
    response = requests.post('http://localhost:11434/api/generate', 
        json={
            'model': 'llama3.1:8b',
            'prompt': analysis_prompt,
            'stream': False
        },
        timeout=60
    )
    
    if response.status_code == 200:
        analysis = response.json().get('response', 'no response')
        print("\n" + "="*60)
        print("AI ANALYSIS RESULTS")
        print("="*60)
        print(analysis)
        print()
    else:
        print(f"ollama error: {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("⚠️  ollama not running. start with: ollama serve")
except Exception as e:
    print(f"analysis failed: {e}")

print("="*60)
print("✓ FULL SCAN COMPLETE")
print("="*60)