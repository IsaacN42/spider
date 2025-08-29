"""
spider real-time file monitor
uses inotify to track filesystem changes
"""

import os
import json
import time
import select
import struct
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque

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

class INotifyMonitor:
    def __init__(self, max_events: int = 1000):
        self.fd = None
        self.watches = {}  # wd -> path mapping
        self.events = deque(maxlen=max_events)
        self.stats = defaultdict(int)
        
    def start_monitoring(self) -> bool:
        """initialize inotify monitoring"""
        try:
            import ctypes
            import ctypes.util
            
            # load libc
            libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
            
            # inotify_init
            libc.inotify_init.restype = ctypes.c_int
            self.fd = libc.inotify_init()
            
            if self.fd < 0:
                return False
                
            self.libc = libc
            return True
            
        except Exception:
            return False
    
    def add_watch(self, path: str, mask: int = None) -> Optional[int]:
        """add directory to watch list"""
        if self.fd is None:
            return None
            
        if mask is None:
            # watch for config file changes
            mask = IN_MODIFY | IN_CREATE | IN_DELETE | IN_MOVED_TO | IN_MOVED_FROM
            
        try:
            # inotify_add_watch
            self.libc.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
            self.libc.inotify_add_watch.restype = ctypes.c_int
            
            wd = self.libc.inotify_add_watch(self.fd, path.encode(), mask)
            
            if wd >= 0:
                self.watches[wd] = path
                return wd
            return None
            
        except Exception:
            return None
    
    def remove_watch(self, wd: int) -> bool:
        """remove watch descriptor"""
        if self.fd is None or wd not in self.watches:
            return False
            
        try:
            # inotify_rm_watch
            self.libc.inotify_rm_watch.argtypes = [ctypes.c_int, ctypes.c_int]
            self.libc.inotify_rm_watch.restype = ctypes.c_int
            
            result = self.libc.inotify_rm_watch(self.fd, wd)
            
            if result == 0:
                del self.watches[wd]
                return True
            return False
            
        except Exception:
            return False
    
    def read_events(self, timeout: float = 1.0) -> List[Dict[str, Any]]:
        """read pending inotify events"""
        if self.fd is None:
            return []
            
        # check if data available
        ready, _, _ = select.select([self.fd], [], [], timeout)
        if not ready:
            return []
            
        try:
            # read event data
            data = os.read(self.fd, 4096)
            events = []
            i = 0
            
            while i < len(data):
                # parse inotify_event struct
                wd, mask, cookie, name_len = struct.unpack('iIII', data[i:i+16])
                i += 16
                
                # read name if present
                name = ""
                if name_len > 0:
                    name = data[i:i+name_len].rstrip(b'\0').decode('utf-8', errors='ignore')
                    i += name_len
                
                # get directory path
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
                
                # update stats
                for event_type in event_types:
                    self.stats[event_type] += 1
                    
            return events
            
        except Exception:
            return []
    
    def get_recent_events(self, minutes: int = 5) -> List[Dict[str, Any]]:
        """get events from last N minutes"""
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
    
    def get_stats(self) -> Dict[str, Any]:
        """get monitoring statistics"""
        return {
            'watched_directories': len(self.watches),
            'total_events': len(self.events),
            'event_types': dict(self.stats),
            'watches': dict(self.watches)
        }
    
    def stop_monitoring(self):
        """cleanup inotify resources"""
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
            self.watches.clear()

class FileChangeTracker:
    def __init__(self, watch_dirs: List[str] = None):
        self.monitor = INotifyMonitor()
        self.watch_dirs = watch_dirs or ['/etc', '/opt/spider', '/var/log']
        self.running = False
        
    def start_tracking(self) -> bool:
        """start tracking file changes"""
        if not self.monitor.start_monitoring():
            return False
            
        # add watches for important directories
        for directory in self.watch_dirs:
            if os.path.exists(directory):
                wd = self.monitor.add_watch(directory)
                if wd is not None:
                    print(f"watching {directory} (wd: {wd})")
        
        self.running = True
        return True
    
    def get_changes_summary(self, minutes: int = 5) -> Dict[str, Any]:
        """get summary of recent changes"""
        events = self.monitor.get_recent_events(minutes)
        
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
            
            # keep last 10 changes
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
    
    def poll_events(self, timeout: float = 1.0) -> List[Dict[str, Any]]:
        """poll for new events"""
        if not self.running:
            return []
        return self.monitor.read_events(timeout)
    
    def stop_tracking(self):
        """stop tracking"""
        self.running = False
        self.monitor.stop_monitoring()

# integration function for main spider
def start_file_monitoring(directories: List[str] = None) -> FileChangeTracker:
    """start file change monitoring"""
    tracker = FileChangeTracker(directories)
    
    if tracker.start_tracking():
        return tracker
    else:
        print("failed to start file monitoring - inotify not available")
        return None

def get_file_changes(tracker: FileChangeTracker, minutes: int = 5) -> Dict[str, Any]:
    """get file changes from tracker"""
    if tracker is None:
        return {'error': 'monitoring not active'}
    
    return tracker.get_changes_summary(minutes)