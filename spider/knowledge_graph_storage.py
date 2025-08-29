"""
spider knowledge graph storage
stores system relationships in queryable format
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from pathlib import Path

class KnowledgeGraph:
    def __init__(self, db_path: str = "/opt/spider/data/knowledge.db"):
        self.db_path = db_path
        self.conn = None
        self._ensure_db_exists()
        
    def _ensure_db_exists(self):
        """create database and tables if needed"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # create tables
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
    
    def add_file(self, path: str, file_type: str = None, size: int = None, 
                 modified_time: float = None, content_hash: str = None) -> int:
        """add or update file in knowledge graph"""
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
    
    def add_relationship(self, source_path: str, target_path: str, 
                        rel_type: str, strength: float = 1.0, metadata: Dict = None):
        """add relationship between two files"""
        
        # ensure both files exist in db
        source_id = self.add_file(source_path)
        target_id = self.add_file(target_path)
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        self.conn.execute(
            """INSERT OR REPLACE INTO relationships 
               (source_file_id, target_file_id, relationship_type, strength, metadata, discovered_time)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (source_id, target_id, rel_type, strength, metadata_json, datetime.now().isoformat())
        )
        
        self.conn.commit()
    
    def store_snapshot(self, snapshot_data: Dict[str, Any]) -> bool:
        """store system snapshot"""
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
    
    def get_file_relationships(self, file_path: str, max_depth: int = 2) -> Dict[str, Any]:
        """get relationships for a specific file"""
        file_id = self._get_file_id(file_path)
        if not file_id:
            return {'error': 'file not found'}
        
        relationships = {
            'file': file_path,
            'outgoing': [],  # files this file references
            'incoming': [],  # files that reference this file
            'depth_map': {}
        }
        
        # get direct relationships
        cursor = self.conn.execute("""
            SELECT f.path, r.relationship_type, r.strength, r.metadata
            FROM relationships r
            JOIN files f ON f.id = r.target_file_id
            WHERE r.source_file_id = ?
        """, (file_id,))
        
        for path, rel_type, strength, metadata in cursor:
            relationships['outgoing'].append({
                'target': path,
                'type': rel_type,
                'strength': strength,
                'metadata': json.loads(metadata) if metadata else {}
            })
        
        # get incoming relationships
        cursor = self.conn.execute("""
            SELECT f.path, r.relationship_type, r.strength, r.metadata
            FROM relationships r
            JOIN files f ON f.id = r.source_file_id
            WHERE r.target_file_id = ?
        """, (file_id,))
        
        for path, rel_type, strength, metadata in cursor:
            relationships['incoming'].append({
                'source': path,
                'type': rel_type,
                'strength': strength,
                'metadata': json.loads(metadata) if metadata else {}
            })
        
        return relationships
    
    def find_connected_files(self, file_path: str, relationship_types: List[str] = None) -> List[str]:
        """find all files connected to given file"""
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
    
    def get_most_connected_files(self, limit: int = 10) -> List[Dict[str, Any]]:
        """get files with most relationships"""
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
    
    def search_files(self, pattern: str, file_type: str = None) -> List[Dict[str, Any]]:
        """search files by path pattern"""
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
    
    def get_relationship_stats(self) -> Dict[str, Any]:
        """get statistics about relationships"""
        stats = {}
        
        # total counts
        cursor = self.conn.execute("SELECT COUNT(*) FROM files")
        stats['total_files'] = cursor.fetchone()[0]
        
        cursor = self.conn.execute("SELECT COUNT(*) FROM relationships")
        stats['total_relationships'] = cursor.fetchone()[0]
        
        # relationship types
        cursor = self.conn.execute("""
            SELECT relationship_type, COUNT(*) 
            FROM relationships 
            GROUP BY relationship_type 
            ORDER BY COUNT(*) DESC
        """)
        stats['relationship_types'] = dict(cursor.fetchall())
        
        # file types
        cursor = self.conn.execute("""
            SELECT file_type, COUNT(*) 
            FROM files 
            GROUP BY file_type 
            ORDER BY COUNT(*) DESC
        """)
        stats['file_types'] = dict(cursor.fetchall())
        
        return stats
    
    def update_from_scan_results(self, scan_results: Dict[str, Any]):
        """update graph from file relationship scan results"""
        # process each directory's results
        for directory, dir_data in scan_results.get('directories', {}).items():
            connections = dir_data.get('connections', {})
            
            for source_file, file_data in connections.items():
                # add source file
                self.add_file(
                    source_file,
                    size=file_data.get('size'),
                    modified_time=file_data.get('modified')
                )
                
                # add relationships
                for rel_type, target_files in file_data.get('references', {}).items():
                    for target_file in target_files:
                        self.add_relationship(source_file, target_file, rel_type)
    
    def get_change_timeline(self, file_path: str, days: int = 7) -> List[Dict[str, Any]]:
        """get change timeline for a file"""
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
    
    def _get_file_id(self, path: str) -> Optional[int]:
        """get file id by path"""
        cursor = self.conn.execute("SELECT id FROM files WHERE path = ?", (path,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def close(self):
        """close database connection"""
        if self.conn:
            self.conn.close()

# integration functions
def create_knowledge_graph(db_path: str = None) -> KnowledgeGraph:
    """create knowledge graph instance"""
    if db_path is None:
        db_path = "/opt/spider/data/knowledge.db"
    return KnowledgeGraph(db_path)

def update_graph_from_spider_data(graph: KnowledgeGraph, snapshot: Dict[str, Any]):
    """update graph from spider snapshot"""
    # store snapshot
    graph.store_snapshot(snapshot)
    
    # update relationships if scan included file relationships
    if 'file_relationships' in snapshot:
        graph.update_from_scan_results(snapshot['file_relationships'])
    
    # track file changes
    if 'file_changes' in snapshot:
        changes = snapshot['file_changes']
        for change in changes.get('recent_changes', []):
            file_id = graph.add_file(change['file'])
            if file_id:
                graph.conn.execute("""
                    INSERT INTO file_changes (file_id, change_type, new_value, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (file_id, ','.join(change['changes']), change['file'], change['time']))
        graph.conn.commit()