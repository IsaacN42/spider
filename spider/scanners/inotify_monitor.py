#!/usr/bin/env python3
# spider/scanners/inotify_monitor.py
# real-time file monitoring using inotify

import sys
import os
import select
import struct
import ctypes
import ctypes.util
from datetime import datetime
from collections import defaultdict, deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# inotify constants
IN_MODIFY = 0x00000002
IN_CREATE = 0x00000100
IN_DELETE = 0x00000200
IN_MOVED_TO = 0x00000080
IN_MOVED_FROM = 0x00000040

EVENT_NAMES = {
    IN_MODIFY: 'modified',
    IN_CREATE: 'created',
    IN_DELETE: 'deleted',
    IN_MOVED_TO: 'moved_to',
    IN_MOVED_FROM: 'moved_from'
}

class INotifyTracker:
    def __init__(self, max_events=1000):
        self.fd = None
        self.watches = {}
        self.events = deque(maxlen=max_events)
        self.stats = defaultdict(int)
        self.libc = None
        
    def initialize_inotify(self):
        try:
            self.libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
            
            self.libc.inotify_init.argtypes = []
            self.libc.inotify_init.restype = ctypes.c_int
            
            self.libc.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
            self.libc.inotify_add_watch.restype = ctypes.c_int
            
            self.libc.inotify_rm_watch.argtypes = [ctypes.c_int, ctypes.c_int]
            self.libc.inotify_rm_watch.restype = ctypes.c_int
            
            self.fd = self.libc.inotify_init()
            return self.fd >= 0
            
        except Exception as e:
            print(f"inotify init failed: {e}")
            return False
    
    def add_directory_watch(self, path, mask=None):
        if self.fd is None or not os.path.exists(path):
            return None
            
        if mask is None:
            mask = IN_MODIFY | IN_CREATE | IN_DELETE | IN_MOVED_TO | IN_MOVED_FROM
            
        try:
            wd = self.libc.inotify_add_watch(self.fd, path.encode(), mask)
            
            if wd >= 0:
                self.watches[wd] = path
                return wd
            else:
                errno = ctypes.get_errno()
                print(f"add_watch failed for {path}, errno: {errno}")
                return None
        except Exception as e:
            print(f"add_watch exception: {e}")
            return None
    
    def read_pending_events(self, timeout=1.0):
        if self.fd is None:
            return []
            
        ready, _, _ = select.select([self.fd], [], [], timeout)
        if not ready:
            return []
            
        try:
            data = os.read(self.fd, 4096)
            events = []
            i = 0
            
            while i < len(data):
                wd, mask, cookie, name_len = struct.unpack('iIII', data[i:i+16])
                i += 16
                
                name = ""
                if name_len > 0:
                    name = data[i:i+name_len].rstrip(b'\0').decode('utf-8', errors='ignore')
                    i += name_len
                
                directory = self.watches.get(wd, 'unknown')
                full_path = os.path.join(directory, name) if name else directory
                
                event_types = []
                for event_mask, event_name in EVENT_NAMES.items():
                    if mask & event_mask:
                        event_types.append(event_name)
                
                event = {
                    'timestamp': datetime.now().isoformat(),
                    'path': full_path,
                    'directory': directory,
                    'filename': name,
                    'event_types': event_types
                }
                
                events.append(event)
                self.events.append(event)
                
                for event_type in event_types:
                    self.stats[event_type] += 1
                    
            return events
        except Exception:
            return []
    
    def get_recent_events(self, minutes=5):
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
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
            self.watches.clear()

class FileChangeMonitor:
    def __init__(self, watch_dirs=None):
        self.tracker = INotifyTracker()
        self.watch_dirs = watch_dirs or ['/etc', '/home/abidan/spider', '/var/log']
        self.running = False
        
    def start_monitoring(self):
        if not self.tracker.initialize_inotify():
            return False
            
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
        if not self.running:
            return []
        return self.tracker.read_pending_events(timeout)
    
    def get_change_summary(self, minutes=5):
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
            
            if len(summary['recent_changes']) < 10:
                summary['recent_changes'].append({
                    'time': event['timestamp'],
                    'file': event['path'],
                    'changes': event['event_types']
                })
        
        summary['files_changed'] = list(summary['files_changed'])
        summary['directories_affected'] = list(summary['directories_affected'])
        summary['event_breakdown'] = dict(summary['event_breakdown'])
        
        return summary
    
    def stop_monitoring(self):
        self.running = False
        self.tracker.cleanup()

def start_file_monitoring(directories=None):
    if directories is None:
        directories = ['/etc', '/home/abidan/spider', '/var/log']
    
    monitor = FileChangeMonitor(directories)
    
    if monitor.start_monitoring():
        return monitor
    else:
        return None

def get_file_changes(monitor, minutes=5):
    if monitor is None:
        return {'error': 'monitoring not active'}
    
    try:
        return monitor.get_change_summary(minutes)
    except Exception as e:
        return {'error': f'failed to get changes: {str(e)}'}