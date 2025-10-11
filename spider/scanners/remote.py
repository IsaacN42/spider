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
        results = {}
        for name, cfg in self.config.get('remote_servers', {}).items():
            self.logger.info(f"Scanning remote server: {name} ({cfg['host']})")
            try:
                results[name] = self.scan_server(name, cfg)
            except Exception as e:
                self.logger.error(f"Failed to scan {name}: {e}")
                results[name] = {'status': 'error', 'error': str(e)}
        return results

    def scan_server(self, name, cfg):
        host, user = cfg['host'], cfg['user']
        key = cfg.get('ssh_key')

        # test connection
        test = self.run_remote_command(host, user, "echo 'connection test'", ssh_key=key)
        if not test or 'connection test' not in test:
            raise Exception("Connection failed")

        server_type = self.detect_server_type(host, user, key)
        hostname = (self.run_remote_command(host, user, "hostname", ssh_key=key) or name).strip()

        system_info = self.get_system_info(host, user, server_type, key)
        disk_info = self.get_disk_info(host, user, server_type, key)
        docker_info = self.get_docker_info(host, user, key)

        if server_type == 'ubuntu_casaos':
            system_info.update(self.get_casaos_specific_info(host, user, key))

        return {
            'status': 'connected',
            'hostname': hostname,
            'server_type': server_type,
            'system_info': system_info,
            'disk_info': disk_info,
            'docker_info': docker_info,
            'scan_time': datetime.now().isoformat()
        }

    def detect_server_type(self, host, user, ssh_key=None):
        casaos = self.run_remote_command(host, user, "ls /etc/casaos && casaos -v", ssh_key)
        if casaos and '/etc/casaos' in casaos:
            return 'ubuntu_casaos'

        os_release = self.run_remote_command(host, user, "cat /etc/os-release", ssh_key)
        if os_release:
            os_lower = os_release.lower()
            if 'ubuntu' in os_lower:
                return 'ubuntu'
            elif 'debian' in os_lower:
                return 'debian'
            elif 'centos' in os_lower:
                return 'centos'
        return 'linux'

    def get_casaos_specific_info(self, host, user, ssh_key=None):
        info = {}
        version = self.run_remote_command(host, user, "casaos -v || echo unknown", ssh_key)
        info['casaos_version'] = version.strip() if version else 'unknown'

        lsblk = self.run_remote_command(host, user, "lsblk -J", ssh_key)
        if lsblk:
            try:
                info['block_devices'] = json.loads(lsblk)
            except:
                info['block_devices'] = {}

        apps = self.run_remote_command(host, user,
                                       "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' || echo none",
                                       ssh_key)
        info['casaos_apps'] = apps.strip() if apps else 'none'

        ha_vm = self.run_remote_command(host, user,
                                        "virsh list --name | grep -i homeassistant || echo not_found",
                                        ssh_key)
        info['homeassistant_vm'] = 'running' if ha_vm and 'homeassistant' in ha_vm.lower() else 'not_found'

        return info

    def get_disk_info(self, host, user, server_type, ssh_key=None):
        df = self.run_remote_command(host, user, "df -h", ssh_key)
        disks = []
        if df:
            for line in df.strip().split("\n")[1:]:
                parts = line.split()
                if len(parts) >= 6:
                    fs = {
                        'device': parts[0],
                        'size': parts[1],
                        'used': parts[2],
                        'available': parts[3],
                        'use_percent': parts[4],
                        'mountpoint': parts[5]
                    }
                    if server_type == 'ubuntu_casaos':
                        fs['casaos_type'] = self.classify_casaos_partition(parts[5])
                    disks.append(fs)
        return {'raw_output': df, 'filesystems': disks}

    def classify_casaos_partition(self, mount):
        if mount == '/':
            return 'system_root'
        elif mount in ['/home', '/DATA', '/media']:
            return 'user_data'
        elif '/var/lib' in mount:
            return 'service_data'
        elif mount == '/boot':
            return 'boot'
        elif '/mnt' in mount:
            return 'mount_point'
        else:
            return 'other'

    def get_system_info(self, host, user, server_type, ssh_key=None):
        info = {'server_type': server_type}
        info['uptime'] = (self.run_remote_command(host, user, "uptime", ssh_key) or 'unknown').strip()
        info['memory'] = (self.run_remote_command(host, user, "free -h", ssh_key) or 'unknown').strip()
        info['load_average'] = (self.run_remote_command(host, user, "cat /proc/loadavg", ssh_key) or 'unknown').strip()
        info['cpu_info'] = (self.run_remote_command(host, user,
                                                    "nproc && cat /proc/cpuinfo | grep 'model name' | head -1",
                                                    ssh_key) or 'unknown').strip()
        return info

    def get_docker_info(self, host, user, ssh_key=None):
        if not self.run_remote_command(host, user, "which docker", ssh_key):
            return {'status': 'not_installed'}

        containers_raw = self.run_remote_command(host, user, "docker ps -a --format '{{json .}}'", ssh_key)
        containers = []
        if containers_raw:
            for line in containers_raw.strip().split("\n"):
                try:
                    containers.append(json.loads(line))
                except:
                    pass

        stats_raw = self.run_remote_command(host, user, "docker system df --format '{{json .}}'", ssh_key)
        stats = {}
        if stats_raw:
            try:
                stats = json.loads(stats_raw)
            except:
                stats = {}

        return {'status': 'installed', 'containers': containers, 'stats': stats}

    def run_remote_command(self, host, user, command, ssh_key=None):
        ssh_cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=20']
        if ssh_key:
            ssh_cmd += ['-i', ssh_key]
        ssh_cmd += [f'{user}@{host}', command]

        try:
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return result.stdout
            self.logger.error(f"SSH command failed: {result.stderr.strip()}")
            return None
        except subprocess.TimeoutExpired:
            self.logger.error(f"SSH command timed out: {command}")
            return None
        except Exception as e:
            self.logger.error(f"SSH command error: {e}")
            return None
