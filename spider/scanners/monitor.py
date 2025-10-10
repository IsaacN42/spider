#!/usr/bin/env python3
# spider/scanners/inotify_monitor.py

"""
spider real-time file monitoring using inotify
tracks filesystem changes for memory system integration
provides real-time change detection for configuration files and system components
"""

import sys
import os
import select
import struct
import time
import ctypes
import ctypes.util
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# inotify constants
IN_ACCESS = 0x00000001
IN_MODIFY = 0x00000002
IN_ATTRIB = 0x00000004
IN_CLOSE_WRITE = 0x00000008
IN_CLOSE_NOWRITE = 0x00000010
IN_OPEN = 0x00000020
IN_MOVED_FROM = 0x00000040
IN_MOVED_TO = 0x00000080
IN_CREATE = 0x00000100
IN_DELETE = 0x00000200
IN_DELETE_SELF = 0x00000400
IN_MOVE_SELF = 0x00000800

EVENT_NAMES = {
    IN_ACCESS: 'accessed',
    IN_MODIFY: 'modified',
    IN_ATTRIB: 'attributes_changed',
    IN_CLOSE_WRITE: 'closed_write',
    IN_CLOSE_NOWRITE: 'closed_nowrite',
    IN_OPEN: 'opened',
    IN_MOVED_FROM: 'moved_from',
    IN_MOVED_TO: 'moved_to',
    IN_CREATE: 'created',
    IN_DELETE: 'deleted',
    IN_DELETE_SELF: 'deleted_self',
    IN_MOVE_SELF: 'moved_self'
}

class INotifyTracker:
    # low-level inotify interface for filesystem monitoring
    
    def __init__(self, max_events=1000):
        self.fd = None
        self.watches = {}  # wd -> path mapping
        self.events = deque(maxlen=max_events)
        self.stats = defaultdict(int)
        self.libc = None
        
    def initialize_inotify(self):
        # setup inotify system interface
        try:
            # load system libc
            self.libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
            
            # Set up ALL function signatures here
            self.libc.inotify_init.argtypes = []
            self.libc.inotify_init.restype = ctypes.c_int
            
            self.libc.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
            self.libc.inotify_add_watch.restype = ctypes.c_int
            
            self.libc.inotify_rm_watch.argtypes = [ctypes.c_int, ctypes.c_int]
            self.libc.inotify_rm_watch.restype = ctypes.c_int
            
            # initialize inotify
            self.fd = self.libc.inotify_init()
            
            return self.fd >= 0
            
        except Exception as e:
            print(f"Exception in initialize_inotify: {e}")
            return False
    
    def add_directory_watch(self, path, mask=None):
        # add directory to watch list
        if self.fd is None or not os.path.exists(path):
            return None
            
        if mask is None:
            # watch for important file events only
            mask = IN_MODIFY | IN_CREATE | IN_DELETE | IN_MOVED_TO | IN_MOVED_FROM
            
        try:
            wd = self.libc.inotify_add_watch(self.fd, path.encode(), mask)
            
            if wd >= 0:
                self.watches[wd] = path
                return wd
            else:
                # Check for errors
                errno = ctypes.get_errno()
                print(f"inotify_add_watch failed for {path}, errno: {errno}")
                return None
            
        except Exception as e:
            print(f"Exception in add_directory_watch: {e}")
            return None
    
    def remove_watch(self, wd):
        # remove watch descriptor
        if self.fd is None or wd not in self.watches:
            return False
            
        try:
            result = self.libc.inotify_rm_watch(self.fd, wd)
            
            if result == 0:
                del self.watches[wd]
                return True
            return False
            
        except Exception:
            return False
    
    def read_pending_events(self, timeout=1.0):
        # read events from inotify with timeout
        if self.fd is None:
            return []
            
        # check for available data
        ready, _, _ = select.select([self.fd], [], [], timeout)
        if not ready:
            return []
            
        try:
            # read raw event data
            data = os.read(self.fd, 4096)
            events = []
            i = 0
            
            while i < len(data):
                # parse inotify_event structure
                wd, mask, cookie, name_len = struct.unpack('iIII', data[i:i+16])
                i += 16
                
                # extract filename if present
                name = ""
                if name_len > 0:
                    name = data[i:i+name_len].rstrip(b'\0').decode('utf-8', errors='ignore')
                    i += name_len
                
                # build event info
                directory = self.watches.get(wd, 'unknown')
                full_path = os.path.join(directory, name) if name else directory
                
                # decode event types
                event_types = []
                for event_mask, event_name in EVENT_NAMES.items():
                    if mask & event_mask:
                        event_types.append(event_name)
                
                event = {
                    'timestamp': datetime.now().isoformat(),
                    'path': full_path,
                    'directory': directory,
                    'filename': name,
                    'event_types': event_types,
                    'mask': mask,
                    'cookie': cookie
                }
                
                events.append(event)
                self.events.append(event)
                
                # update statistics
                for event_type in event_types:
                    self.stats[event_type] += 1
                    
            return events
            
        except Exception:
            return []
    
    def get_recent_events(self, minutes=5):
        # filter events by time window
        cutoff = datetime.now().timestamp() - (minutes * 60)
        recent = []
        
        for event in self.events:
            try:
                event_time = datetime.fromisoformat(event['timestamp']).timestamp()
                if event_time >= cutoff:
                    recent.append(event)
            except:
                continue
                
        return recent
    
    def cleanup(self):
        # cleanup inotify resources
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
            self.watches.clear()

