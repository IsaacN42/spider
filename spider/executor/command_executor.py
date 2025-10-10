#!/usr/bin/env python3
# spider/executor/command_executor.py
# safely executes whitelisted system commands

import subprocess
import shlex
import os
from typing import Dict, Any

# whitelisted commands
SAFE_COMMANDS = {
    'df', 'lsblk', 'fdisk', 'journalctl', 'systemctl', 'docker', 
    'iptables', 'ufw', 'lshw', 'dmidecode', 'powertop', 'lsof',
    'ip', 'ss', 'netstat', 'ps', 'mount', 'free', 'uptime'
}

# commands that actually need sudo
NEEDS_SUDO = {
    'fdisk', 'journalctl', 'iptables', 'ufw', 'lshw', 'dmidecode', 'powertop'
}

class CommandExecutor:
    def __init__(self, use_sudo=False):
        self.use_sudo = use_sudo
    
    def run_command(self, command: str, force_sudo: bool = False) -> Dict[str, Any]:
        """execute a whitelisted command safely"""
        try:
            # parse command
            parts = shlex.split(command)
            if not parts:
                return {'returncode': 1, 'stdout': '', 'stderr': 'empty command'}
            
            base_cmd = parts[0]
            if base_cmd not in SAFE_COMMANDS:
                return {'returncode': 1, 'stdout': '', 'stderr': f'command not whitelisted: {base_cmd}'}
            
            # only use sudo if needed or forced
            needs_sudo = force_sudo or (self.use_sudo and base_cmd in NEEDS_SUDO)
            
            # build full command
            if needs_sudo and os.geteuid() != 0:
                full_cmd = ['sudo'] + parts
            else:
                full_cmd = parts
            
            # execute
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {'returncode': 1, 'stdout': '', 'stderr': 'command timeout'}
        except Exception as e:
            return {'returncode': 1, 'stdout': '', 'stderr': str(e)}
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """alias for run_command"""
        return self.run_command(command)