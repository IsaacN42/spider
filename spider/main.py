#!/usr/bin/env python3
"""
enhanced spider main with week 1 memory integration
adds osquery, file relationships, inotify, and knowledge graph
"""

import sys
import os
import argparse
import time
import json
from datetime import datetime

# add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# new week 1 imports
from scanners.osquery_scanner import scan_with_osquery
from scanners.file_relationships import scan_file_relationships
from scanners.inotify_monitor import start_file_monitoring, get_file_changes
from storage.knowledge_graph import create_knowledge_graph, update_graph_from_spider_data

def enhanced_scan(include_remote=False, include_analysis=False, include_memory=True):
    """enhanced scan with memory integration features"""
    snapshot_data = {}
    
    try:
        # existing spider scanners
        from scanners.filesystem_scanner import scan_important_configs
        from scanners.disk_scanner import scan_disks
        from scanners.network_scanner import scan_network_interfaces
        from scanners.docker_scanner import scan_docker_containers
        
        print(f"[*] starting enhanced spider scan at {datetime.now()}")
        
        # week 1 enhancement: initialize knowledge graph
        if include_memory:
            print("[*] initializing knowledge graph...")
            try:
                kg = create_knowledge_graph()
                print("[✓] knowledge graph ready")
            except Exception as e:
                print(f"[!] knowledge graph failed: {e}")
                kg = None
        
        # existing local scans
        print("[*] scanning local filesystem...")
        configs = scan_important_configs()
        snapshot_data['filesystem'] = configs
        print(f"[✓] scanned {len(configs)} config directories")
        
        # week 1 enhancement: osquery integration
        if include_memory:
            print("[*] deep system scan with osquery...")
            try:
                osquery_data = scan_with_osquery()
                if 'error' not in osquery_data:
                    snapshot_data['osquery'] = osquery_data
                    print("[✓] osquery scan completed")
                else:
                    print("[!] osquery not available - install with: apt install osquery")
            except Exception as e:
                print(f"[!] osquery scan failed: {e}")
        
        # week 1 enhancement: file relationships
        if include_memory:
            print("[*] mapping file relationships...")
            try:
                rel_data = scan_file_relationships(['/etc', '/opt/spider', '/var/log'])
                snapshot_data['file_relationships'] = rel_data
                total_connections = rel_data['summary']['total_connections']
                print(f"[✓] mapped {total_connections} file relationships")
            except Exception as e:
                print(f"[!] relationship mapping failed: {e}")
        
        # existing system scans
        print("[*] checking local system status...")
        
        disk_data = scan_disks()
        snapshot_data['disk'] = disk_data
        filesystems = len(disk_data.get('usage', []))
        print(f"[✓] disk usage: {filesystems} mounted filesystems")
        
        network_data = scan_network_interfaces()
        snapshot_data['network'] = network_data
        listening_count = network_data.get('listening_ports', '').count('LISTEN')
        print(f"[✓] network services: {listening_count} listening ports")
        
        docker_data = scan_docker_containers()
        snapshot_data['docker'] = docker_data
        container_count = len(docker_data.get('containers', []))
        running_count = len([c for c in docker_data.get('containers', []) if 'Up' in c.get('status', '')])
        print(f"[✓] docker containers: {running_count}/{container_count} running")
        
        # remote scans (existing functionality)
        if include_remote:
            print("[*] initiating remote server scans...")
            try:
                from scanners.remote_scanner import scan_remote_servers
                remote_results = scan_remote_servers()
                snapshot_data['remote_servers'] = remote_results
                
                server_count = len(remote_results.get('servers', {}))
                connected = sum(1 for s in remote_results.get('servers', {}).values() 
                              if s.get('connection_status') == 'connected')
                print(f"[✓] remote servers: {connected}/{server_count} connected")
            except Exception as e:
                print(f"[!] remote scan error: {e}")
        
        # week 1 enhancement: update knowledge graph
        if include_memory and kg:
            print("[*] updating knowledge graph...")
            try:
                update_graph_from_spider_data(kg, snapshot_data)
                stats = kg.get_relationship_stats()
                print(f"[✓] knowledge graph: {stats['total_files']} files, {stats['total_relationships']} relationships")
                kg.close()
            except Exception as e:
                print(f"[!] knowledge graph update failed: {e}")
        
        # save enhanced snapshot
        scan_type = "enhanced"
        if include_remote:
            scan_type += "_remote"
        snapshot_path = save_snapshot(snapshot_data, scan_type)
        if snapshot_path:
            print(f"[✓] snapshot saved: {snapshot_path}")
        
        # ai analysis (existing functionality)
        if include_analysis:
            print("[*] starting ai analysis...")
            try:
                from llm.llm_analyzer import LLMAnalyzer
                
                analyzer = LLMAnalyzer()
                
                if analyzer.check_ollama_health():
                    print("[✓] ollama connection verified")
                else:
                    print("[!] ollama not available - using rule-based analysis")
                
                analysis = analyzer.analyze_system(snapshot_data)
                
                # save analysis
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_path = f"/opt/spider/logs/reports/enhanced_analysis_{timestamp}.md"
                os.makedirs("/opt/spider/logs/reports", exist_ok=True)
                
                with open(report_path, 'w') as f:
                    f.write(analysis)
                
                print(f"[✓] enhanced analysis saved: {report_path}")
                
            except Exception as e:
                print(f"[!] analysis error: {e}")
        
        print(f"[✓] enhanced spider scan complete at {datetime.now()}")
        return True
        
    except Exception as e:
        print(f"[✗] enhanced scan failed: {e}")
        return False

