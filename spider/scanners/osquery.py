#!/usr/bin/env python3
# spider/scanners/osquery.py

"""
spider osquery scanner
deep system introspection using osquery
"""

import json
import subprocess
import time
import re
from datetime import datetime
from typing import Dict, Any, List
# from prometheus_client import Gauge, Counter

class OSQueryScanner:
    def __init__(self):
        self.osquery_path = "osqueryi"
        
        # prometheus metrics
        self.osquery_queries = Counter('spider_osquery_queries_total', 'osquery queries executed')
        self.osquery_duration = Gauge('spider_osquery_duration_seconds', 'last osquery scan duration')
        self.files_tracked = Gauge('spider_osquery_files_tracked', 'files tracked by osquery')
        
    def check_osquery_installed(self) -> bool:
        """check if osquery is available"""
        try:
            result = subprocess.run([self.osquery_path, "--version"], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def query(self, sql: str) -> List[Dict]:
        """execute osquery sql and return results"""
        self.osquery_queries.inc()
        try:
            cmd = [self.osquery_path, "--json", sql]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            return []
        except Exception as e:
            print(f"osquery error: {e}")
            return []
    
    def scan_critical_file_relationships(self) -> Dict[str, Any]:
        """enhanced file relationships for homelab monitoring"""
        relationships = {
            'config_files': [],
            'docker_configs': [],
            'systemd_services': [],
            'nginx_configs': [],
            'ssh_configs': [],
            'process_file_map': {},
            'recent_changes': []
        }
        
        # critical config files
        config_files = self.query("""
        SELECT path, size, mtime, ctime, uid, gid, permissions
        FROM file 
        WHERE (path LIKE '/etc/systemd/%'
           OR path LIKE '/etc/nginx/%'
           OR path LIKE '/etc/ssh/%'
           OR path LIKE '/etc/docker/%'
           OR path LIKE '/home/abidan/spider/%')
        AND size < 1000000
        ORDER BY mtime DESC
        """)
        relationships['config_files'] = config_files
        
        # docker-specific files
        docker_configs = self.query("""
        SELECT path, size, mtime, permissions
        FROM file
        WHERE path LIKE '/var/lib/docker/%'
           OR path LIKE '/etc/docker/%'
           OR path = '/usr/bin/docker'
           OR path = '/usr/bin/docker-compose'
        """)
        relationships['docker_configs'] = docker_configs
        
        # active systemd services and their files
        systemd_services = self.query("""
        SELECT name, status, active_enter_timestamp, memory_current, 
               cpu_usage_nsec, fragment_path
        FROM systemd_units
        WHERE unit_type = 'service' 
        AND (active = 'active' OR active = 'failed')
        """)
        relationships['systemd_services'] = systemd_services
        
        # process to file mappings (critical for impact analysis)
        process_files = self.query("""
        SELECT p.name, p.pid, p.cmdline, f.path, f.fd
        FROM processes p
        JOIN process_open_files f ON p.pid = f.pid
        WHERE f.path LIKE '/etc/%'
           OR f.path LIKE '/opt/%'
           OR f.path LIKE '/var/log/%'
           OR f.path LIKE '/var/lib/docker/%'
        ORDER BY p.name
        LIMIT 200
        """)
        
        # group by process for easier analysis
        process_map = {}
        for pf in process_files:
            proc_name = pf['name']
            if proc_name not in process_map:
                process_map[proc_name] = {
                    'pids': set(),
                    'files': set(),
                    'cmdline': pf.get('cmdline', '')
                }
            process_map[proc_name]['pids'].add(pf['pid'])
            process_map[proc_name]['files'].add(pf['path'])
        
        # convert sets to lists for json serialization
        for proc in process_map:
            process_map[proc]['pids'] = list(process_map[proc]['pids'])
            process_map[proc]['files'] = list(process_map[proc]['files'])
        
        relationships['process_file_map'] = process_map
        
        # files modified in last 24 hours
        recent_changes = self.query("""
        SELECT path, mtime, size, uid, gid
        FROM file
        WHERE path LIKE '/etc/%'
           OR path LIKE '/home/abidan/spider/%'
           OR path LIKE '/var/lib/docker/%'
        AND mtime > strftime('%s', 'now', '-1 day')
        ORDER BY mtime DESC
        LIMIT 50
        """)
        relationships['recent_changes'] = recent_changes
        
        return relationships
    
    def scan_homelab_services(self) -> Dict[str, Any]:
        """scan homelab-specific services and their health"""
        services = {
            'docker_containers': [],
            'systemd_health': [],
            'network_services': [],
            'disk_health': [],
            'process_health': []
        }
        
        # docker container info via processes
        docker_processes = self.query("""
        SELECT name, pid, cmdline, cpu_time, memory_size
        FROM processes
        WHERE name = 'docker' 
           OR name = 'containerd'
           OR cmdline LIKE '%docker%'
        """)
        services['docker_containers'] = docker_processes
        
        # critical systemd services
        systemd_health = self.query("""
        SELECT name, status, active_enter_timestamp, memory_current,
               fragment_path, wants, requires
        FROM systemd_units
        WHERE name IN ('docker.service', 'ssh.service', 'nginx.service',
                      'systemd-resolved.service', 'NetworkManager.service')
        """)
        services['systemd_health'] = systemd_health
        
        # network services
        network_services = self.query("""
        SELECT DISTINCT p.name, p.pid, s.local_address, s.local_port, 
               s.protocol, p.cpu_time, p.memory_size
        FROM processes p
        JOIN process_open_sockets s ON p.pid = s.pid
        WHERE s.state = 'LISTEN'
        AND (s.local_port IN ('22', '80', '443', '8080', '7860', '11434')
             OR p.name IN ('sshd', 'nginx', 'apache2', 'docker'))
        """)
        services['network_services'] = network_services
        
        # disk/filesystem health indicators
        disk_health = self.query("""
        SELECT device, path, type, flags, blocks_size, blocks_free, 
               blocks_available, inodes_free
        FROM mounts
        WHERE path IN ('/', '/home', '/var', '/opt', '/DATA')
           OR type = 'ext4'
           OR type = 'xfs'
        """)
        services['disk_health'] = disk_health
        
        # resource-heavy processes
        process_health = self.query("""
        SELECT name, pid, cpu_time, memory_size, state, nice
        FROM processes
        WHERE memory_size > 100000000  -- >100MB
           OR cpu_time > 60  -- >1min cpu
        ORDER BY memory_size DESC
        LIMIT 30
        """)
        services['process_health'] = process_health
        
        return services
    
    def scan_security_indicators(self) -> Dict[str, Any]:
        """enhanced security monitoring for homelab"""
        security = {
            'ssh_activity': [],
            'listening_services': [],
            'suid_files': [],
            'failed_auth': [],
            'docker_security': [],
            'file_permissions': []
        }
        
        # ssh-related processes and connections
        ssh_activity = self.query("""
        SELECT p.name, p.pid, p.cmdline, s.local_port, s.remote_address
        FROM processes p
        LEFT JOIN process_open_sockets s ON p.pid = s.pid
        WHERE p.name IN ('sshd', 'ssh')
           OR p.cmdline LIKE '%ssh%'
        """)
        security['ssh_activity'] = ssh_activity
        
        # all listening services (potential attack surface)
        listening = self.query("""
        SELECT DISTINCT p.name, s.local_address, s.local_port, s.protocol,
               p.uid, p.gid, p.cmdline
        FROM processes p
        JOIN process_open_sockets s ON p.pid = s.pid
        WHERE s.state = 'LISTEN'
        ORDER BY CAST(s.local_port AS INTEGER)
        """)
        security['listening_services'] = listening
        
        # suid/sgid files (security risk)
        suid_files = self.query("""
        SELECT path, permissions, uid, gid, size
        FROM file
        WHERE (path LIKE '/usr/bin/%' OR path LIKE '/usr/sbin/%' OR path LIKE '/bin/%')
        AND (permissions LIKE '%s%' OR permissions LIKE '%S%')
        ORDER BY path
        """)
        security['suid_files'] = suid_files
        
        # docker-related security
        docker_security = self.query("""
        SELECT path, permissions, uid, gid
        FROM file
        WHERE path = '/var/run/docker.sock'
           OR path LIKE '/var/lib/docker/containers/%/config.json'
        """)
        security['docker_security'] = docker_security
        
        # world-writable files in critical locations
        file_permissions = self.query("""
        SELECT path, permissions, uid, gid, mtime
        FROM file
        WHERE path LIKE '/etc/%'
        AND permissions LIKE '%w%'
        AND permissions LIKE '%-%-%w%'  -- world writable
        """)
        security['file_permissions'] = file_permissions
        
        return security
    
    def analyze_file_impact(self, changed_file: str) -> Dict[str, Any]:
        """analyze what would be affected by a file change"""
        impact = {
            'affected_processes': [],
            'dependent_services': [],
            'config_references': [],
            'restart_required': []
        }
        
        # find processes using this file
        affected_procs = self.query(f"""
        SELECT p.name, p.pid, p.cmdline
        FROM processes p
        JOIN process_open_files f ON p.pid = f.pid
        WHERE f.path = '{changed_file}'
        """)
        impact['affected_processes'] = affected_procs
        
        # check if it's a systemd service file
        if '/systemd/' in changed_file and changed_file.endswith('.service'):
            service_name = changed_file.split('/')[-1]
            impact['restart_required'].append(f"systemctl restart {service_name}")
        
        # check if it's nginx config
        if '/nginx/' in changed_file:
            impact['restart_required'].append("systemctl reload nginx")
        
        # check if it's ssh config
        if '/ssh/' in changed_file:
            impact['restart_required'].append("systemctl restart ssh")
        
        return impact
    
    def get_system_performance_metrics(self) -> Dict[str, Any]:
        """collect performance metrics for monitoring"""
        metrics = {
            'memory_usage': [],
            'cpu_usage': [],
            'disk_io': [],
            'network_io': []
        }
        
        # memory info
        memory = self.query("SELECT * FROM memory_info")
        metrics['memory_usage'] = memory
        
        # cpu info
        cpu = self.query("SELECT * FROM cpu_time")
        metrics['cpu_usage'] = cpu
        
        # disk stats
        disk_stats = self.query("""
        SELECT name, reads, writes, read_bytes, write_bytes, read_time, write_time
        FROM disk_stats
        WHERE name NOT LIKE 'loop%'
        """)
        metrics['disk_io'] = disk_stats
        
        return metrics

def scan_with_osquery() -> Dict[str, Any]:
    """main osquery scanning function with enhanced homelab focus"""
    scanner = OSQueryScanner()
    start_time = time.time()
    
    if not scanner.check_osquery_installed():
        return {'error': 'osquery not installed or not accessible'}
    
    try:
        result = {
            'scan_timestamp': datetime.now().isoformat(),
            'scanner_version': 'enhanced_v1.0',
            'file_relationships': scanner.scan_critical_file_relationships(),
            'homelab_services': scanner.scan_homelab_services(), 
            'security_indicators': scanner.scan_security_indicators(),
            'performance_metrics': scanner.get_system_performance_metrics()
        }
        
        # update prometheus metrics
        scanner.osquery_duration.set(time.time() - start_time)
        total_files = len(result['file_relationships'].get('config_files', []))
        scanner.files_tracked.set(total_files)
        
        return result
        
    except Exception as e:
        return {
            'error': f'osquery scan failed: {str(e)}',
            'scan_timestamp': datetime.now().isoformat()
        }
