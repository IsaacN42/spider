#!/usr/bin/env python3
# spider/storage/knowledge_graph.py

"""
spider knowledge graph storage system
stores file relationships and system state in queryable sqlite database
provides graph operations for file dependency analysis and change tracking
"""

import sys
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class KnowledgeGraphDB:
    # sqlite-based storage for file relationships and system snapshots
    
    def __init__(self, db_path="/opt/spider/data/knowledge.db"):
        self.db_path = db_path
        self.conn = None
        self._initialize_database()
        
    def _initialize_database(self):
        # create database schema if needed
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # create main tables
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            path TEXT UNIQUE NOT NULL,
            file_type TEXT,
            size INTEGER,
            modified_time REAL,
            created_time TEXT,
            content_hash TEXT
        );
        
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY,
            source_file_id INTEGER,
            target_file_id INTEGER,
            relationship_type TEXT NOT NULL,
            strength REAL DEFAULT 1.0,
            metadata TEXT,
            discovered_time TEXT,
            FOREIGN KEY (source_file_id) REFERENCES files (id),
            FOREIGN KEY (target_file_id) REFERENCES files (id)
        );
        
        CREATE TABLE IF NOT EXISTS system_snapshots (
            id INTEGER PRIMARY KEY,
            snapshot_id TEXT UNIQUE,
            timestamp TEXT,
            hostname TEXT,
            scan_type TEXT,
            data_json TEXT
        );
        
        CREATE TABLE IF NOT EXISTS file_changes (
            id INTEGER PRIMARY KEY,
            file_id INTEGER,
            change_type TEXT,
            old_value TEXT,
            new_value TEXT,
            timestamp TEXT,
            FOREIGN KEY (file_id) REFERENCES files (id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_file_path ON files(path);
        CREATE INDEX IF NOT EXISTS idx_relationship_source ON relationships(source_file_id);
        CREATE INDEX IF NOT EXISTS idx_relationship_type ON relationships(relationship_type);
        CREATE INDEX IF NOT EXISTS idx_changes_time ON file_changes(timestamp);
        """)
        
        self.conn.commit()
    
    def add_file_record(self, path, file_type=None, size=None, modified_time=None, content_hash=None):
        # add or update file in database
        if file_type is None:
            file_type = Path(path).suffix.lstrip('.')
            
        cursor = self.conn.execute(
            """INSERT OR REPLACE INTO files 
               (path, file_type, size, modified_time, created_time, content_hash)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (path, file_type, size, modified_time, datetime.now().isoformat(), content_hash)
        )
        
        self.conn.commit()
        return cursor.lastrowid
    
    def add_file_relationship(self, source_path, target_path, rel_type, strength=1.0, metadata=None):
        # create relationship between two files
        
        # ensure both files exist
        source_id = self.add_file_record(source_path)
        target_id = self.add_file_record(target_path)
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        self.conn.execute(
            """INSERT OR REPLACE INTO relationships 
               (source_file_id, target_file_id, relationship_type, strength, metadata, discovered_time)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (source_id, target_id, rel_type, strength, metadata_json, datetime.now().isoformat())
        )
        
        self.conn.commit()
    
    def store_system_snapshot(self, snapshot_data):
        # store complete system snapshot
        snapshot_id = snapshot_data.get('scan_id', f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        try:
            self.conn.execute(
                """INSERT OR REPLACE INTO system_snapshots 
                   (snapshot_id, timestamp, hostname, scan_type, data_json)
                   VALUES (?, ?, ?, ?, ?)""",
                (snapshot_id, 
                 snapshot_data.get('timestamp', datetime.now().isoformat()),
                 snapshot_data.get('hostname', 'unknown'),
                 snapshot_data.get('scan_type', 'unknown'),
                 json.dumps(snapshot_data))
            )
            
            self.conn.commit()
            return True
        except Exception:
            return False
    
    def get_file_connections(self, file_path, max_depth=2):
        # get all connections for a specific file
        file_id = self._get_file_id(file_path)
        if not file_id:
            return {'error': 'file not found'}
        
        connections = {
            'file': file_path,
            'outgoing': [],  # files this references
            'incoming': [],  # files that reference this
            'related_files': set()
        }
        
        # get outgoing relationships
        cursor = self.conn.execute("""
            SELECT f.path, r.relationship_type, r.strength, r.metadata
            FROM relationships r
            JOIN files f ON f.id = r.target_file_id
            WHERE r.source_file_id = ?
        """, (file_id,))
        
        for path, rel_type, strength, metadata in cursor:
            connections['outgoing'].append({
                'target': path,
                'type': rel_type,
                'strength': strength,
                'metadata': json.loads(metadata) if metadata else {}
            })
            connections['related_files'].add(path)
        
        # get incoming relationships
        cursor = self.conn.execute("""
            SELECT f.path, r.relationship_type, r.strength, r.metadata
            FROM relationships r
            JOIN files f ON f.id = r.source_file_id
            WHERE r.target_file_id = ?
        """, (file_id,))
        
        for path, rel_type, strength, metadata in cursor:
            connections['incoming'].append({
                'source': path,
                'type': rel_type,
                'strength': strength,
                'metadata': json.loads(metadata) if metadata else {}
            })
            connections['related_files'].add(path)
        
        # convert set to list
        connections['related_files'] = list(connections['related_files'])
        return connections
    
    def find_connected_files(self, file_path, relationship_types=None):
        # find all files connected to given file
        file_id = self._get_file_id(file_path)
        if not file_id:
            return []
        
        type_filter = ""
        params = [file_id, file_id]
        
        if relationship_types:
            placeholders = ','.join('?' * len(relationship_types))
            type_filter = f"AND r.relationship_type IN ({placeholders})"
            params.extend(relationship_types)
        
        query = f"""
            SELECT DISTINCT f.path
            FROM relationships r
            JOIN files f ON (f.id = r.target_file_id OR f.id = r.source_file_id)
            WHERE (r.source_file_id = ? OR r.target_file_id = ?)
            AND f.id != ?
            {type_filter}
        """
        params.append(file_id)
        
        cursor = self.conn.execute(query, params)
        return [row[0] for row in cursor]
    
    def get_most_connected_files(self, limit=10):
        # find files with highest connection counts
        cursor = self.conn.execute("""
            SELECT f.path, f.file_type, COUNT(r.id) as connection_count
            FROM files f
            LEFT JOIN relationships r ON (f.id = r.source_file_id OR f.id = r.target_file_id)
            GROUP BY f.id, f.path, f.file_type
            ORDER BY connection_count DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {'path': path, 'type': file_type, 'connections': count}
            for path, file_type, count in cursor
        ]
    
    def search_files_by_pattern(self, pattern, file_type=None):
        # search files by path pattern
        query = "SELECT path, file_type, size, modified_time FROM files WHERE path LIKE ?"
        params = [f"%{pattern}%"]
        
        if file_type:
            query += " AND file_type = ?"
            params.append(file_type)
        
        cursor = self.conn.execute(query, params)
        return [
            {'path': path, 'type': ftype, 'size': size, 'modified': mtime}
            for path, ftype, size, mtime in cursor
        ]
    
    def get_database_stats(self):
        # get comprehensive database statistics
        stats = {}
        
        # basic counts
        cursor = self.conn.execute("SELECT COUNT(*) FROM files")
        stats['total_files'] = cursor.fetchone()[0]
        
        cursor = self.conn.execute("SELECT COUNT(*) FROM relationships")
        stats['total_relationships'] = cursor.fetchone()[0]
        
        cursor = self.conn.execute("SELECT COUNT(*) FROM system_snapshots")
        stats['total_snapshots'] = cursor.fetchone()[0]
        
        # relationship type breakdown
        cursor = self.conn.execute("""
            SELECT relationship_type, COUNT(*) 
            FROM relationships 
            GROUP BY relationship_type 
            ORDER BY COUNT(*) DESC
        """)
        stats['relationship_types'] = dict(cursor.fetchall())
        
        # file type breakdown
        cursor = self.conn.execute("""
            SELECT file_type, COUNT(*) 
            FROM files 
            GROUP BY file_type 
            ORDER BY COUNT(*) DESC
        """)
        stats['file_types'] = dict(cursor.fetchall())
        
        return stats
    
    def update_from_relationship_scan(self, scan_results):
        # update database from file relationship scan results
        for directory, dir_data in scan_results.get('directories', {}).items():
            connections = dir_data.get('connections', {})
            
            for source_file, file_data in connections.items():
                # add source file
                self.add_file_record(
                    source_file,
                    size=file_data.get('size'),
                    modified_time=file_data.get('modified')
                )
                
                # add all relationships
                for rel_type, target_files in file_data.get('references', {}).items():
                    for target_file in target_files:
                        self.add_file_relationship(source_file, target_file, rel_type)
    
    def get_change_timeline(self, file_path, days=7):
        # get change history for specific file
        file_id = self._get_file_id(file_path)
        if not file_id:
            return []
        
        cutoff = datetime.now().timestamp() - (days * 24 * 3600)
        cutoff_iso = datetime.fromtimestamp(cutoff).isoformat()
        
        cursor = self.conn.execute("""
            SELECT change_type, old_value, new_value, timestamp
            FROM file_changes
            WHERE file_id = ? AND timestamp > ?
            ORDER BY timestamp DESC
        """, (file_id, cutoff_iso))
        
        return [
            {'type': change_type, 'old': old_val, 'new': new_val, 'time': timestamp}
            for change_type, old_val, new_val, timestamp in cursor
        ]
    
    def _get_file_id(self, path):
        # get file id by path
        cursor = self.conn.execute("SELECT id FROM files WHERE path = ?", (path,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def close_connection(self):
        # cleanup database connection
        if self.conn:
            self.conn.close()

def create_knowledge_graph(db_path=None):
    # factory function for knowledge graph creation
    if db_path is None:
        db_path = "/opt/spider/data/knowledge.db"
    return KnowledgeGraphDB(db_path)

def update_graph_from_spider_data(graph, snapshot):
    # update graph from spider snapshot data
    try:
        # store the snapshot
        graph.store_system_snapshot(snapshot)
        
        # update file relationships if present
        if 'file_relationships' in snapshot:
            graph.update_from_relationship_scan(snapshot['file_relationships'])
        
        # track file changes if present
        if 'file_changes' in snapshot:
            changes = snapshot['file_changes']
            for change in changes.get('recent_changes', []):
                file_id = graph.add_file_record(change['file'])
                if file_id:
                    graph.conn.execute("""
                        INSERT INTO file_changes (file_id, change_type, new_value, timestamp)
                        VALUES (?, ?, ?, ?)
                    """, (file_id, ','.join(change['changes']), change['file'], change['time']))
            graph.conn.commit()
            
        return True
        
    except Exception as e:
        return False