def start_memory_daemon(watch_dirs=None):
    """start file monitoring daemon"""
    if watch_dirs is None:
        watch_dirs = ['/etc', '/opt/spider', '/var/log']
    
    print("[*] starting memory daemon...")
    tracker = start_file_monitoring(watch_dirs)
    
    if tracker is None:
        print("[!] file monitoring not available")
        return False
    
    print(f"[✓] monitoring {len(watch_dirs)} directories")
    
    try:
        while True:
            # poll for events
            events = tracker.poll_events(timeout=5.0)
            
            if events:
                print(f"[*] detected {len(events)} file changes")
                for event in events[:5]:  # show first 5
                    types = ', '.join(event['event_types'])
                    print(f"    {event['filename']}: {types}")
            
            # periodic summary every 5 minutes
            if int(time.time()) % 300 == 0:
                summary = get_file_changes(tracker, minutes=5)
                if summary['total_events'] > 0:
                    print(f"[*] 5min summary: {summary['total_events']} changes to {len(summary['files_changed'])} files")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[*] stopping memory daemon...")
        tracker.stop_tracking()
        return True

def query_knowledge_graph(pattern=None, file_type=None, relationship_type=None):
    """query the knowledge graph"""
    try:
        kg = create_knowledge_graph()
        
        if pattern:
            print(f"[*] searching files matching: {pattern}")
            results = kg.search_files(pattern, file_type)
            print(f"[✓] found {len(results)} files")
            
            for result in results[:10]:
                print(f"    {result['path']} ({result['type']}, {result['size']} bytes)")
        
        elif relationship_type:
            print(f"[*] analyzing {relationship_type} relationships...")
            stats = kg.get_relationship_stats()
            rel_count = stats['relationship_types'].get(relationship_type, 0)
            print(f"[✓] found {rel_count} {relationship_type} relationships")
        
        else:
            print("[*] knowledge graph statistics:")
            stats = kg.get_relationship_stats()
            
            print(f"    files: {stats['total_files']}")
            print(f"    relationships: {stats['total_relationships']}")
            print("    top relationship types:")
            
            for rel_type, count in list(stats['relationship_types'].items())[:5]:
                print(f"      {rel_type}: {count}")
        
        # show most connected files
        print("\n[*] most connected files:")
        connected = kg.get_most_connected_files(5)
        for file_info in connected:
            print(f"    {file_info['path']}: {file_info['connections']} connections")
        
        kg.close()
        return True
        
    except Exception as e:
        print(f"[!] knowledge graph query failed: {e}")
        return False

