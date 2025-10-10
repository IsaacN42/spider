#!/usr/bin/env python3
# comprehensive spider scan with ai analysis

import sys
from pathlib import Path

# add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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

# show disk warnings
if disks.get('warnings'):
    print("\n⚠️  disk warnings:")
    for warning in disks['warnings']:
        print(f"  - {warning}")

# show docker warnings
if docker.get('warnings'):
    print("\n⚠️  docker warnings:")
    for warning in docker['warnings']:
        print(f"  - {warning}")

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
    'physical_disks': len(disks.get('physical_disks', [])),
    'partitions': len(disks.get('partitions', [])),
    'mounted_filesystems': len(disks.get('mounts', [])),
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
- physical disks: {summary['physical_disks']} detected
- partitions: {summary['partitions']} detected  
- mounted filesystems: {summary['mounted_filesystems']}
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
    analysis = "analysis skipped - ollama not available"
except Exception as e:
    print(f"analysis failed: {e}")
    analysis = f"analysis failed: {e}"

# save results
output_file = project_root / 'data' / 'reports' / f'scan_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
output_file.parent.mkdir(parents=True, exist_ok=True)
with open(output_file, 'w') as f:
    json.dump({
        'scan': scan_data,
        'summary': summary,
        'analysis': analysis
    }, f, indent=2)

print("="*60)
print("✓ FULL SCAN COMPLETE")
print(f"💾 saved to: {output_file}")
print("="*60)