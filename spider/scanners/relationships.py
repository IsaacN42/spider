#!/usr/bin/env python3
# spider/scanners/file_relationships.py

"""
spider file relationship scanner
maps connections between config files, imports, logs, and system references
builds comprehensive file dependency graphs for system understanding
"""

import sys
import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class FileRelationshipMapper:
    # builds file dependency maps using pattern matching and content analysis
    
    def __init__(self):
        self.relationships = defaultdict(set)
        self.patterns = {
            'config_include': [
                r'include\s+["\']?([^"\';\s]+)["\']?',
                r'source\s+["\']?([^"\';\s]+)["\']?',
                r'@import\s+["\']?([^"\';\s]+)["\']?',
                r'require\s+["\']?([^"\';\s]+)["\']?'
            ],
            'path_reference': [
                r'["\']([/][^"\';\s]+\.[a-z]{2,4})["\']',
                r'["\']([/][^"\';\s]+\.conf)["\']',
                r'["\']([/][^"\';\s]+\.log)["\']'
            ],
            'python_import': [
                r'^from\s+([a-zA-Z_][a-zA-Z0-9_\.]*)\s+import',
                r'^import\s+([a-zA-Z_][a-zA-Z0-9_\.]*)'
            ],
            'docker_reference': [
                r'image:\s*["\']?([^"\':\s]+:[^"\':\s]+)["\']?',
                r'FROM\s+([^\s]+)',
                r'volume:\s*["\']?([^"\':\s]+)["\']?'
            ]
        }
    
    def scan_file_content(self, filepath):
        # extract references from file content using pattern matching
        refs = defaultdict(set)
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            for pattern_type, patterns in self.patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.MULTILINE)
                    for match in matches:
                        ref_path = match.group(1)
                        # resolve relative paths
                        if not ref_path.startswith('/'):
                            ref_path = os.path.join(os.path.dirname(filepath), ref_path)
                        refs[pattern_type].add(ref_path)
                        
        except Exception:
            # skip files that can't be read
            pass
            
        return refs
    
    def scan_directory(self, directory, max_files=1000):
        # scan directory for file relationships with limits
        results = {
            'directory': directory,
            'files_scanned': 0,
            'connections': {},
            'file_types': defaultdict(int),
            'orphaned_files': []
        }
        
        scanned_files = []
        path_obj = Path(directory)
        
        # collect important file types only
        for ext in ['.conf', '.cfg', '.yml', '.yaml', '.json', '.py', '.sh', '.service']:
            try:
                pattern = f"**/*{ext}"
                files = list(path_obj.glob(pattern))
                scanned_files.extend(files[:max_files//8])
            except PermissionError:
                continue
        
        # scan each file for references
        for filepath in scanned_files[:max_files]:
            if not filepath.is_file():
                continue
                
            try:
                file_str = str(filepath)
                file_refs = self.scan_file_content(file_str)
                
                if file_refs:
                    results['connections'][file_str] = {
                        'size': filepath.stat().st_size,
                        'modified': filepath.stat().st_mtime,
                        'references': {k: list(v) for k, v in file_refs.items()}
                    }
                
                # count file types
                suffix = filepath.suffix or 'no_extension'
                results['file_types'][suffix] += 1
                results['files_scanned'] += 1
                
            except (PermissionError, OSError):
                # skip inaccessible files
                continue
        
        return results
    
    def build_dependency_graph(self, scan_results):
        # create graph structure from scan results
        graph = {
            'nodes': [],
            'edges': [],
            'stats': {}
        }
        
        # create nodes for each file
        for filepath, data in scan_results.get('connections', {}).items():
            graph['nodes'].append({
                'id': filepath,
                'size': data['size'],
                'modified': data['modified'],
                'type': Path(filepath).suffix
            })
        
        # create edges for relationships
        edge_id = 0
        for source_file, data in scan_results.get('connections', {}).items():
            for ref_type, ref_files in data.get('references', {}).items():
                for target_file in ref_files:
                    graph['edges'].append({
                        'id': edge_id,
                        'source': source_file,
                        'target': target_file,
                        'type': ref_type
                    })
                    edge_id += 1
        
        # calculate statistics
        graph['stats'] = {
            'total_files': len(graph['nodes']),
            'total_connections': len(graph['edges']),
            'most_connected': self._find_most_connected(scan_results),
            'connection_types': self._count_connection_types(scan_results)
        }
        
        return graph
    
    def _find_most_connected(self, scan_results):
        # find files with most relationships
        connection_counts = defaultdict(int)
        
        for filepath, data in scan_results.get('connections', {}).items():
            total_refs = sum(len(refs) for refs in data.get('references', {}).values())
            connection_counts[filepath] = total_refs
        
        # sort by connection count
        sorted_files = sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'file': filepath, 'connections': count}
            for filepath, count in sorted_files[:10]
        ]
    
    def _count_connection_types(self, scan_results):
        # count different relationship types
        type_counts = defaultdict(int)
        
        for data in scan_results.get('connections', {}).values():
            for ref_type, refs in data.get('references', {}).items():
                type_counts[ref_type] += len(refs)
        
        return dict(type_counts)

def scan_file_relationships(directories=None):
    # main scanner function compatible with existing spider architecture
    if directories is None:
        directories = ['/etc', '/opt', '/var/log']
    
    mapper = FileRelationshipMapper()
    results = {
        'scan_time': datetime.now().isoformat(),
        'directories': {},
        'global_graph': {},
        'summary': {}
    }
    
    # scan each directory
    total_files = 0
    total_connections = 0
    
    for directory in directories:
        if os.path.exists(directory):
            try:
                dir_results = mapper.scan_directory(directory)
                results['directories'][directory] = dir_results
                
                total_files += dir_results['files_scanned']
                total_connections += len(dir_results.get('connections', {}))
                
            except PermissionError:
                results['directories'][directory] = {'error': 'permission_denied'}
            except Exception as e:
                results['directories'][directory] = {'error': str(e)}
    
    # build global dependency graph
    all_connections = {}
    for dir_data in results['directories'].values():
        if 'connections' in dir_data:
            all_connections.update(dir_data.get('connections', {}))
    
    combined_results = {'connections': all_connections}
    results['global_graph'] = mapper.build_dependency_graph(combined_results)
    
    # create summary statistics
    results['summary'] = {
        'directories_scanned': len([d for d in results['directories'] if 'error' not in results['directories'][d]]),
        'total_files_scanned': total_files,
        'total_connections': total_connections,
        'most_connected_files': results['global_graph']['stats']['most_connected'][:5] if 'stats' in results['global_graph'] else []
    }
    
    return results