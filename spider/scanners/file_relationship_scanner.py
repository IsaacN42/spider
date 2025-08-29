"""
spider file relationship detector
maps connections between config files, imports, logs
"""

import re
import os
import json
from pathlib import Path
from typing import Dict, Set, List, Any
from collections import defaultdict

class FileRelationshipScanner:
    def __init__(self):
        self.relationships = defaultdict(set)
        self.patterns = {
            # config file patterns
            'include': [
                r'include\s+["\']?([^"\';\s]+)["\']?',
                r'source\s+["\']?([^"\';\s]+)["\']?',
                r'@import\s+["\']?([^"\';\s]+)["\']?',
                r'require\s+["\']?([^"\';\s]+)["\']?'
            ],
            # path references
            'path_ref': [
                r'["\']([/][^"\';\s]+\.[a-z]{2,4})["\']',
                r'["\']([/][^"\';\s]+\.conf)["\']',
                r'["\']([/][^"\';\s]+\.log)["\']'
            ],
            # python imports
            'python_import': [
                r'^from\s+([a-zA-Z_][a-zA-Z0-9_\.]*)\s+import',
                r'^import\s+([a-zA-Z_][a-zA-Z0-9_\.]*)'
            ],
            # docker references
            'docker_ref': [
                r'image:\s*["\']?([^"\':\s]+:[^"\':\s]+)["\']?',
                r'FROM\s+([^\s]+)',
                r'volume:\s*["\']?([^"\':\s]+)["\']?'
            ]
        }
    
    def scan_file_content(self, filepath: str) -> Dict[str, Set[str]]:
        """scan file for references to other files"""
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
            pass
            
        return refs
    
    def scan_directory(self, directory: str, max_files: int = 1000) -> Dict[str, Any]:
        """scan directory for file relationships"""
        relationships = {
            'directory': directory,
            'files_scanned': 0,
            'connections': {},
            'file_types': defaultdict(int),
            'orphaned_files': []
        }
        
        scanned_files = []
        path_obj = Path(directory)
        
        # collect files to scan
        for ext in ['.conf', '.cfg', '.yml', '.yaml', '.json', '.py', '.sh', '.service']:
            pattern = f"**/*{ext}"
            files = list(path_obj.glob(pattern))
            scanned_files.extend(files[:max_files//8])  # limit per extension
        
        # scan each file
        for filepath in scanned_files[:max_files]:
            if not filepath.is_file():
                continue
                
            file_str = str(filepath)
            file_refs = self.scan_file_content(file_str)
            
            if file_refs:
                relationships['connections'][file_str] = {
                    'size': filepath.stat().st_size,
                    'modified': filepath.stat().st_mtime,
                    'references': {k: list(v) for k, v in file_refs.items()}
                }
            
            # count file types
            suffix = filepath.suffix or 'no_extension'
            relationships['file_types'][suffix] += 1
            relationships['files_scanned'] += 1
        
        # find orphaned files (no references to them)
        referenced_files = set()
        for conn in relationships['connections'].values():
            for ref_list in conn['references'].values():
                referenced_files.update(ref_list)
        
        all_files = set(str(f) for f in scanned_files)
        relationships['orphaned_files'] = list(all_files - referenced_files)[:20]
        
        return relationships
    
    def build_dependency_graph(self, scan_results: Dict) -> Dict[str, Any]:
        """build dependency graph from scan results"""
        graph = {
            'nodes': [],
            'edges': [],
            'clusters': [],
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
        
        # calculate stats
        graph['stats'] = {
            'total_files': len(graph['nodes']),
            'total_connections': len(graph['edges']),
            'most_connected': self.find_most_connected(scan_results),
            'connection_types': self.count_connection_types(scan_results)
        }
        
        return graph
    
    def find_most_connected(self, scan_results: Dict) -> List[Dict]:
        """find files with most connections"""
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
    
    def count_connection_types(self, scan_results: Dict) -> Dict[str, int]:
        """count different types of connections"""
        type_counts = defaultdict(int)
        
        for data in scan_results.get('connections', {}).values():
            for ref_type, refs in data.get('references', {}).items():
                type_counts[ref_type] += len(refs)
        
        return dict(type_counts)

def scan_file_relationships(directories: List[str] = None) -> Dict[str, Any]:
    """main function to scan file relationships"""
    if directories is None:
        directories = ['/etc', '/opt', '/home', '/var/log']
    
    scanner = FileRelationshipScanner()
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
            dir_results = scanner.scan_directory(directory)
            results['directories'][directory] = dir_results
            
            total_files += dir_results['files_scanned']
            total_connections += len(dir_results.get('connections', {}))
    
    # build global dependency graph
    all_connections = {}
    for dir_data in results['directories'].values():
        all_connections.update(dir_data.get('connections', {}))
    
    combined_results = {'connections': all_connections}
    results['global_graph'] = scanner.build_dependency_graph(combined_results)
    
    # summary stats
    results['summary'] = {
        'directories_scanned': len(directories),
        'total_files_scanned': total_files,
        'total_connections': total_connections,
        'most_connected_files': results['global_graph']['stats']['most_connected'][:5]
    }
    
    return results