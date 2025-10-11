#!/usr/bin/env python3
"""
Spider Monitor MCP Server
MCP wrapper for existing Spider monitoring capabilities with GPU support
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
from spider.scanners.monitor import start_file_monitoring, get_file_changes
from spider.scanners.disk import scan_disks
from spider.scanners.network import scan_network_interfaces
from spider.scanners.docker import scan_docker_containers

try:
    import pynvml
    NVIDIA_AVAILABLE = True
except ImportError:
    NVIDIA_AVAILABLE = False

import psutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MonitorServer:
    """MCP server wrapper for Spider monitoring capabilities"""
    
    def __init__(self):
        self.server = Server("monitor")
        self.file_monitor = None
        self.setup_nvidia()
        self.setup_handlers()
    
    def setup_nvidia(self):
        """Initialize NVIDIA monitoring if available"""
        if NVIDIA_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.device_count = pynvml.nvmlDeviceGetCount()
                logger.info(f"NVIDIA monitoring initialized: {self.device_count} GPU(s)")
            except Exception as e:
                logger.warning(f"NVIDIA monitoring unavailable: {e}")
                self.device_count = 0
        else:
            logger.warning("pynvml not available - GPU monitoring disabled")
            self.device_count = 0
    
    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available monitoring tools"""
            return [
                Tool(
                    name="get_system_metrics",
                    description="Get comprehensive system metrics including GPU, CPU, RAM, disk",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_gpu": {
                                "type": "boolean",
                                "description": "Include GPU metrics",
                                "default": True
                            }
                        }
                    }
                ),
                Tool(
                    name="get_gpu_status",
                    description="Get detailed GPU status and utilization",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "integer",
                                "description": "GPU device ID (0-based)",
                                "default": 0
                            }
                        }
                    }
                ),
                Tool(
                    name="scan_disks",
                    description="Scan disk usage and filesystem information",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="scan_network",
                    description="Scan network interfaces and listening ports",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="scan_docker",
                    description="Scan Docker containers and their status",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="start_file_monitoring",
                    description="Start real-time file monitoring",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directories": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Directories to monitor",
                                "default": ["/etc", "/home/abidan/spider", "/var/log"]
                            }
                        }
                    }
                ),
                Tool(
                    name="get_file_changes",
                    description="Get recent file changes from monitoring",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "minutes": {
                                "type": "integer",
                                "description": "Time window in minutes",
                                "default": 5
                            }
                        }
                    }
                ),
                Tool(
                    name="get_model_recommendation",
                    description="Get model switching recommendation based on current resources",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target_model": {
                                "type": "string",
                                "description": "Target model name (qwen3-14b, qwen3-8b)",
                                "enum": ["qwen3-14b", "qwen3-8b"]
                            }
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                if name == "get_system_metrics":
                    include_gpu = arguments.get("include_gpu", True)
                    metrics = await self.get_system_metrics(include_gpu)
                    return [TextContent(
                        type="text",
                        text=json.dumps(metrics, indent=2, default=str)
                    )]
                
                elif name == "get_gpu_status":
                    device_id = arguments.get("device_id", 0)
                    gpu_data = await self.get_gpu_status(device_id)
                    return [TextContent(
                        type="text",
                        text=json.dumps(gpu_data, indent=2)
                    )]
                
                elif name == "scan_disks":
                    disk_data = scan_disks()
                    return [TextContent(
                        type="text",
                        text=json.dumps(disk_data, indent=2, default=str)
                    )]
                
                elif name == "scan_network":
                    network_data = scan_network_interfaces()
                    return [TextContent(
                        type="text",
                        text=json.dumps(network_data, indent=2, default=str)
                    )]
                
                elif name == "scan_docker":
                    docker_data = scan_docker_containers()
                    return [TextContent(
                        type="text",
                        text=json.dumps(docker_data, indent=2, default=str)
                    )]
                
                elif name == "start_file_monitoring":
                    directories = arguments.get("directories", ["/etc", "/home/abidan/spider", "/var/log"])
                    success = self.start_file_monitoring(directories)
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": success,
                            "message": "File monitoring started" if success else "Failed to start file monitoring"
                        }, indent=2)
                    )]
                
                elif name == "get_file_changes":
                    minutes = arguments.get("minutes", 5)
                    changes = self.get_file_changes(minutes)
                    return [TextContent(
                        type="text",
                        text=json.dumps(changes, indent=2, default=str)
                    )]
                
                elif name == "get_model_recommendation":
                    target_model = arguments.get("target_model", "qwen3-14b")
                    recommendation = await self.get_model_recommendation(target_model)
                    return [TextContent(
                        type="text",
                        text=json.dumps(recommendation, indent=2)
                    )]
                
                else:
                    raise ValueError(f"Unknown tool: {name}")
            
            except Exception as e:
                logger.error(f"Tool call error: {e}")
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}, indent=2)
                )]
    
    async def get_system_metrics(self, include_gpu: bool = True) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        disk_free_gb = disk.free / (1024**3)
        
        # Load average
        load_avg = os.getloadavg()
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "load_avg_1m": load_avg[0],
                "load_avg_5m": load_avg[1],
                "load_avg_15m": load_avg[2]
            },
            "memory": {
                "percent": memory_percent,
                "used_gb": memory_used_gb,
                "total_gb": memory_total_gb,
                "available_gb": memory.available / (1024**3)
            },
            "disk": {
                "usage_percent": disk_usage_percent,
                "free_gb": disk_free_gb,
                "total_gb": disk.total / (1024**3),
                "used_gb": disk.used / (1024**3)
            }
        }
        
        # GPU metrics
        if include_gpu and NVIDIA_AVAILABLE and self.device_count > 0:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                
                # Memory info
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                gpu_memory_used_gb = mem_info.used / (1024**3)
                gpu_memory_total_gb = mem_info.total / (1024**3)
                gpu_memory_percent = (mem_info.used / mem_info.total) * 100
                
                # Temperature
                gpu_temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                
                # Utilization
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_utilization = util.gpu
                
                # Power usage
                gpu_power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
                
                # Clock speeds
                graphics_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                memory_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
                
                metrics["gpu"] = {
                    "available": True,
                    "memory": {
                        "used_gb": gpu_memory_used_gb,
                        "total_gb": gpu_memory_total_gb,
                        "percent": gpu_memory_percent,
                        "free_gb": gpu_memory_total_gb - gpu_memory_used_gb
                    },
                    "utilization": {
                        "gpu_percent": gpu_utilization,
                        "memory_percent": util.memory
                    },
                    "temperature": {
                        "gpu_celsius": gpu_temperature
                    },
                    "power": {
                        "usage_watts": gpu_power_usage
                    },
                    "clocks": {
                        "graphics_mhz": graphics_clock,
                        "memory_mhz": memory_clock
                    }
                }
                
            except Exception as e:
                logger.warning(f"GPU monitoring error: {e}")
                metrics["gpu"] = {
                    "available": False,
                    "error": str(e)
                }
        else:
            metrics["gpu"] = {
                "available": False,
                "reason": "NVIDIA monitoring not available"
            }
        
        return metrics
    
    async def get_gpu_status(self, device_id: int = 0) -> Dict[str, Any]:
        """Get detailed GPU status"""
        if not NVIDIA_AVAILABLE or self.device_count == 0:
            return {"error": "NVIDIA monitoring not available"}
        
        if device_id >= self.device_count:
            return {"error": f"Device ID {device_id} out of range (0-{self.device_count-1})"}
        
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
            
            # Basic info
            name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
            driver_version = pynvml.nvmlSystemGetDriverVersion().decode('utf-8')
            
            # Memory info
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            
            # Performance info
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
            power_limit = pynvml.nvmlDeviceGetPowerManagementLimitConstraints(handle)[1] / 1000.0
            
            # Clock speeds
            graphics_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
            memory_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
            
            return {
                "device_id": device_id,
                "name": name,
                "driver_version": driver_version,
                "memory": {
                    "total_gb": mem_info.total / (1024**3),
                    "used_gb": mem_info.used / (1024**3),
                    "free_gb": mem_info.free / (1024**3),
                    "percent_used": (mem_info.used / mem_info.total) * 100
                },
                "utilization": {
                    "gpu_percent": util.gpu,
                    "memory_percent": util.memory
                },
                "temperature": {
                    "gpu_celsius": temperature
                },
                "power": {
                    "usage_watts": power_usage,
                    "limit_watts": power_limit,
                    "percent_used": (power_usage / power_limit) * 100
                },
                "clocks": {
                    "graphics_mhz": graphics_clock,
                    "memory_mhz": memory_clock
                }
            }
        
        except Exception as e:
            return {"error": f"Failed to get GPU status: {str(e)}"}
    
    def start_file_monitoring(self, directories: List[str]) -> bool:
        """Start file monitoring"""
        try:
            self.file_monitor = start_file_monitoring(directories)
            return self.file_monitor is not None
        except Exception as e:
            logger.error(f"Failed to start file monitoring: {e}")
            return False
    
    def get_file_changes(self, minutes: int = 5) -> Dict[str, Any]:
        """Get file changes from monitoring"""
        if not self.file_monitor:
            return {"error": "File monitoring not started"}
        
        try:
            return get_file_changes(self.file_monitor, minutes)
        except Exception as e:
            return {"error": f"Failed to get file changes: {str(e)}"}
    
    async def get_model_recommendation(self, target_model: str) -> Dict[str, Any]:
        """Get model switching recommendation based on current resources"""
        metrics = await self.get_system_metrics()
        
        recommendation = {
            "target_model": target_model,
            "current_resources": {
                "gpu_memory_used_gb": metrics.get("gpu", {}).get("memory", {}).get("used_gb", 0),
                "gpu_memory_total_gb": metrics.get("gpu", {}).get("memory", {}).get("total_gb", 0),
                "gpu_memory_percent": metrics.get("gpu", {}).get("memory", {}).get("percent", 0),
                "memory_used_gb": metrics.get("memory", {}).get("used_gb", 0),
                "memory_total_gb": metrics.get("memory", {}).get("total_gb", 0)
            },
            "recommendation": "unknown",
            "reason": "",
            "safe_to_switch": False
        }
        
        if target_model == "qwen3-14b":
            # Qwen3-14B needs ~10GB VRAM
            gpu_memory = metrics.get("gpu", {})
            if gpu_memory.get("available"):
                available_vram = gpu_memory["memory"]["free_gb"]
                if available_vram >= 10.5:  # 10GB + 0.5GB buffer
                    recommendation["recommendation"] = "switch_to_14b"
                    recommendation["reason"] = f"Sufficient VRAM available: {available_vram:.1f}GB"
                    recommendation["safe_to_switch"] = True
                elif available_vram >= 8.0:
                    recommendation["recommendation"] = "switch_with_caution"
                    recommendation["reason"] = f"Limited VRAM available: {available_vram:.1f}GB (may need to free memory)"
                    recommendation["safe_to_switch"] = False
                else:
                    recommendation["recommendation"] = "switch_to_8b"
                    recommendation["reason"] = f"Insufficient VRAM: {available_vram:.1f}GB available, need 10GB+"
                    recommendation["safe_to_switch"] = False
            else:
                recommendation["reason"] = "GPU monitoring not available"
        
        elif target_model == "qwen3-8b":
            # Qwen3-8B needs ~6GB VRAM
            gpu_memory = metrics.get("gpu", {})
            if gpu_memory.get("available"):
                available_vram = gpu_memory["memory"]["free_gb"]
                if available_vram >= 6.5:  # 6GB + 0.5GB buffer
                    recommendation["recommendation"] = "switch_to_8b"
                    recommendation["reason"] = f"Sufficient VRAM available: {available_vram:.1f}GB"
                    recommendation["safe_to_switch"] = True
                else:
                    recommendation["recommendation"] = "free_memory_first"
                    recommendation["reason"] = f"Insufficient VRAM: {available_vram:.1f}GB available, need 6GB+"
                    recommendation["safe_to_switch"] = False
            else:
                recommendation["reason"] = "GPU monitoring not available"
        
        return recommendation

async def main():
    """Main entry point"""
    server = MonitorServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="monitor",
                server_version="1.0.0",
                capabilities={}
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
