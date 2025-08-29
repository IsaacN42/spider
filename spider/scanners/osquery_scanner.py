"""
spider osquery scanner
deep system introspection using osquery
"""

import json
import subprocess
from datetime import datetime
from typing import Dict, Any, List

class OSQueryScanner:
    def __init__(self):
        self.osquery_path = "osqueryi"
        
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
        try:
            cmd = [self.osquery_path, "--json", sql]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            return []
        except:
            return []
    
    def scan_file_relationships(self) -> Dict[str, Any]:
        """build file relationship map"""
        relationships = {
            'config_references': [],
            'log_references': [],
            'binary_dependencies': [],
            'service_files': []
        }
        
        # find config files that reference other files
        config_refs = self.query("""
        SELECT path, size, mtime 
        FROM file 
        WHERE path LIKE '/etc/%' 
        AND size < 100000
        """)
        
        relationships['config_references'] = config_refs
        
        # find running processes and their open files
        process_files = self.query("""
        SELECT p.name, p.pid, f.path
        FROM processes p
        JOIN process_open_files f ON p.pid = f.pid
        WHERE f.path NOT LIKE '/proc/%'
        AND f.path NOT LIKE '/sys/%'
        AND f.path NOT LIKE '/dev/%'
        LIMIT 100
        """)
        
        relationships['process_files'] = process_files
        
        # systemd service files
        services = self.query("""
        SELECT name, status, source
        FROM systemd_units
        WHERE source LIKE '%.service'
        """)
        
        relationships['service_files'] = services
        
        return relationships
    
    def scan_system_state(self) -> Dict[str, Any]:
        """comprehensive system state scan"""
        state = {
            'scan_time': datetime.now().isoformat(),
            'hostname': '',
            'users': [],
            'processes': [],
            'network': [],
            'mounts': []
        }
        
        # hostname
        hostname = self.query("SELECT hostname FROM system_info")
        if hostname:
            state['hostname'] = hostname[0].get('hostname', '')
        
        # active users
        users = self.query("SELECT username, type, time FROM logged_in_users")
        state['users'] = users
        
        # top processes by cpu
        processes = self.query("""
        SELECT name, pid, cpu_time, memory_size, state
        FROM processes 
        ORDER BY cpu_time DESC 
        LIMIT 20
        """)
        state['processes'] = processes
        
        # network connections
        network = self.query("""
        SELECT local_address, local_port, remote_address, state, protocol
        FROM process_open_sockets
        WHERE state = 'LISTEN'
        """)
        state['network'] = network
        
        # mounted filesystems
        mounts = self.query("""
        SELECT device, path, type, flags
        FROM mounts
        WHERE path NOT LIKE '/proc%'
        AND path NOT LIKE '/sys%'
        """)
        state['mounts'] = mounts
        
        return state
    
    def scan_security_state(self) -> Dict[str, Any]:
        """scan security-relevant system state"""
        security = {
            'suid_files': [],
            'listening_services': [],
            'failed_logins': [],
            'iptables_rules': []
        }
        
        # suid binaries
        suid = self.query("""
        SELECT path, permissions, uid, gid
        FROM file
        WHERE path LIKE '/usr/%'
        AND (permissions LIKE '%s%' OR permissions LIKE '%S%')
        """)
        security['suid_files'] = suid
        
        # listening services
        listening = self.query("""
        SELECT DISTINCT p.name, s.local_address, s.local_port, s.protocol
        FROM processes p
        JOIN process_open_sockets s ON p.pid = s.pid
        WHERE s.state = 'LISTEN'
        """)
        security['listening_services'] = listening
        
        return security

def scan_with_osquery() -> Dict[str, Any]:
    """main osquery scanning function"""
    scanner = OSQueryScanner()
    
    if not scanner.check_osquery_installed():
        return {'error': 'osquery not installed'}
    
    return {
        'relationships': scanner.scan_file_relationships(),
        'system_state': scanner.scan_system_state(),
        'security_state': scanner.scan_security_state()
    }