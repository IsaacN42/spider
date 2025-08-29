"""
spider network scanner
scans network interfaces, routing, and connections
"""

import sys
import os
import subprocess
from datetime import datetime

def scan_network_interfaces():
    """scan network interfaces"""
    result = {
        'scan_time': datetime.now().isoformat(),
        'interfaces': [],
        'connections': []
    }
    
    # get interfaces - try without sudo first
    try:
        ip_result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=10)
        if ip_result.returncode == 0:
            result['ip_addr_output'] = ip_result.stdout
        else:
            # fallback to sudo if needed
            ip_result = subprocess.run(['sudo', 'ip', 'addr', 'show'], capture_output=True, text=True, timeout=10)
            if ip_result.returncode == 0:
                result['ip_addr_output'] = ip_result.stdout
    except:
        result['ip_addr_output'] = 'failed to get network interfaces'
    
    # get connections - try without sudo first
    try:
        ss_result = subprocess.run(['ss', '-tuln'], capture_output=True, text=True, timeout=10)
        if ss_result.returncode == 0:
            result['listening_ports'] = ss_result.stdout
        else:
            # fallback to sudo if needed
            ss_result = subprocess.run(['sudo', 'ss', '-tuln'], capture_output=True, text=True, timeout=10)
            if ss_result.returncode == 0:
                result['listening_ports'] = ss_result.stdout
    except:
        result['listening_ports'] = 'failed to get network connections'
    
    return result

def scan_network_connections():
    """get network connections"""
    return scan_network_interfaces()['connections']