class FileChangeMonitor:
    # high-level file monitoring interface for spider integration
    
    def __init__(self, watch_dirs=None):
        self.tracker = INotifyTracker()
<<<<<<< HEAD
        self.watch_dirs = watch_dirs or ['/etc', '/opt/spider', '/var/log']
=======
        self.watch_dirs = watch_dirs or ['/etc', '/home/abidan/spider', '/var/log']
>>>>>>> 0de83c2 (spider homelab monitoring system)
        self.running = False
        
    def start_monitoring(self):
        # initialize and start file monitoring
        if not self.tracker.initialize_inotify():
            return False
            
        # add watches for important directories
        watch_count = 0
        for directory in self.watch_dirs:
            if os.path.exists(directory):
                wd = self.tracker.add_directory_watch(directory)
                if wd is not None:
                    watch_count += 1
        
        if watch_count > 0:
            self.running = True
            return True
        return False
    
    def poll_changes(self, timeout=1.0):
        # poll for new filesystem events
        if not self.running:
            return []
        return self.tracker.read_pending_events(timeout)
    
    def get_change_summary(self, minutes=5):
        # summarize recent file changes
        events = self.tracker.get_recent_events(minutes)
        
        summary = {
            'period_minutes': minutes,
            'total_events': len(events),
            'files_changed': set(),
            'directories_affected': set(),
            'event_breakdown': defaultdict(int),
            'recent_changes': []
        }
        
        for event in events:
            summary['files_changed'].add(event['path'])
            summary['directories_affected'].add(event['directory'])
            
            for event_type in event['event_types']:
                summary['event_breakdown'][event_type] += 1
            
            # keep sample of recent changes
            if len(summary['recent_changes']) < 10:
                summary['recent_changes'].append({
                    'time': event['timestamp'],
                    'file': event['path'],
                    'changes': event['event_types']
                })
        
        # convert sets to lists for json serialization
        summary['files_changed'] = list(summary['files_changed'])
        summary['directories_affected'] = list(summary['directories_affected'])
        summary['event_breakdown'] = dict(summary['event_breakdown'])
        
        return summary
    
    def stop_monitoring(self):
        # stop file monitoring
        self.running = False
        self.tracker.cleanup()

class MockFileMonitor:
    # fallback when inotify is not available
    
    def __init__(self, watch_dirs=None):
        self.watch_dirs = watch_dirs or []
        self.running = False
        
    def start_monitoring(self):
        return False
    
    def poll_changes(self, timeout=1.0):
        return []
    
    def get_change_summary(self, minutes=5):
        return {
            'error': 'file monitoring not available',
            'total_events': 0,
            'files_changed': [],
            'directories_affected': [],
            'event_breakdown': {},
            'recent_changes': []
        }
    
    def stop_monitoring(self):
        self.running = False

def start_file_monitoring(directories=None):
    # main entry point for spider integration
    if directories is None:
<<<<<<< HEAD
        directories = ['/etc', '/opt/spider', '/var/log']
=======
        directories = ['/etc', '/home/abidan/spider', '/var/log']
>>>>>>> 0de83c2 (spider homelab monitoring system)
    
    # try to start real monitoring first
    monitor = FileChangeMonitor(directories)
    
    if monitor.start_monitoring():
        return monitor
    else:
        # fall back to mock monitor if inotify fails
        return MockFileMonitor(directories)

def get_file_changes(monitor, minutes=5):
    # get file changes from monitor instance
    if monitor is None:
        return {'error': 'monitoring not active'}
    
    try:
        return monitor.get_change_summary(minutes)
    except Exception as e:
        return {'error': f'failed to get changes: {str(e)}'}