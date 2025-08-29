#!/usr/bin/env python3
# spider/scanners/docker.py

"""
spider docker scanner
scans docker containers, images, networks, and volumes
"""

import sys
import os
import json
from datetime import datetime

# add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from executor.command_executor import CommandExecutor

def scan_docker_containers():
    """scan running docker containers"""
    executor = CommandExecutor()
    result = {
        'scan_time': datetime.now().isoformat(),
        'containers': [],
        'images': []
    }
    
    # get containers
    ps_result = executor.run_command('docker ps -a --format "{{.Names}},{{.Image}},{{.Status}},{{.Ports}}"')
    if ps_result['returncode'] == 0:
        lines = ps_result['stdout'].strip().split('\n')
        for line in lines:
            if line:
                parts = line.split(',', 3)
                if len(parts) >= 3:
                    result['containers'].append({
                        'name': parts[0],
                        'image': parts[1],
                        'status': parts[2],
                        'ports': parts[3] if len(parts) > 3 else ''
                    })
    
    # get images
    images_result = executor.run_command('docker images --format "{{.Repository}},{{.Tag}},{{.Size}}"')
    if images_result['returncode'] == 0:
        lines = images_result['stdout'].strip().split('\n')
        for line in lines:
            if line:
                parts = line.split(',', 2)
                if len(parts) >= 2:
                    result['images'].append({
                        'repository': parts[0],
                        'tag': parts[1],
                        'size': parts[2] if len(parts) > 2 else ''
                    })
    
    return result

def scan_docker_images():
    """get docker images"""
    return scan_docker_containers()['images']
