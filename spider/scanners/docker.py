#!/usr/bin/env python3
# spider/scanners/docker.py
# scans docker containers, images, networks, and volumes

import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from executor.command_executor import CommandExecutor

def scan_docker_containers():
    """scan docker containers and images"""
    executor = CommandExecutor()
    result = {
        'scan_time': datetime.now().isoformat(),
        'containers': [],
        'images': [],
        'warnings': []
    }
    
    # check docker access
    test_result = executor.run_command('docker ps --help')
    if test_result['returncode'] != 0:
        result['warnings'].append('docker not accessible - add user to docker group or check installation')
        return result
    
    # get containers with full details
    ps_result = executor.run_command('docker ps -a --format "{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}|{{.CreatedAt}}"')
    if ps_result['returncode'] == 0:
        lines = ps_result['stdout'].strip().split('\n')
        for line in lines:
            if line and line.strip():
                parts = line.split('|')
                if len(parts) >= 3:
                    container = {
                        'name': parts[0].strip(),
                        'image': parts[1].strip(),
                        'status': parts[2].strip(),
                        'ports': parts[3].strip() if len(parts) > 3 else '',
                        'created': parts[4].strip() if len(parts) > 4 else ''
                    }
                    
                    # parse uptime from status
                    status_lower = container['status'].lower()
                    if 'up' in status_lower:
                        container['state'] = 'running'
                        # extract uptime
                        if 'hour' in status_lower:
                            hours = status_lower.split('hour')[0].split()[-1]
                            try:
                                if int(hours) > 24:
                                    result['warnings'].append(f"{container['name']} running for {hours}+ hours")
                            except:
                                pass
                    elif 'exited' in status_lower:
                        container['state'] = 'stopped'
                        result['warnings'].append(f"{container['name']} is stopped")
                    else:
                        container['state'] = 'unknown'
                    
                    # parse exposed ports
                    if container['ports']:
                        # extract port ranges
                        port_list = []
                        for port_section in container['ports'].split(','):
                            if '->' in port_section:
                                # external mapping
                                external = port_section.split('->')[0].strip()
                                internal = port_section.split('->')[1].strip()
                                port_list.append(f"{external}→{internal}")
                        container['port_mappings'] = port_list
                    
                    result['containers'].append(container)
    else:
        result['warnings'].append(f"failed to list containers: {ps_result.get('stderr', 'unknown error')}")
    
    # get images
    images_result = executor.run_command('docker images --format "{{.Repository}}|{{.Tag}}|{{.Size}}|{{.CreatedAt}}"')
    if images_result['returncode'] == 0:
        lines = images_result['stdout'].strip().split('\n')
        for line in lines:
            if line and line.strip():
                parts = line.split('|')
                if len(parts) >= 2:
                    result['images'].append({
                        'repository': parts[0].strip(),
                        'tag': parts[1].strip(),
                        'size': parts[2].strip() if len(parts) > 2 else '',
                        'created': parts[3].strip() if len(parts) > 3 else ''
                    })
    else:
        result['warnings'].append(f"failed to list images: {images_result.get('stderr', 'unknown error')}")
    
    # get docker info
    info_result = executor.run_command('docker info --format "{{.ServerVersion}}|{{.ContainersRunning}}|{{.ContainersStopped}}"')
    if info_result['returncode'] == 0:
        parts = info_result['stdout'].strip().split('|')
        if len(parts) >= 3:
            result['docker_info'] = {
                'version': parts[0],
                'running': parts[1],
                'stopped': parts[2]
            }
    
    return result

def scan_docker_images():
    """get docker images only"""
    return scan_docker_containers()['images']

def get_container_stats():
    """get resource usage stats for running containers"""
    executor = CommandExecutor()
    stats = []
    
    stats_result = executor.run_command('docker stats --no-stream --format "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.NetIO}}"')
    if stats_result['returncode'] == 0:
        lines = stats_result['stdout'].strip().split('\n')
        for line in lines:
            if line and line.strip():
                parts = line.split('|')
                if len(parts) >= 3:
                    stats.append({
                        'name': parts[0].strip(),
                        'cpu': parts[1].strip(),
                        'memory': parts[2].strip(),
                        'network': parts[3].strip() if len(parts) > 3 else ''
                    })
    
    return stats