def save_snapshot(data: dict, scan_type: str = "enhanced") -> str:
    """save enhanced scan data"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{scan_type}_scan_{timestamp}.json"
    filepath = f"/opt/spider/logs/snapshots/{filename}"
    
    os.makedirs("/opt/spider/logs/snapshots", exist_ok=True)
    
    data.update({
        "scan_id": filename.replace('.json', ''),
        "timestamp": datetime.now().isoformat(),
        "scan_type": scan_type,
        "spider_version": "enhanced_v1.0"
    })
    
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return filepath
    except Exception as e:
        print(f"[!] failed to save snapshot: {e}")
        return ""

def main():
    parser = argparse.ArgumentParser(description='enhanced spider with memory integration')
    parser.add_argument('--scan', action='store_true', help='run enhanced system scan')
    parser.add_argument('--daemon', action='store_true', help='run as continuous daemon')
    parser.add_argument('--memory-daemon', action='store_true', help='run file monitoring daemon')
    parser.add_argument('--remote', action='store_true', help='include remote server scanning')
    parser.add_argument('--analyze', action='store_true', help='include ai analysis')
    parser.add_argument('--no-memory', action='store_true', help='disable memory features')
    parser.add_argument('--query', type=str, help='query knowledge graph')
    parser.add_argument('--file-type', type=str, help='filter by file type')
    parser.add_argument('--rel-type', type=str, help='analyze relationship type')
    parser.add_argument('--test-osquery', action='store_true', help='test osquery integration')
    parser.add_argument('--interval', type=int, default=30, help='daemon interval (minutes)')
    
    args = parser.parse_args()
    
    print("🕷️  enhanced spider with memory integration")
    print("=" * 50)
    print(f"[*] starting at {datetime.now()}")
    
    if args.test_osquery:
        print("[*] testing osquery integration...")
        try:
            result = scan_with_osquery()
            if 'error' in result:
                print(f"[!] {result['error']}")
                print("    install with: sudo apt install osquery")
                return 1
            else:
                print("[✓] osquery working")
                print(f"    hostname: {result.get('system_state', {}).get('hostname', 'unknown')}")
                return 0
        except Exception as e:
            print(f"[!] osquery test failed: {e}")
            return 1
    
    elif args.query:
        success = query_knowledge_graph(args.query, args.file_type, args.rel_type)
        return 0 if success else 1
    
    elif args.memory_daemon:
        success = start_memory_daemon()
        return 0 if success else 1
    
    elif args.scan:
        print("[*] running enhanced comprehensive scan...")
        include_memory = not args.no_memory
        success = enhanced_scan(
            include_remote=args.remote, 
            include_analysis=args.analyze,
            include_memory=include_memory
        )
        return 0 if success else 1
    
    elif args.daemon:
        print(f"[*] enhanced daemon mode (scan every {args.interval} minutes)...")
        include_memory = not args.no_memory
        scan_count = 0
        
        while True:
            try:
                scan_count += 1
                print(f"\n[*] enhanced scan #{scan_count} at {datetime.now()}")
                success = enhanced_scan(
                    include_remote=args.remote,
                    include_analysis=args.analyze,
                    include_memory=include_memory
                )
                
                if success:
                    print(f"[✓] scan #{scan_count} completed")
                else:
                    print(f"[!] scan #{scan_count} had errors")
                
                sleep_seconds = args.interval * 60
                print(f"[*] sleeping for {args.interval} minutes...")
                time.sleep(sleep_seconds)
                
            except KeyboardInterrupt:
                print(f"\n[*] enhanced spider daemon stopping after {scan_count} scans...")
                break
    
    else:
        print("[*] enhanced spider commands:")
        print("  --scan                    # enhanced local scan")
        print("  --scan --remote           # enhanced scan + remote servers")  
        print("  --scan --analyze          # enhanced scan + ai analysis")
        print("  --scan --no-memory        # disable memory features")
        print("  --memory-daemon           # start file monitoring")
        print("  --query pattern           # query knowledge graph")
        print("  --test-osquery            # test osquery integration")
        print("  --daemon                  # continuous enhanced scanning")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())