#!/usr/bin/env python3
# spider/main.py

import sys
import os
import argparse
import time
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# spider imports
from spider.scanners.osquery import scan_with_osquery
from spider.scanners.file_relationships import scan_file_relationships
from spider.scanners.inotify_monitor import start_file_monitoring, get_file_changes
from spider.storage.knowledge_graph import create_knowledge_graph, update_graph_from_spider_data
from spider.scanners.filesystem import scan_important_configs
from spider.scanners.disk import scan_disks
from spider.scanners.network import scan_network_interfaces
from spider.scanners.docker import scan_docker_containers
from spider.llm.llm_analyzer import LLMAnalyzer
from spider.scanners.remote import RemoteScanner

class SpiderEnhanced:
    def __init__(self):
        self.config = self._load_config()
        self.knowledge_graph = None
        
    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'spider_config.yml')
        
        default_config = {
            'scan_directories': ['/etc', '/home/abidan/spider', '/var/log'],
            'remote_servers': {},
            'ollama_host': 'localhost:11434',
            'data_path': 'data',
            'log_path': 'logs'
        }
        
        # try to load yaml if available
        try:
            import yaml
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                default_config.update(user_config)
        except:
            pass
            
        return default_config
    
    def run_enhanced_scan(self, include_remote=False, include_analysis=False, include_memory=True):
        snapshot_data = {}
        
        try:
            print(f"[*] starting enhanced spider scan at {datetime.now()}")
            
            # initialize knowledge graph
            if include_memory:
                print("[*] initializing knowledge graph...")
                try:
                    self.knowledge_graph = create_knowledge_graph(
                        os.path.join(self.config['data_path'], 'knowledge.db')
                    )
                    print("[✓] knowledge graph ready")
                except Exception as e:
                    print(f"[!] knowledge graph failed: {e}")
                    self.knowledge_graph = None
            
            # local scans
            print("[*] scanning local system...")
            
            try:
                configs = scan_important_configs()
                snapshot_data['filesystem'] = configs
                print(f"[✓] scanned config directories")
            except Exception as e:
                print(f"[!] filesystem scan failed: {e}")
            
            try:
                disk_data = scan_disks()
                snapshot_data['disks'] = disk_data
                print(f"[✓] disk: {disk_data['summary']['physical_disk_count']} disks, {disk_data['summary']['mounted_filesystem_count']} filesystems")
            except Exception as e:
                print(f"[!] disk scan failed: {e}")
            
            try:
                network_data = scan_network_interfaces()
                snapshot_data['network'] = network_data
                print(f"[✓] network scan complete")
            except Exception as e:
                print(f"[!] network scan failed: {e}")
            
            try:
                docker_data = scan_docker_containers()
                snapshot_data['docker'] = docker_data
                running = len([c for c in docker_data.get('containers', []) if 'Up' in c.get('status', '')])
                total = len(docker_data.get('containers', []))
                print(f"[✓] docker: {running}/{total} containers running")
            except Exception as e:
                print(f"[!] docker scan failed: {e}")
            
            # remote servers
            if include_remote:
                print("[*] scanning remote servers...")
                try:
                    remote_scanner = RemoteScanner(self.config)
                    remote_results = remote_scanner.scan_remote_servers()
                    snapshot_data['remote_servers'] = remote_results
                    print(f"[✓] remote scan complete")
                except Exception as e:
                    print(f"[!] remote scan failed: {e}")
            
            # update knowledge graph
            if include_memory and self.knowledge_graph:
                print("[*] updating knowledge graph...")
                try:
                    update_graph_from_spider_data(self.knowledge_graph, snapshot_data)
                    stats = self.knowledge_graph.get_database_stats()
                    print(f"[✓] knowledge: {stats['total_files']} files, {stats['total_relationships']} relationships")
                    self.knowledge_graph.close_connection()
                except Exception as e:
                    print(f"[!] knowledge update failed: {e}")
            
            # save snapshot
            snapshot_path = self._save_snapshot(snapshot_data, "enhanced")
            if snapshot_path:
                print(f"[✓] saved: {snapshot_path}")
            
            # ai analysis
            if include_analysis:
                print("[*] running ai analysis...")
                try:
                    analyzer = LLMAnalyzer()
                    
                    if analyzer.check_ollama_health():
                        print("[✓] ollama connected")
                    else:
                        print("[!] ollama offline - using fallback")
                    
                    analysis = analyzer.analyze_system(snapshot_data)
                    
                    # save analysis
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    report_path = os.path.join(self.config['log_path'], 'reports', f'analysis_{timestamp}.md')
                    os.makedirs(os.path.dirname(report_path), exist_ok=True)
                    
                    with open(report_path, 'w') as f:
                        f.write(analysis)
                    
                    print(f"[✓] analysis saved: {report_path}")
                    
                except Exception as e:
                    print(f"[!] analysis error: {e}")
            
            print(f"[✓] scan complete at {datetime.now()}")
            return True
            
        except Exception as e:
            print(f"[✗] scan failed: {e}")
            return False
    
    def _save_snapshot(self, data, scan_type="enhanced"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{scan_type}_{timestamp}.json"
        filepath = os.path.join(self.config['log_path'], 'snapshots', filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        data.update({
            "scan_id": filename.replace('.json', ''),
            "timestamp": datetime.now().isoformat(),
            "scan_type": scan_type
        })
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return filepath
        except Exception as e:
            print(f"[!] save failed: {e}")
            return ""

def main():
    parser = argparse.ArgumentParser(description='spider enhanced')
    parser.add_argument('--scan', action='store_true', help='run scan')
    parser.add_argument('--remote', action='store_true', help='include remote')
    parser.add_argument('--analyze', action='store_true', help='ai analysis')
    parser.add_argument('--no-memory', action='store_true', help='disable memory')
    
    args = parser.parse_args()
    
    print("🕷️  spider enhanced")
    print("=" * 50)
    
    spider = SpiderEnhanced()
    
    if args.scan:
        success = spider.run_enhanced_scan(
            include_remote=args.remote,
            include_analysis=args.analyze,
            include_memory=not args.no_memory
        )
        return 0 if success else 1
    else:
        print("usage:")
        print("  --scan           # local scan")
        print("  --scan --remote  # + remote servers")
        print("  --scan --analyze # + ai analysis")
        return 1

if __name__ == '__main__':
    sys.exit(main())