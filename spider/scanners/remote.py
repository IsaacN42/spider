#!/usr/bin/env python3
# spider/scanners/remote.py

import subprocess
import json
import logging
from datetime import datetime

class RemoteScanner:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def scan_remote_servers(self):
        """scan all configured remote servers"""
        results = {}
        
        for server_name, server_config in self.config.get('remote_servers', {}).items():
            self.logger.info(f"scanning remote server: {server_name} ({server_config['host']})")
            try:
                server_data = self.scan_server(server_name, server_config)
                results[server_name] = server_data
            except Exception as e:
                self.logger.error(f"failed to scan {server_name}: {e}")
                results[server_name] = {'status': 'error', 'error': str(e)}
                
        return results
    
    def scan_server(self, name, config):
        """scan individual remote server"""
        host = config['host']
        user = config['user']
        
        # test connection
        self.logger.info(f"  testing connection to {name}...")
        test_result = self.run_remote_command(host, user, "echo 'connection test'")
        if not test_result or 'connection test' not in test_result:
            raise Exception("connection failed")
        
        # determine server type first
        server_type = self.detect_server_type(host, user)
        self.logger.info(f"  detected server type: {server_type}")
        
        # get hostname
        hostname_result = self.run_remote_command(host, user, "hostname")
        hostname = hostname_result.strip() if hostname_result else name
        self.logger.info(f"  connected to {hostname}")
        
        # gather system info
        self.logger.info("  gathering system info...")
        system_info = self.get_system_info(host, user, server_type)
        
        # get disk usage with server-specific logic
        self.logger.info("  checking disk usage...")
        disk_info = self.get_disk_info(host, user, server_type)
        
        # check docker
        self.logger.info("  checking docker status...")
        docker_info = self.get_docker_info(host, user)
        
        # run server-specific checks
        if server_type == 'zimaos':
            self.logger.info("  running zimaos-specific checks...")
            zimaos_info = self.get_zimaos_specific_info(host, user)
            system_info.update(zimaos_info)
        
        return {
            'status': 'connected',
            'hostname': hostname,
            'server_type': server_type,
            'system_info': system_info,
            'disk_info': disk_info,
            'docker_info': docker_info,
            'scan_time': datetime.now().isoformat()
        }
    
    def detect_server_type(self, host, user):
        """detect what type of server this is"""
        # check for zimaos
        zima_check = self.run_remote_command(host, user, "ls /etc/casaos 2>/dev/null && echo 'zimaos'")
        if zima_check and 'zimaos' in zima_check:
            return 'zimaos'
        
        # check for other distros
        os_release = self.run_remote_command(host, user, "cat /etc/os-release 2>/dev/null")
        if os_release:
            if 'ubuntu' in os_release.lower():
                return 'ubuntu'
            elif 'debian' in os_release.lower():
                return 'debian'
            elif 'centos' in os_release.lower():
                return 'centos'
        
        return 'linux'
    
    def get_zimaos_specific_info(self, host, user):
        """get zimaos-specific information"""
        info = {}
        
        # casaos version
        casaos_version = self.run_remote_command(host, user, "casaos -v 2>/dev/null || echo 'unknown'")
        info['casaos_version'] = casaos_version.strip() if casaos_version else 'unknown'
        
        # zimaos partitioning info
        lsblk_output = self.run_remote_command(host, user, "lsblk -J")
        if lsblk_output:
            try:
                lsblk_data = json.loads(lsblk_output)
                info['block_devices'] = lsblk_data
            except:
                pass
        
        # casaos apps
        apps_info = self.run_remote_command(host, user, "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' 2>/dev/null")
        if apps_info:
            info['casaos_apps'] = apps_info.strip()
        
        return info
    
    def get_disk_info(self, host, user, server_type):
        """get disk usage info with server-type awareness"""
        df_result = self.run_remote_command(host, user, "df -h")
        disk_info = {'raw_output': df_result, 'filesystems': []}
        
        if df_result:
            lines = df_result.strip().split('\n')[1:]  # skip header
            for line in lines:
                parts = line.split()
                if len(parts) >= 6:
                    filesystem = {
                        'device': parts[0],
                        'size': parts[1],
                        'used': parts[2], 
                        'available': parts[3],
                        'use_percent': parts[4],
                        'mountpoint': parts[5]
                    }
                    
                    # add zimaos context
                    if server_type == 'zimaos':
                        filesystem['zimaos_type'] = self.classify_zimaos_partition(parts[5], parts[1])
                    
                    disk_info['filesystems'].append(filesystem)
        
        return disk_info
    
    def classify_zimaos_partition(self, mountpoint, size):
        """classify zimaos partition types"""
        if mountpoint == '/':
            return 'system_root'  # small root partition is normal
        elif mountpoint in ['/DATA', '/media']:
            return 'user_data'    # main data storage
        elif '/var/lib' in mountpoint:
            return 'service_data' # docker/app data
        elif mountpoint == '/mnt/boot':
            return 'boot'
        elif '/mnt/overlay' in mountpoint:
            return 'overlay'
        else:
            return 'other'
    
    def get_system_info(self, host, user, server_type):
        """get basic system information"""
        info = {'server_type': server_type}
        
        # uptime
        uptime_result = self.run_remote_command(host, user, "uptime")
        info['uptime'] = uptime_result.strip() if uptime_result else 'unknown'
        
        # memory
        mem_result = self.run_remote_command(host, user, "free -h")
        info['memory'] = mem_result.strip() if mem_result else 'unknown'
        
        # load average
        load_result = self.run_remote_command(host, user, "cat /proc/loadavg")
        info['load_average'] = load_result.strip() if load_result else 'unknown'
        
        # cpu info
        cpu_result = self.run_remote_command(host, user, "nproc && cat /proc/cpuinfo | grep 'model name' | head -1")
        info['cpu_info'] = cpu_result.strip() if cpu_result else 'unknown'
        
        return info
    
    def get_docker_info(self, host, user):
        """get docker information"""
        # check if docker is installed
        docker_check = self.run_remote_command(host, user, "which docker")
        if not docker_check:
            return {'status': 'not_installed'}
        
        # get container info
        containers_result = self.run_remote_command(host, user, "docker ps -a --format 'json'")
        containers = []
        
        if containers_result:
            for line in containers_result.strip().split('\n'):
                if line.strip():
                    try:
                        container = json.loads(line)
                        containers.append(container)
                    except:
                        pass
        
        # get docker stats
        stats_result = self.run_remote_command(host, user, "docker system df --format 'json'")
        docker_stats = {}
        if stats_result:
            try:
                docker_stats = json.loads(stats_result)
            except:
                pass
        
        return {
            'status': 'installed',
            'containers': containers,
            'stats': docker_stats
        }
    
    def run_remote_command(self, host, user, command):
        """execute command on remote host via ssh"""
        ssh_cmd = [
            'ssh', '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10',
            f'{user}@{host}', command
        ]
        
        try:
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout
            else:
                self.logger.error(f"ssh command failed: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            self.logger.error(f"ssh command timed out: {command}")
            return None
        except Exception as e:
            self.logger.error(f"ssh command error: {e}")
            return None
