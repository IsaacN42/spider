#!/usr/bin/env python3
# spider/llm/llm_analyzer.py
# unified spider llm analyzer with casaos awareness

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
    
    def analyze_system_health(self, snapshot: Dict) -> Dict[str, Any]:
        """analyze system health from snapshot"""
        issues = []
        recommendations = []
        
        # disk analysis
        if 'disks' in snapshot:
            # handle new disk structure
            mounts = snapshot['disks'].get('mounts', [])
            for mount in mounts:
                try:
                    usage_pct = int(mount.get('use_percent', '0%').rstrip('%'))
                    mount_point = mount.get('mount_point', '')
                    
                    if usage_pct > 90:
                        issues.append(f"high disk usage on {mount_point}: {usage_pct}%")
                        recommendations.append(f"clean up files on {mount_point}")
                    elif usage_pct > 75:
                        issues.append(f"moderate disk usage on {mount_point}: {usage_pct}%")
                        recommendations.append(f"monitor {mount_point}")
                except (ValueError, KeyError):
                    continue
        
        # docker analysis
        if 'docker' in snapshot:
            containers = snapshot['docker'].get('containers', [])
            exited = [c for c in containers if 'exited' in c.get('status', '').lower()]
            
            if exited:
                issues.append(f"{len(exited)} containers in exited state")
                recommendations.append("check logs and restart failed containers")
        
        return {
            'issues': issues,
            'recommendations': recommendations,
            'severity': 'high' if len(issues) > 5 else 'medium' if len(issues) > 2 else 'low'
        }
    
    def prepare_snapshot_summary(self, snapshot: Dict) -> Dict:
        """prepare summary for llm analysis"""
        summary = {
            "timestamp": snapshot.get("timestamp", "unknown"),
            "hostname": snapshot.get("hostname", "unknown")
        }
        
        # storage summary
        if "disks" in snapshot:
            mounts = snapshot["disks"].get("mounts", [])
            summary["storage"] = {
                "physical_disks": len(snapshot["disks"].get("physical_disks", [])),
                "partitions": len(snapshot["disks"].get("partitions", [])),
                "mounted_filesystems": len(mounts),
                "high_usage": [
                    f"{m['mount_point']}: {m['use_percent']}" 
                    for m in mounts 
                    if int(m.get('use_percent', '0%').rstrip('%')) > 80
                ]
            }
        
        # docker summary
        if "docker" in snapshot:
            containers = snapshot["docker"].get("containers", [])
            summary["docker"] = {
                "total": len(containers),
                "running": len([c for c in containers if "up" in c.get("status", "").lower()]),
                "stopped": len([c for c in containers if "exited" in c.get("status", "").lower()])
            }
        
        return summary
    
    def create_analysis_prompt(self, summary_data: Dict) -> str:
        """create casaos-aware analysis prompt"""
        
        casaos_context = """
system context:
- ubuntu server with casaos for container management
- standard linux disk usage patterns apply
- casaos containers are normal and expected
- monitor standard ubuntu server health metrics
"""
        
        prompt = f"""you are spider, a homelab system administrator ai. analyze this system snapshot.

{casaos_context}

snapshot data:
{json.dumps(summary_data, indent=2)}

provide analysis:

# system health status
[overall assessment: excellent/good/warning/critical]

# issues found
[list critical problems requiring attention]

# warnings
[list moderate issues to monitor]

# key metrics
[important statistics]

# recommendations
[specific actionable recommendations]

be specific and focus on actionable insights."""

        return prompt
    
    def analyze_system(self, snapshot: Dict) -> str:
        """main analysis - uses ollama if available"""
        
        if self.check_ollama_health():
            print("[*] analyzing with llm...")
            try:
                summary_data = self.prepare_snapshot_summary(snapshot)
                prompt = self.create_analysis_prompt(summary_data)
                analysis = self.query_ollama(prompt, max_tokens=3000)
                
                full_analysis = f"""# spider llm analysis
**generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**model:** {self.model}

{analysis}

*powered by spider intelligence system*
"""
                
                self.analysis_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'model': self.model,
                    'type': 'llm_analysis'
                })
                
                return full_analysis
                
            except Exception as e:
                print(f"[!] llm failed: {e}, using fallback...")
        else:
            print("[!] ollama unavailable, using rule-based analysis...")
        
        # fallback
        health = self.analyze_system_health(snapshot)
        summary = f"""# spider analysis
**time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## health assessment
**severity:** {health['severity']}
**issues:** {len(health['issues'])}

"""
        
        if health['issues']:
            summary += "### issues\n"
            for issue in health['issues']:
                summary += f"- {issue}\n"
            summary += "\n"
        
        if health['recommendations']:
            summary += "### recommendations\n"
            for rec in health['recommendations']:
                summary += f"- {rec}\n"
        
        return summary
    
    def test_connection(self) -> bool:
        """test ollama connection"""
        if not self.check_ollama_health():
            return False
        
        response = self.query_ollama("respond: spider llm working", max_tokens=20)
        return "spider llm working" in response.lower()

# convenience functions
def analyze_system_enhanced(snapshot: Dict) -> str:
    analyzer = LLMAnalyzer()
    return analyzer.analyze_system(snapshot)

def create_analyzer(model="llama3.1:8b", host="localhost:11434") -> LLMAnalyzer:
    return LLMAnalyzer(model=model, host=host)