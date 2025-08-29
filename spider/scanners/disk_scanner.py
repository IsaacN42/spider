"""
spider disk scanner
scans storage devices, partitions, and usage
"""

import sys
import os
from datetime import datetime

# add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from executor.command_executor import CommandExecutor

def scan_disks():
    """scan disk information"""
    executor = CommandExecutor()
    result = {
        'scan_time': datetime.now().isoformat(),
        'disks': [],
        'usage': []
    }
    
    # get disk usage
    df_result = executor.run_command('df -h')
    if df_result['returncode'] == 0:
        lines = df_result['stdout'].strip().split('\n')[1:]  # skip header
        for line in lines:
            parts = line.split()
            if len(parts) >= 6:
                result['usage'].append({
                    'filesystem': parts[0],
                    'size': parts[1],
                    'used': parts[2],
                    'available': parts[3],
                    'use_percent': parts[4],
                    'mount_point': parts[5]
                })
    
    # get block devices
    lsblk_result = executor.run_command('lsblk -J')
    if lsblk_result['returncode'] == 0:
        result['lsblk_output'] = lsblk_result['stdout']
    
    return result

def get_disk_usage():
    """get simplified disk usage"""
    return scan_disks()['usage']
