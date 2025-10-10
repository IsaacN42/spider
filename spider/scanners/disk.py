#!/usr/bin/env python3
# spider/scanners/disk.py
# scans storage devices, partitions, and usage

import sys
import os
import json
from datetime import datetime

# add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from executor.command_executor import CommandExecutor

def scan_disks():
    """scan disk information"""
    executor = CommandExecutor()
    result = {
        'scan_time': datetime.now().isoformat(),
        'physical_disks': [],
        'partitions': [],
        'mounts': [],
        'warnings': []
    }
    
    # check if running as root
    if os.geteuid() != 0:
        result['warnings'].append('running without root - some disk info may be limited')
    
    # get block devices with details
    try:
        lsblk_result = executor.run_command('lsblk -J -o NAME,TYPE,SIZE,MOUNTPOINT,FSTYPE,MODEL')
        if lsblk_result['returncode'] == 0:
            try:
                devices = json.loads(lsblk_result['stdout']).get('blockdevices', [])
                
                for device in devices:
                    if device.get('type') == 'disk':
                        # physical disk
                        disk_info = {
                            'name': device.get('name'),
                            'size': device.get('size'),
                            'model': device.get('model', 'unknown'),
                            'partitions': []
                        }
                        
                        # get partitions for this disk
                        for child in device.get('children', []):
                            partition = {
                                'name': child.get('name'),
                                'size': child.get('size'),
                                'type': child.get('type'),
                                'fstype': child.get('fstype'),
                                'mountpoint': child.get('mountpoint')
                            }
                            disk_info['partitions'].append(partition)
                            result['partitions'].append(partition)
                        
                        result['physical_disks'].append(disk_info)
                    elif device.get('type') in ['part', 'lvm']:
                        # standalone partition or lvm
                        result['partitions'].append({
                            'name': device.get('name'),
                            'size': device.get('size'),
                            'type': device.get('type'),
                            'fstype': device.get('fstype'),
                            'mountpoint': device.get('mountpoint')
                        })
            except json.JSONDecodeError as e:
                result['warnings'].append(f'failed to parse lsblk output: {str(e)}')
        else:
            result['warnings'].append(f'lsblk command failed: {lsblk_result.get("stderr", "unknown error")}')
    except Exception as e:
        result['warnings'].append(f'block device scan failed: {str(e)}')
    
    # get mount point usage
    try:
        df_result = executor.run_command('df -h --output=source,size,used,avail,pcent,target')
        if df_result['returncode'] == 0:
            lines = df_result['stdout'].strip().split('\n')[1:]  # skip header
            for line in lines:
                parts = line.split()
                if len(parts) >= 6:
                    # filter out tmpfs, devtmpfs, etc
                    filesystem = parts[0]
                    if filesystem.startswith(('/dev/', '/mapper/')):
                        mount_info = {
                            'filesystem': filesystem,
                            'size': parts[1],
                            'used': parts[2],
                            'available': parts[3],
                            'use_percent': parts[4],
                            'mount_point': parts[5]
                        }
                        result['mounts'].append(mount_info)
                        
                        # warn on high usage
                        try:
                            usage_pct = int(parts[4].rstrip('%'))
                            if usage_pct > 80:
                                result['warnings'].append(
                                    f'{parts[5]} is {usage_pct}% full ({parts[2]}/{parts[1]})'
                                )
                        except ValueError:
                            pass
        else:
            result['warnings'].append(f'df command failed: {df_result.get("stderr", "unknown error")}')
    except Exception as e:
        result['warnings'].append(f'mount usage scan failed: {str(e)}')
    
    # add storage summary
    result['summary'] = {
        'physical_disk_count': len(result['physical_disks']),
        'partition_count': len(result['partitions']),
        'mounted_filesystem_count': len(result['mounts']),
        'total_warnings': len(result['warnings'])
    }
    
    return result

def get_disk_usage():
    """get simplified disk usage"""
    scan_result = scan_disks()
    return {
        'mounts': scan_result['mounts'],
        'warnings': scan_result['warnings']
    }

def get_storage_summary():
    """get human-readable storage summary"""
    scan = scan_disks()
    
    print("\n" + "="*60)
    print("STORAGE SUMMARY")
    print("="*60 + "\n")
    
    # physical disks
    print(f"Physical Disks: {len(scan['physical_disks'])}")
    for disk in scan['physical_disks']:
        print(f"  📀 {disk['name']}: {disk['size']} ({disk['model']})")
        if disk['partitions']:
            for part in disk['partitions']:
                mount = part.get('mountpoint', 'not mounted')
                print(f"     └─ {part['name']}: {part['size']} - {mount}")
    
    print(f"\nTotal Partitions: {len(scan['partitions'])}")
    print(f"Mounted Filesystems: {len(scan['mounts'])}\n")
    
    # mounted filesystem usage
    print("Filesystem Usage:")
    for mount in scan['mounts']:
        usage = mount['use_percent'].rstrip('%')
        icon = "🔴" if int(usage) > 80 else "🟡" if int(usage) > 60 else "🟢"
        print(f"  {icon} {mount['mount_point']}: {mount['used']}/{mount['size']} ({mount['use_percent']})")
    
    # warnings
    if scan['warnings']:
        print(f"\n⚠️  Warnings ({len(scan['warnings'])}):")
        for warning in scan['warnings']:
            print(f"  - {warning}")
    
    print("\n" + "="*60)
    
    return scan

if __name__ == '__main__':
    get_storage_summary()