#!/usr/bin/env python3
"""
Spider LLM Analyzer MCP Server
MCP wrapper for existing Spider LLM analysis capabilities
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
from spider.llm.llm_analyzer import LLMAnalyzer, analyze_system_enhanced, compare_snapshots_enhanced

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMServer:
    """MCP server wrapper for Spider LLM analysis capabilities"""
    
    def __init__(self, model: str = "llama3.1:8b", host: str = "localhost:11434"):
        self.server = Server("llm")
        self.model = model
        self.host = host
        self.analyzer = LLMAnalyzer(model=model, host=host)
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available LLM analysis tools"""
            return [
                Tool(
                    name="check_ollama_health",
                    description="Check if Ollama service is running and accessible",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="analyze_system",
                    description="Analyze system snapshot using LLM or rule-based fallback",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "snapshot_data": {
                                "type": "object",
                                "description": "System snapshot data to analyze"
                            }
                        },
                        "required": ["snapshot_data"]
                    }
                ),
                Tool(
                    name="compare_snapshots",
                    description="Compare two system snapshots for changes and trends",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "current_snapshot": {
                                "type": "object",
                                "description": "Current system snapshot"
                            },
                            "previous_snapshot": {
                                "type": "object",
                                "description": "Previous system snapshot for comparison"
                            }
                        },
                        "required": ["current_snapshot", "previous_snapshot"]
                    }
                ),
                Tool(
                    name="analyze_system_health",
                    description="Analyze system health from snapshot (rule-based)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "snapshot_data": {
                                "type": "object",
                                "description": "System snapshot data to analyze"
                            }
                        },
                        "required": ["snapshot_data"]
                    }
                ),
                Tool(
                    name="prepare_snapshot_summary",
                    description="Prepare summary data for LLM analysis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "snapshot_data": {
                                "type": "object",
                                "description": "System snapshot data to summarize"
                            }
                        },
                        "required": ["snapshot_data"]
                    }
                ),
                Tool(
                    name="query_ollama",
                    description="Send a direct query to Ollama",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "Prompt to send to Ollama"
                            },
                            "max_tokens": {
                                "type": "integer",
                                "description": "Maximum tokens to generate",
                                "default": 2000
                            }
                        },
                        "required": ["prompt"]
                    }
                ),
                Tool(
                    name="test_connection",
                    description="Test Ollama connection with Spider-specific test",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="get_analysis_history",
                    description="Get history of recent analyses",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of entries to return",
                                "default": 10
                            }
                        }
                    }
                ),
                Tool(
                    name="chunk_data",
                    description="Chunk large data for LLM context limits",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "object",
                                "description": "Data to chunk"
                            },
                            "max_size": {
                                "type": "integer",
                                "description": "Maximum size per chunk",
                                "default": 50000
                            }
                        },
                        "required": ["data"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                if name == "check_ollama_health":
                    health = self.analyzer.check_ollama_health()
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "ollama_available": health,
                            "model": self.model,
                            "host": self.host
                        }, indent=2)
                    )]
                
                elif name == "analyze_system":
                    snapshot_data = arguments["snapshot_data"]
                    analysis = self.analyzer.analyze_system(snapshot_data)
                    return [TextContent(
                        type="text",
                        text=analysis
                    )]
                
                elif name == "compare_snapshots":
                    current = arguments["current_snapshot"]
                    previous = arguments["previous_snapshot"]
                    comparison = self.analyzer.compare_snapshots(current, previous)
                    return [TextContent(
                        type="text",
                        text=comparison
                    )]
                
                elif name == "analyze_system_health":
                    snapshot_data = arguments["snapshot_data"]
                    health_analysis = self.analyzer.analyze_system_health(snapshot_data)
                    return [TextContent(
                        type="text",
                        text=json.dumps(health_analysis, indent=2)
                    )]
                
                elif name == "prepare_snapshot_summary":
                    snapshot_data = arguments["snapshot_data"]
                    summary = self.analyzer.prepare_snapshot_summary(snapshot_data)
                    return [TextContent(
                        type="text",
                        text=json.dumps(summary, indent=2, default=str)
                    )]
                
                elif name == "query_ollama":
                    prompt = arguments["prompt"]
                    max_tokens = arguments.get("max_tokens", 2000)
                    response = self.analyzer.query_ollama(prompt, max_tokens)
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "prompt": prompt,
                            "response": response,
                            "max_tokens": max_tokens
                        }, indent=2)
                    )]
                
                elif name == "test_connection":
                    test_result = self.analyzer.test_connection()
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "connection_test": test_result,
                            "model": self.model,
                            "host": self.host
                        }, indent=2)
                    )]
                
                elif name == "get_analysis_history":
                    limit = arguments.get("limit", 10)
                    history = self.analyzer.analysis_history[-limit:] if self.analyzer.analysis_history else []
                    return [TextContent(
                        type="text",
                        text=json.dumps(history, indent=2, default=str)
                    )]
                
                elif name == "chunk_data":
                    data = arguments["data"]
                    max_size = arguments.get("max_size", 50000)
                    chunks = self.analyzer.chunk_data(data, max_size)
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "chunks": chunks,
                            "total_chunks": len(chunks),
                            "max_size": max_size
                        }, indent=2, default=str)
                    )]
                
                else:
                    raise ValueError(f"Unknown tool: {name}")
            
            except Exception as e:
                logger.error(f"Tool call error: {e}")
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}, indent=2)
                )]

async def main():
    """Main entry point"""
    server = LLMServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="llm",
                server_version="1.0.0",
                capabilities={}
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
