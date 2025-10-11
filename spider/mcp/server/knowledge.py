#!/usr/bin/env python3
"""
Spider Knowledge Graph MCP Server
MCP wrapper for existing Spider knowledge graph with enhanced semantic search
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add spider to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import existing Spider components
from spider.storage.knowledge_graph import create_knowledge_graph, update_graph_from_spider_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeServer:
    """MCP server wrapper for Spider knowledge graph capabilities"""
    
    def __init__(self, db_path: str = "data/archive/spider_knowledge.db"):
        self.server = Server("knowledge")
        self.db_path = db_path
        self.knowledge_graph = None
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available knowledge graph tools"""
            return [
                Tool(
                    name="get_database_stats",
                    description="Get knowledge base statistics and overview",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="search_files_by_pattern",
                    description="Search files by path pattern",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "File path pattern to search"
                            },
                            "file_type": {
                                "type": "string",
                                "description": "Filter by file type (optional)"
                            }
                        },
                        "required": ["pattern"]
                    }
                ),
                Tool(
                    name="get_file_connections",
                    description="Get all connections for a specific file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file"
                            },
                            "max_depth": {
                                "type": "integer",
                                "description": "Maximum depth to search",
                                "default": 2
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="find_connected_files",
                    description="Find files connected to a given file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file"
                            },
                            "relationship_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Filter by relationship types (optional)"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="get_most_connected_files",
                    description="Get files with highest connection counts",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of files to return",
                                "default": 10
                            }
                        }
                    }
                ),
                Tool(
                    name="get_change_timeline",
                    description="Get change history for a specific file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to look back",
                                "default": 7
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="get_system_snapshots",
                    description="Get available system snapshots",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of snapshots to return",
                                "default": 10
                            }
                        }
                    }
                ),
                Tool(
                    name="get_snapshot_data",
                    description="Get data from a specific snapshot",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "snapshot_id": {
                                "type": "string",
                                "description": "Snapshot ID to retrieve"
                            }
                        },
                        "required": ["snapshot_id"]
                    }
                ),
                Tool(
                    name="add_file_relationship",
                    description="Add a relationship between two files",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_path": {
                                "type": "string",
                                "description": "Source file path"
                            },
                            "target_path": {
                                "type": "string",
                                "description": "Target file path"
                            },
                            "rel_type": {
                                "type": "string",
                                "description": "Relationship type"
                            },
                            "strength": {
                                "type": "number",
                                "description": "Relationship strength (0-1)",
                                "default": 1.0
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata"
                            }
                        },
                        "required": ["source_path", "target_path", "rel_type"]
                    }
                ),
                Tool(
                    name="update_from_spider_data",
                    description="Update knowledge graph from Spider scan data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "snapshot_data": {
                                "type": "object",
                                "description": "Spider snapshot data to process"
                            }
                        },
                        "required": ["snapshot_data"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                # Ensure knowledge graph is initialized
                if not self.knowledge_graph:
                    self.knowledge_graph = create_knowledge_graph(self.db_path)
                
                if name == "get_database_stats":
                    stats = self.knowledge_graph.get_database_stats()
                    return [TextContent(
                        type="text",
                        text=json.dumps(stats, indent=2)
                    )]
                
                elif name == "search_files_by_pattern":
                    pattern = arguments["pattern"]
                    file_type = arguments.get("file_type")
                    results = self.knowledge_graph.search_files_by_pattern(pattern, file_type)
                    return [TextContent(
                        type="text",
                        text=json.dumps(results, indent=2, default=str)
                    )]
                
                elif name == "get_file_connections":
                    file_path = arguments["file_path"]
                    max_depth = arguments.get("max_depth", 2)
                    connections = self.knowledge_graph.get_file_connections(file_path, max_depth)
                    return [TextContent(
                        type="text",
                        text=json.dumps(connections, indent=2, default=str)
                    )]
                
                elif name == "find_connected_files":
                    file_path = arguments["file_path"]
                    relationship_types = arguments.get("relationship_types")
                    files = self.knowledge_graph.find_connected_files(file_path, relationship_types)
                    return [TextContent(
                        type="text",
                        text=json.dumps(files, indent=2)
                    )]
                
                elif name == "get_most_connected_files":
                    limit = arguments.get("limit", 10)
                    files = self.knowledge_graph.get_most_connected_files(limit)
                    return [TextContent(
                        type="text",
                        text=json.dumps(files, indent=2)
                    )]
                
                elif name == "get_change_timeline":
                    file_path = arguments["file_path"]
                    days = arguments.get("days", 7)
                    timeline = self.knowledge_graph.get_change_timeline(file_path, days)
                    return [TextContent(
                        type="text",
                        text=json.dumps(timeline, indent=2, default=str)
                    )]
                
                elif name == "get_system_snapshots":
                    limit = arguments.get("limit", 10)
                    snapshots = self.get_system_snapshots(limit)
                    return [TextContent(
                        type="text",
                        text=json.dumps(snapshots, indent=2, default=str)
                    )]
                
                elif name == "get_snapshot_data":
                    snapshot_id = arguments["snapshot_id"]
                    data = self.get_snapshot_data(snapshot_id)
                    return [TextContent(
                        type="text",
                        text=json.dumps(data, indent=2, default=str)
                    )]
                
                elif name == "add_file_relationship":
                    source_path = arguments["source_path"]
                    target_path = arguments["target_path"]
                    rel_type = arguments["rel_type"]
                    strength = arguments.get("strength", 1.0)
                    metadata = arguments.get("metadata")
                    
                    self.knowledge_graph.add_file_relationship(
                        source_path, target_path, rel_type, strength, metadata
                    )
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "message": f"Added relationship: {source_path} -> {target_path} ({rel_type})"
                        }, indent=2)
                    )]
                
                elif name == "update_from_spider_data":
                    snapshot_data = arguments["snapshot_data"]
                    success = update_graph_from_spider_data(self.knowledge_graph, snapshot_data)
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": success,
                            "message": "Knowledge graph updated" if success else "Failed to update knowledge graph"
                        }, indent=2)
                    )]
                
                else:
                    raise ValueError(f"Unknown tool: {name}")
            
            except Exception as e:
                logger.error(f"Tool call error: {e}")
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}, indent=2)
                )]
    
    def get_system_snapshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get available system snapshots"""
        if not self.knowledge_graph:
            return []
        
        try:
            cursor = self.knowledge_graph.conn.execute("""
                SELECT snapshot_id, timestamp, hostname, scan_type
                FROM system_snapshots
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            snapshots = []
            for row in cursor:
                snapshots.append({
                    "snapshot_id": row[0],
                    "timestamp": row[1],
                    "hostname": row[2],
                    "scan_type": row[3]
                })
            
            return snapshots
        
        except Exception as e:
            logger.error(f"Failed to get snapshots: {e}")
            return []
    
    def get_snapshot_data(self, snapshot_id: str) -> Dict[str, Any]:
        """Get data from a specific snapshot"""
        if not self.knowledge_graph:
            return {"error": "Knowledge graph not initialized"}
        
        try:
            cursor = self.knowledge_graph.conn.execute("""
                SELECT data_json
                FROM system_snapshots
                WHERE snapshot_id = ?
            """, (snapshot_id,))
            
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            else:
                return {"error": "Snapshot not found"}
        
        except Exception as e:
            logger.error(f"Failed to get snapshot data: {e}")
            return {"error": str(e)}
    
    def close_connection(self):
        """Close knowledge graph connection"""
        if self.knowledge_graph:
            self.knowledge_graph.close_connection()

async def main():
    """Main entry point"""
    server = KnowledgeServer()
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="knowledge",
                    server_version="1.0.0",
                    capabilities={}
                )
            )
    finally:
        server.close_connection()

if __name__ == "__main__":
    asyncio.run(main())
