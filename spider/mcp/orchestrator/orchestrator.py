#!/usr/bin/env python3
"""
Spider MCP Orchestrator
Main coordinator for all Spider MCP servers and tools
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
from spider.main import SpiderEnhanced
from spider.scanners.disk import scan_disks
from spider.scanners.network import scan_network_interfaces
from spider.scanners.docker import scan_docker_containers
from spider.scanners.filesystem import scan_important_configs
from spider.scanners.remote import RemoteScanner
from spider.llm.llm_analyzer import LLMAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Orchestrator:
    """Main Spider MCP orchestrator that coordinates all tools and servers"""
    
    def __init__(self):
        self.server = Server("orchestrator")
        self.spider = SpiderEnhanced()
        self.llm_analyzer = LLMAnalyzer()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available Spider orchestration tools"""
            return [
                Tool(
                    name="run_comprehensive_scan",
                    description="Run comprehensive Spider scan with all components",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_remote": {
                                "type": "boolean",
                                "description": "Include remote server scanning",
                                "default": False
                            },
                            "include_analysis": {
                                "type": "boolean",
                                "description": "Include AI analysis",
                                "default": True
                            },
                            "include_memory": {
                                "type": "boolean",
                                "description": "Include memory/knowledge graph features",
                                "default": True
                            }
                        }
                    }
                ),
                Tool(
                    name="run_quick_scan",
                    description="Run quick system health check",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "components": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["disk", "network", "docker", "filesystem"]
                                },
                                "description": "Components to scan",
                                "default": ["disk", "network", "docker"]
                            }
                        }
                    }
                ),
                Tool(
                    name="get_system_status",
                    description="Get current system status overview",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="analyze_system_health",
                    description="Analyze system health and provide recommendations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "snapshot_data": {
                                "type": "object",
                                "description": "System snapshot data to analyze (optional)"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_model_recommendation",
                    description="Get AI model recommendation based on current resources",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workload": {
                                "type": "string",
                                "enum": ["general", "high_quality", "complex", "speed", "throughput"],
                                "description": "Type of workload",
                                "default": "general"
                            }
                        }
                    }
                ),
                Tool(
                    name="start_monitoring_daemon",
                    description="Start continuous monitoring daemon",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "interval_minutes": {
                                "type": "integer",
                                "description": "Monitoring interval in minutes",
                                "default": 30
                            },
                            "include_remote": {
                                "type": "boolean",
                                "description": "Include remote monitoring",
                                "default": False
                            }
                        }
                    }
                ),
                Tool(
                    name="get_spider_config",
                    description="Get current Spider configuration",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="test_ollama_connection",
                    description="Test Ollama LLM connection",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="get_recent_snapshots",
                    description="Get recent system snapshots",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of snapshots",
                                "default": 10
                            }
                        }
                    }
                ),
                Tool(
                    name="compare_snapshots",
                    description="Compare two system snapshots",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "snapshot1_id": {
                                "type": "string",
                                "description": "First snapshot ID"
                            },
                            "snapshot2_id": {
                                "type": "string",
                                "description": "Second snapshot ID"
                            }
                        },
                        "required": ["snapshot1_id", "snapshot2_id"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                if name == "run_comprehensive_scan":
                    include_remote = arguments.get("include_remote", False)
                    include_analysis = arguments.get("include_analysis", True)
                    include_memory = arguments.get("include_memory", True)
                    
                    success = self.spider.run_enhanced_scan(
                        include_remote=include_remote,
                        include_analysis=include_analysis,
                        include_memory=include_memory
                    )
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": success,
                            "scan_type": "comprehensive",
                            "include_remote": include_remote,
                            "include_analysis": include_analysis,
                            "include_memory": include_memory,
                            "timestamp": datetime.now().isoformat()
                        }, indent=2)
                    )]
                
                elif name == "run_quick_scan":
                    components = arguments.get("components", ["disk", "network", "docker"])
                    results = {}
                    
                    for component in components:
                        try:
                            if component == "disk":
                                results["disk"] = scan_disks()
                            elif component == "network":
                                results["network"] = scan_network_interfaces()
                            elif component == "docker":
                                results["docker"] = scan_docker_containers()
                            elif component == "filesystem":
                                results["filesystem"] = scan_important_configs()
                        except Exception as e:
                            results[component] = {"error": str(e)}
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "scan_type": "quick",
                            "components": components,
                            "results": results,
                            "timestamp": datetime.now().isoformat()
                        }, indent=2, default=str)
                    )]
                
                elif name == "get_system_status":
                    status = await self.get_system_status()
                    return [TextContent(
                        type="text",
                        text=json.dumps(status, indent=2, default=str)
                    )]
                
                elif name == "analyze_system_health":
                    snapshot_data = arguments.get("snapshot_data")
                    if not snapshot_data:
                        # Run quick scan to get current data
                        snapshot_data = {
                            "disk": scan_disks(),
                            "network": scan_network_interfaces(),
                            "docker": scan_docker_containers(),
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    analysis = self.llm_analyzer.analyze_system(snapshot_data)
                    return [TextContent(
                        type="text",
                        text=analysis
                    )]
                
                elif name == "get_model_recommendation":
                    workload = arguments.get("workload", "general")
                    recommendation = await self.get_model_recommendation(workload)
                    return [TextContent(
                        type="text",
                        text=json.dumps(recommendation, indent=2)
                    )]
                
                elif name == "start_monitoring_daemon":
                    interval = arguments.get("interval_minutes", 30)
                    include_remote = arguments.get("include_remote", False)
                    
                    # This would start a background daemon
                    # For now, return instructions
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "message": "Daemon mode not implemented in MCP server",
                            "instructions": f"Run: python spider/main.py --daemon --interval {interval}" + 
                                          (" --remote" if include_remote else ""),
                            "interval_minutes": interval,
                            "include_remote": include_remote
                        }, indent=2)
                    )]
                
                elif name == "get_spider_config":
                    config = self.spider.config
                    return [TextContent(
                        type="text",
                        text=json.dumps(config, indent=2)
                    )]
                
                elif name == "test_ollama_connection":
                    health = self.llm_analyzer.check_ollama_health()
                    test_result = self.llm_analyzer.test_connection() if health else False
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "ollama_available": health,
                            "connection_test": test_result,
                            "model": self.llm_analyzer.model,
                            "host": self.llm_analyzer.ollama_host
                        }, indent=2)
                    )]
                
                elif name == "get_recent_snapshots":
                    limit = arguments.get("limit", 10)
                    snapshots = self.get_recent_snapshots(limit)
                    return [TextContent(
                        type="text",
                        text=json.dumps(snapshots, indent=2, default=str)
                    )]
                
                elif name == "compare_snapshots":
                    snapshot1_id = arguments["snapshot1_id"]
                    snapshot2_id = arguments["snapshot2_id"]
                    comparison = self.compare_snapshots(snapshot1_id, snapshot2_id)
                    return [TextContent(
                        type="text",
                        text=json.dumps(comparison, indent=2, default=str)
                    )]
                
                else:
                    raise ValueError(f"Unknown tool: {name}")
            
            except Exception as e:
                logger.error(f"Tool call error: {e}")
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}, indent=2)
                )]
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status overview"""
        try:
            # Quick system check
            import psutil
            
            status = {
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_usage_percent": psutil.disk_usage('/').percent
                },
                "spider": {
                    "config_loaded": bool(self.spider.config),
                    "knowledge_graph_available": self.spider.knowledge_graph is not None
                },
                "llm": {
                    "ollama_available": self.llm_analyzer.check_ollama_health(),
                    "model": self.llm_analyzer.model,
                    "host": self.llm_analyzer.ollama_host
                }
            }
            
            # Add GPU status if available
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                
                status["gpu"] = {
                    "available": True,
                    "memory_percent": (mem_info.used / mem_info.total) * 100,
                    "memory_used_gb": mem_info.used / (1024**3),
                    "memory_total_gb": mem_info.total / (1024**3)
                }
            except:
                status["gpu"] = {"available": False}
            
            return status
        
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    async def get_model_recommendation(self, workload: str) -> Dict[str, Any]:
        """Get model recommendation based on current resources and workload"""
        try:
            import psutil
            
            # Get current resource status
            memory = psutil.virtual_memory()
            memory_available_gb = memory.available / (1024**3)
            
            # Check GPU if available
            gpu_available = False
            gpu_memory_available_gb = 0
            
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                gpu_available = True
                gpu_memory_available_gb = mem_info.free / (1024**3)
            except:
                pass
            
            recommendation = {
                "workload": workload,
                "current_resources": {
                    "system_memory_available_gb": memory_available_gb,
                    "gpu_available": gpu_available,
                    "gpu_memory_available_gb": gpu_memory_available_gb
                },
                "recommended_model": None,
                "reason": "",
                "alternatives": []
            }
            
            if workload in ["high_quality", "complex"]:
                # Prefer 14B for high quality tasks
                if gpu_available and gpu_memory_available_gb >= 10.5:
                    recommendation["recommended_model"] = "qwen3-14b"
                    recommendation["reason"] = "Sufficient VRAM for high quality inference"
                elif gpu_available and gpu_memory_available_gb >= 6.5:
                    recommendation["recommended_model"] = "qwen3-8b"
                    recommendation["reason"] = "14B unavailable, 8B provides good quality"
                else:
                    recommendation["reason"] = "Insufficient GPU memory for AI models"
            
            elif workload in ["speed", "throughput"]:
                # Prefer 8B for speed
                if gpu_available and gpu_memory_available_gb >= 6.5:
                    recommendation["recommended_model"] = "qwen3-8b"
                    recommendation["reason"] = "Optimal for high throughput"
                elif gpu_available and gpu_memory_available_gb >= 10.5:
                    recommendation["recommended_model"] = "qwen3-14b"
                    recommendation["reason"] = "8B unavailable, 14B as fallback"
                else:
                    recommendation["reason"] = "Insufficient GPU memory for AI models"
            
            else:  # general workload
                # Balance quality and speed
                if gpu_available and gpu_memory_available_gb >= 12.0:
                    recommendation["recommended_model"] = "qwen3-14b"
                    recommendation["reason"] = "Sufficient resources for high quality"
                elif gpu_available and gpu_memory_available_gb >= 6.5:
                    recommendation["recommended_model"] = "qwen3-8b"
                    recommendation["reason"] = "Balanced performance and resource usage"
                else:
                    recommendation["reason"] = "Insufficient GPU memory for AI models"
            
            return recommendation
        
        except Exception as e:
            return {"error": str(e), "workload": workload}
    
    def get_recent_snapshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent system snapshots"""
        try:
            # This would typically read from the knowledge graph or log directory
            # For now, return a placeholder
            return [{
                "message": "Snapshot retrieval not implemented",
                "instructions": "Use knowledge graph MCP server for snapshot access"
            }]
        except Exception as e:
            return [{"error": str(e)}]
    
    def compare_snapshots(self, snapshot1_id: str, snapshot2_id: str) -> Dict[str, Any]:
        """Compare two system snapshots"""
        try:
            # This would typically load snapshots and compare them
            # For now, return a placeholder
            return {
                "message": "Snapshot comparison not implemented",
                "instructions": "Use LLM analyzer MCP server for snapshot comparison"
            }
        except Exception as e:
            return {"error": str(e)}

async def main():
    """Main entry point"""
    orchestrator = Orchestrator()
    
    async with stdio_server() as (read_stream, write_stream):
        await orchestrator.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="orchestrator",
                server_version="1.0.0",
                capabilities={}
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
