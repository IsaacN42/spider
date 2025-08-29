#!/usr/bin/env python3
# spider/scanners/filesystem.py

import os
from pathlib import Path
from datetime import datetime

def scan_directory(path, max_depth=3):
    """scan directory structure"""
    result = {'path': path, 'files': [], 'config_files': []}
    try:
        path_obj = Path(path)
        if path_obj.exists():
            for item in path_obj.iterdir():
                if item.is_file():
                    result['files'].append(str(item))
    except:
        pass
    return result

def scan_important_configs():
    """scan key config directories"""
    return {'/etc': scan_directory('/etc')}

def parse_config_file(filepath):
    """parse config file"""
    try:
        with open(filepath, 'r') as f:
            return {'content': f.read()[:500]}
    except:
        return {'error': 'cannot read'}
