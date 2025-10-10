#!/usr/bin/env python3
# spider/llm/llm_analyzer.py

"""
unified spider llm analyzer
combines rule-based analysis with ollama integration
"""

import json
import requests
import os
from datetime import datetime
from typing import Dict, Any, List

class LLMAnalyzer:
    def __init__(self, model="llama3.1:8b", host="localhost:11434"):
        self.model = model
        self.ollama_host = f"http://{host}"
        self.analysis_history = []
        
    def check_ollama_health(self) -> bool:
        """check if ollama is running"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def query_ollama(self, prompt: str, max_tokens: int = 2000) -> str:
        """send prompt to ollama"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7
                }
            }
            
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "no response received")
            else:
                return f"error: http {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "error: request timeout"
        except Exception as e:
            return f"error: {str(e)}"
    
    def chunk_data(self, data: Dict, max_size: int = 50000) -> List[Dict]:
        """chunk large data for llm context limits"""
        data_str = json.dumps(data, default=str)
        
        if len(data_str) <= max_size:
            return [data]
        
        chunks = []
        for key, value in data.items():
            chunk = {key: value}
            chunk_str = json.dumps(chunk, default=str)
            
            if len(chunk_str) > max_size:
                if isinstance(value, dict):
                    sub_chunks = self.chunk_data(value, max_size)
                    for sub_chunk in sub_chunks:
                        chunks.append({f"{key}_part": sub_chunk})
                else:
                    chunks.append({key: str(value)[:max_size//2]})
            else:
                chunks.append(chunk)
        
        return chunks
    
    def analyze_system_health(self, snapshot: Dict) -> Dict[str, Any]:
        """analyze system health from snapshot"""
        issues = []
        recommendations = []
        
        # disk analysis
        if 'disk' in snapshot:
            disk_data = snapshot['disk']
            filesystems = disk_data.get('usage', [])
            
            for fs in filesystems:
                try:
                    usage_pct = int(fs.get('use_percent', '0%').rstrip('%'))
                    mount_point = fs.get('mount_point', fs.get('mountpoint', ''))
                    
<<<<<<< HEAD
                    # zimaos root partition exception
                    if mount_point == '/' and usage_pct == 100:
                        # check if this might be zimaos
                        size = fs.get('size', '')
                        if '1.' in size and 'G' in size:  # ~1.2g root partition
                            continue  # normal for zimaos
=======
                    # normal ubuntu server disk usage expectations
                    # no special exceptions needed for ubuntu server
>>>>>>> 0de83c2 (spider homelab monitoring system)
                    
                    if usage_pct > 90:
                        issues.append(f"high disk usage on {mount_point}: {usage_pct}%")
                        recommendations.append(f"clean up files on {mount_point} or expand storage")
                    elif usage_pct > 75:
                        issues.append(f"moderate disk usage on {mount_point}: {usage_pct}%")
                        recommendations.append(f"monitor disk usage on {mount_point}")
                except (ValueError, KeyError):
                    continue
        
        # docker analysis
        if 'docker' in snapshot:
            containers = snapshot['docker'].get('containers', [])
            exited_count = len([c for c in containers if 'exited' in c.get('status', '').lower()])
            
            if exited_count > 0:
                issues.append(f"{exited_count} docker containers in exited state")
                recommendations.append("check docker logs and restart failed containers")
        
        # remote server analysis
        if 'remote_servers' in snapshot:
            remote_data = snapshot['remote_servers']
            total_servers = remote_data.get('total_servers', 0)
            connected = remote_data.get('connected_servers', 0)
            
            if connected < total_servers:
                offline = total_servers - connected
                issues.append(f"{offline} remote servers offline")
                recommendations.append("check network connectivity to remote servers")
        
        return {
            'issues': issues,
            'recommendations': recommendations,
            'severity': 'high' if len(issues) > 5 else 'medium' if len(issues) > 2 else 'low'
        }
    
    def prepare_snapshot_summary(self, snapshot: Dict) -> Dict:
        """prepare summary for llm analysis"""
        summary = {
            "timestamp": snapshot.get("timestamp", "unknown"),
            "hostname": snapshot.get("hostname", "unknown"),
            "scan_type": "local_and_remote" if "remote_servers" in snapshot else "local_only"
        }
        
        # local system summary
        if "disk" in snapshot:
            filesystems = snapshot["disk"].get("usage", [])
            
            summary["storage"] = {
                "filesystems_count": len(filesystems),
                "high_usage": [
                    f"{fs.get('mount_point', fs.get('mountpoint', '?'))}: {fs['use_percent']}" 
                    for fs in filesystems 
                    if int(fs.get('use_percent', '0%').rstrip('%')) > 80
                ],
                "total_usage": [
                    f"{fs.get('mount_point', fs.get('mountpoint', '?'))}: {fs['use_percent']} ({fs.get('used', '?')}/{fs.get('size', '?')})"
                    for fs in filesystems[:5]
                ]
            }
        
        # docker summary
        if "docker" in snapshot:
            containers = snapshot["docker"].get("containers", [])
            summary["docker"] = {
                "total_containers": len(containers),
                "running": len([c for c in containers if "up" in c.get("status", "").lower()]),
                "stopped": len([c for c in containers if "exited" in c.get("status", "").lower()]),
                "container_list": [f"{c.get('name', '?')}: {c.get('status', '?')}" for c in containers[:10]]
            }
        
        # network summary
        if "network" in snapshot:
            listening_ports = snapshot["network"].get("listening_ports", "")
            summary["network"] = {
                "interfaces_scanned": True,
                "listening_services": listening_ports.count("LISTEN") if listening_ports else 0
            }
        
        # remote servers summary
        if "remote_servers" in snapshot:
            remote_data = snapshot["remote_servers"]
            summary["remote_servers"] = {
                "total": remote_data.get("total_servers", 0),
                "connected": remote_data.get("connected_servers", 0),
                "servers": {}
            }
            
            for server_name, server_data in remote_data.get("servers", {}).items():
                if server_data.get("connection_status") == "connected":
                    # extract docker container count from output
                    docker_stdout = server_data.get("docker_containers", {}).get("stdout", "")
                    container_count = max(0, docker_stdout.count("\n") - 1) if docker_stdout else 0
                    
                    summary["remote_servers"]["servers"][server_name] = {
                        "hostname": server_data.get("hostname", "unknown"),
                        "status": "online",
                        "docker_containers": container_count,
                        "disk_usage": self.extract_remote_disk_summary(server_data)
                    }
                else:
                    summary["remote_servers"]["servers"][server_name] = {
                        "status": "offline",
                        "error": server_data.get("error", "unknown")
                    }
        
        return summary
    
    def extract_remote_disk_summary(self, server_data: Dict) -> List[str]:
        """extract disk usage from remote server data"""
        disk_output = server_data.get("disk_usage", {}).get("stdout", "")
        if not disk_output:
            return []
        
        usage_lines = []
        lines = disk_output.split('\n')[1:]  # skip header
        for line in lines[:5]:  # top 5 filesystems
            parts = line.split()
            if len(parts) >= 6:
                usage_lines.append(f"{parts[5]}: {parts[4]} ({parts[2]}/{parts[1]})")
        
        return usage_lines
    
<<<<<<< HEAD
    def create_zimaos_aware_prompt(self, summary_data: Dict) -> str:
        """create analysis prompt with zimaos knowledge"""
        
        zimaos_knowledge = """
        zimaos architecture knowledge:
        - zimaos uses small root partition (1-6gb) and large data partition (400gb+)
        - root partition at 100% usage is normal and expected behavior
        - main data storage is on /data partition
        - casaos manages containerized applications
        - multiple overlay mounts for different services
        - small root partition contains only os files, not user data
=======
    def create_casaos_aware_prompt(self, summary_data: Dict) -> str:
        """create analysis prompt with casaos knowledge"""
        
        casaos_knowledge = """
        casaos on ubuntu server architecture knowledge:
        - casaos runs on standard ubuntu server with normal partitioning
        - casaos manages containerized applications via docker
        - normal ubuntu disk usage expectations apply (no special exceptions)
        - casaos provides web interface for app management
        - home assistant typically runs as KVM VM
        - standard ubuntu server monitoring applies
>>>>>>> 0de83c2 (spider homelab monitoring system)
        """
        
        prompt = f"""you are spider, an expert homelab system administrator ai. analyze this system snapshot and provide actionable insights.

<<<<<<< HEAD
{zimaos_knowledge}
=======
{casaos_knowledge}
>>>>>>> 0de83c2 (spider homelab monitoring system)

system snapshot data:
{json.dumps(summary_data, indent=2)}

provide analysis in this format:

# 🕷️ spider intelligence report

## 🏥 system health status
[overall health assessment: excellent/good/warning/critical]

## 🚨 critical issues
[list any critical problems requiring immediate attention]

## ⚠️ warnings
[list moderate issues that should be monitored]

## 📊 key metrics
[important system statistics and trends]

## 💡 recommendations
[specific actionable recommendations for improvement]

## 🔮 predictions
[what might happen if current trends continue]

<<<<<<< HEAD
important zimaos rules:
- for zimaos servers: root partition at 100% is normal, focus on /data partition health
- distinguish between system partitions and data partitions
- casaos containers are expected and normal
=======
important casaos rules:
- for casaos servers: normal ubuntu server disk usage expectations apply
- casaos containers are expected and normal
- home assistant VM status should be monitored
- focus on standard ubuntu server health metrics
>>>>>>> 0de83c2 (spider homelab monitoring system)

be specific, practical, and focus on actionable insights."""

        return prompt
    
    def generate_rule_based_summary(self, snapshot: Dict) -> str:
        """generate rule-based summary as fallback"""
        timestamp = snapshot.get('timestamp', 'unknown')
        hostname = snapshot.get('hostname', 'unknown')
        
        summary = f"# spider analysis report\n"
        summary += f"**host:** {hostname}\n"
        summary += f"**scan time:** {timestamp}\n\n"
        
        # system overview
        if 'disk' in snapshot:
            filesystems = snapshot['disk'].get('usage', [])
            summary += f"**storage:** {len(filesystems)} filesystems scanned\n"
        
        if 'docker' in snapshot:
            containers = snapshot['docker'].get('containers', [])
            running = len([c for c in containers if 'up' in c.get('status', '').lower()])
            summary += f"**docker:** {running}/{len(containers)} containers running\n"
        
        if 'remote_servers' in snapshot:
            remote_data = snapshot['remote_servers']
            connected = remote_data.get('connected_servers', 0)
            total = remote_data.get('total_servers', 0)
            summary += f"**remote servers:** {connected}/{total} connected\n"
        
        # health analysis
        health = self.analyze_system_health(snapshot)
        summary += f"\n## health assessment\n"
        summary += f"**severity:** {health['severity']}\n"
        summary += f"**issues found:** {len(health['issues'])}\n\n"
        
        if health['issues']:
            summary += "### issues detected\n"
            for issue in health['issues']:
                summary += f"- {issue}\n"
            summary += "\n"
        
        if health['recommendations']:
            summary += "### recommendations\n"
            for rec in health['recommendations']:
                summary += f"- {rec}\n"
            summary += "\n"
        
        return summary
    
    def analyze_system(self, snapshot: Dict) -> str:
        """main analysis function - uses ollama if available, falls back to rules"""
        
        # try ollama first
        if self.check_ollama_health():
            print("[*] analyzing with llama 3.1 8b...")
            try:
                summary_data = self.prepare_snapshot_summary(snapshot)
<<<<<<< HEAD
                prompt = self.create_zimaos_aware_prompt(summary_data)
=======
                prompt = self.create_casaos_aware_prompt(summary_data)
>>>>>>> 0de83c2 (spider homelab monitoring system)
                analysis = self.query_ollama(prompt, max_tokens=3000)
                
                # add metadata
                full_analysis = f"""# spider llm analysis report
**generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**model:** {self.model}
**snapshot id:** {snapshot.get('scan_id', 'unknown')}

---

{analysis}

---

*analysis powered by spider intelligence system with llama 3.1*
"""
                
                # save to history
                self.analysis_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'model': self.model,
                    'type': 'llm_analysis',
                    'snapshot_id': snapshot.get('scan_id', 'unknown')
                })
                
                return full_analysis
                
            except Exception as e:
                print(f"[!] llm analysis failed: {e}")
                print("[*] falling back to rule-based analysis...")
        else:
            print("[!] ollama not available, using rule-based analysis...")
        
        # fallback to rule-based analysis
        rule_analysis = self.generate_rule_based_summary(snapshot)
        
        self.analysis_history.append({
            'timestamp': datetime.now().isoformat(),
            'model': 'rule_based',
            'type': 'fallback_analysis',
            'snapshot_id': snapshot.get('scan_id', 'unknown')
        })
        
        return rule_analysis
    
    def compare_snapshots(self, current: Dict, previous: Dict) -> str:
        """compare two snapshots for changes"""
        
        # try llm comparison first
        if self.check_ollama_health():
            try:
                current_summary = self.prepare_snapshot_summary(current)
                previous_summary = self.prepare_snapshot_summary(previous)
                
                prompt = f"""you are spider, analyzing changes between two system snapshots. compare these snapshots and identify significant changes, trends, and potential issues.

current snapshot:
{json.dumps(current_summary, indent=2)}

previous snapshot:
{json.dumps(previous_summary, indent=2)}

provide analysis in this format:

# 📈 spider change analysis

## 🔄 key changes detected
[list the most significant changes]

## 📊 trends analysis
[what trends are emerging from these changes]

## ⚠️ concerns
[any changes that might indicate problems]

## 👍 improvements
[positive changes or optimizations detected]

## 🎯 action items
[specific actions recommended based on changes]

focus on actionable insights and avoid mentioning minor fluctuations."""

                analysis = self.query_ollama(prompt, max_tokens=2000)
                
                return f"""# spider change analysis report
**generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**model:** {self.model}
**comparison period:** {previous.get('timestamp', 'unknown')} → {current.get('timestamp', 'unknown')}

---

{analysis}

---

*analysis powered by spider intelligence system with llama 3.1*
"""
                
            except Exception as e:
                print(f"[!] llm comparison failed: {e}, using rule-based...")
        
        # fallback rule-based comparison
        changes = []
        
        # compare disk usage
        curr_disk = current.get('disk', {}).get('usage', [])
        prev_disk = previous.get('disk', {}).get('usage', [])
        
        curr_fs = {fs.get('mount_point', fs.get('mountpoint')): fs for fs in curr_disk}
        prev_fs = {fs.get('mount_point', fs.get('mountpoint')): fs for fs in prev_disk}
        
        for mount in curr_fs:
            if mount in prev_fs:
                curr_usage = curr_fs[mount].get('use_percent', '0%')
                prev_usage = prev_fs[mount].get('use_percent', '0%')
                
                try:
                    curr_pct = int(curr_usage.rstrip('%'))
                    prev_pct = int(prev_usage.rstrip('%'))
                    diff = curr_pct - prev_pct
                    
                    if abs(diff) >= 5:
                        changes.append(f"disk usage on {mount}: {prev_pct}% -> {curr_pct}% ({diff:+d}%)")
                except ValueError:
                    continue
        
        # compare docker containers
        curr_containers = len(current.get('docker', {}).get('containers', []))
        prev_containers = len(previous.get('docker', {}).get('containers', []))
        
        if curr_containers != prev_containers:
            changes.append(f"docker containers: {prev_containers} -> {curr_containers}")
        
        if changes:
            return "# snapshot comparison\n\n" + "\n".join(f"- {change}" for change in changes)
        else:
            return "# snapshot comparison\n\nno significant changes detected."
    
    def test_connection(self) -> bool:
        """test ollama connection with spider-specific test"""
        if not self.check_ollama_health():
            return False
        
        test_response = self.query_ollama("respond with exactly: spider llm is working!", max_tokens=20)
        return "spider llm is working" in test_response.lower()

# convenience functions for main spider
def analyze_system_enhanced(snapshot: Dict) -> str:
    """enhanced system analysis using unified analyzer"""
    analyzer = LLMAnalyzer()
    return analyzer.analyze_system(snapshot)

def compare_snapshots_enhanced(current: Dict, previous: Dict) -> str:
    """enhanced snapshot comparison using unified analyzer"""
    analyzer = LLMAnalyzer()
    return analyzer.compare_snapshots(current, previous)

def create_analyzer(model="llama3.1:8b", host="localhost:11434") -> LLMAnalyzer:
    """factory function to create analyzer"""
    return LLMAnalyzer(model=model, host=host)