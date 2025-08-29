#!/usr/bin/env python3
import sys
import os
import argparse
import time
import json
from datetime import datetime

# add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def save_snapshot(data: dict, scan_type: str = "full") -> str:
    """save scan data as json snapshot"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{scan_type}_scan_{timestamp}.json"
    filepath = f"/opt/spider/logs/snapshots/{filename}"
    
    # ensure directory exists
    os.makedirs("/opt/spider/logs/snapshots", exist_ok=True)
    
    # add metadata
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
        print(f"[!] failed to save snapshot: {e}")
        return ""

def run_scan(include_remote=False, include_analysis=False):
    """run comprehensive scan with optional ai analysis"""
    snapshot_data = {}
    
    try:
        from scanners.filesystem_scanner import scan_important_configs
        from scanners.disk_scanner import scan_disks
        from scanners.network_scanner import scan_network_interfaces
        from scanners.docker_scanner import scan_docker_containers
        from executor.command_executor import CommandExecutor
        
        print(f"[*] starting spider scan at {datetime.now()}")
        
        # local scans
        print("[*] scanning local filesystem...")
        configs = scan_important_configs()
        snapshot_data['filesystem'] = configs
        print(f"[✓] scanned {len(configs)} config directories")
        
        print("[*] checking local system status...")
        
        # disk scanning
        disk_data = scan_disks()
        snapshot_data['disk'] = disk_data
        filesystems = len(disk_data.get('usage', []))
        print(f"[✓] disk usage: {filesystems} mounted filesystems")
        
        # network scanning
        network_data = scan_network_interfaces()
        snapshot_data['network'] = network_data
        listening_count = network_data.get('listening_ports', '').count('LISTEN')
        print(f"[✓] network services: {listening_count} listening ports")
        
        # docker scanning
        docker_data = scan_docker_containers()
        snapshot_data['docker'] = docker_data
        container_count = len(docker_data.get('containers', []))
        running_count = len([c for c in docker_data.get('containers', []) if 'Up' in c.get('status', '')])
        print(f"[✓] docker containers: {running_count}/{container_count} running")
        
        # remote scans
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
                
                # show brief status for each server
                for server_name, server_data in remote_results.get('servers', {}).items():
                    status = server_data.get('connection_status', 'unknown')
                    hostname = server_data.get('hostname', 'unknown')
                    if status == 'connected':
                        print(f"    [✓] {server_name} ({hostname}): online")
                    else:
                        error = server_data.get('error', 'unknown error')
                        print(f"    [✗] {server_name}: {error}")
                        
            except ImportError:
                print("[!] remote scanner not available - run setup_remote_access.sh first")
            except Exception as e:
                print(f"[!] remote scan error: {e}")
        
        # save snapshot
        scan_type = "remote" if include_remote else "local"
        snapshot_path = save_snapshot(snapshot_data, scan_type)
        if snapshot_path:
            print(f"[✓] snapshot saved: {snapshot_path}")
        
        # ai analysis
        if include_analysis:
            print("[*] starting ai analysis...")
            try:
                from llm.llm_analyzer import LLMAnalyzer
                
                analyzer = LLMAnalyzer()
                
                # test connection first
                if analyzer.check_ollama_health():
                    print("[✓] ollama connection verified")
                else:
                    print("[!] ollama not available - using rule-based analysis")
                
                analysis = analyzer.analyze_system(snapshot_data)
                
                # save analysis report
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_path = f"/opt/spider/logs/reports/analysis_{timestamp}.md"
                os.makedirs("/opt/spider/logs/reports", exist_ok=True)
                
                with open(report_path, 'w') as f:
                    f.write(analysis)
                
                print(f"[✓] analysis saved: {report_path}")
                
                # show summary
                print("\n" + "="*60)
                print("🧠 spider ai analysis summary")
                print("="*60)
                
                # extract key points from analysis
                lines = analysis.split('\n')
                summary_started = False
                line_count = 0
                
                for line in lines:
                    # look for health status or summary sections
                    if any(keyword in line.lower() for keyword in ['system health', 'critical issues', 'warnings', 'recommendations']):
                        summary_started = True
                        print(line)
                        line_count += 1
                    elif summary_started and line.strip():
                        print(line)
                        line_count += 1
                        if line_count > 15:  # limit output
                            print("...")
                            break
                    elif summary_started and line.startswith('##') and 'predictions' in line.lower():
                        break
                
                print("="*60)
                
            except ImportError:
                print("[!] llm analyzer not available")
                print("[*] ensure llm_analyzer.py is in the llm/ directory")
            except Exception as e:
                print(f"[!] analysis error: {e}")
        
        print(f"[✓] spider scan complete at {datetime.now()}")
        return True
        
    except Exception as e:
        print(f"[✗] spider scan failed: {e}")
        return False

def test_llm_connection():
    """test llm connection"""
    print("[*] testing llm connection...")
    try:
        from llm.llm_analyzer import LLMAnalyzer
        
        analyzer = LLMAnalyzer()
        
        if analyzer.check_ollama_health():
            print("[✓] ollama is running and responsive")
            
            # test simple query
            test_response = analyzer.query_ollama("say 'spider llm is working!' and nothing else.", max_tokens=20)
            print(f"[✓] test response: {test_response}")
            
            # test spider-specific connection
            if analyzer.test_connection():
                print("[✓] spider-specific test passed")
                return True
            else:
                print("[!] spider-specific test failed")
                return False
        else:
            print("[✗] ollama is not responsive")
            print("    make sure ollama is installed and running:")
            print("    sudo systemctl status ollama")
            return False
            
    except ImportError:
        print("[✗] llm analyzer not found")
        print("    ensure llm_analyzer.py exists in llm/ directory")
        return False
    except Exception as e:
        print(f"[✗] llm test failed: {e}")
        return False

def test_remote_connections():
    """test remote server connections"""
    print("[*] testing remote server connections...")
    try:
        from scanners.remote_scanner import scan_remote_servers
        results = scan_remote_servers()
        
        connected = results.get('connected_servers', 0)
        total = results.get('total_servers', 0)
        
        print(f"[*] connection results: {connected}/{total} servers")
        
        for server_name, server_data in results.get('servers', {}).items():
            status = server_data.get('connection_status', 'unknown')
            if status == 'connected':
                hostname = server_data.get('hostname', 'unknown')
                print(f"    [✓] {server_name} ({hostname}): connected")
            else:
                error = server_data.get('error', 'connection failed')
                print(f"    [✗] {server_name}: {error}")
        
        return connected > 0
        
    except ImportError:
        print("[✗] remote scanner not available")
        print("    run setup_remote_access.sh to configure ssh keys")
        return False
    except Exception as e:
        print(f"[✗] remote test failed: {e}")
        return False

def compare_latest_snapshots():
    """compare the two most recent snapshots"""
    snapshots_dir = "/opt/spider/logs/snapshots"
    
    try:
        # get all snapshot files
        snapshot_files = [f for f in os.listdir(snapshots_dir) if f.endswith('.json')]
        snapshot_files.sort(reverse=True)  # newest first
        
        if len(snapshot_files) < 2:
            print("[!] need at least 2 snapshots for comparison")
            return False
        
        # load the two most recent snapshots
        current_file = os.path.join(snapshots_dir, snapshot_files[0])
        previous_file = os.path.join(snapshots_dir, snapshot_files[1])
        
        with open(current_file, 'r') as f:
            current = json.load(f)
        with open(previous_file, 'r') as f:
            previous = json.load(f)
        
        print(f"[*] comparing snapshots:")
        print(f"    current:  {snapshot_files[0]}")
        print(f"    previous: {snapshot_files[1]}")
        
        # run comparison
        from llm.llm_analyzer import LLMAnalyzer
        analyzer = LLMAnalyzer()
        
        comparison = analyzer.compare_snapshots(current, previous)
        
        # save comparison report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"/opt/spider/logs/reports/comparison_{timestamp}.md"
        
        with open(report_path, 'w') as f:
            f.write(comparison)
        
        print(f"[✓] comparison saved: {report_path}")
        
        # show brief summary
        print("\n" + "="*50)
        print("🔄 snapshot comparison summary")
        print("="*50)
        
        lines = comparison.split('\n')[:20]  # first 20 lines
        for line in lines:
            if line.strip():
                print(line)
        
        print("="*50)
        return True
        
    except Exception as e:
        print(f"[!] comparison failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='spider homelab intelligence system')
    parser.add_argument('--scan', action='store_true', help='run single system scan')
    parser.add_argument('--daemon', action='store_true', help='run as continuous daemon')
    parser.add_argument('--remote', action='store_true', help='include remote server scanning')
    parser.add_argument('--analyze', action='store_true', help='include ai analysis')
    parser.add_argument('--test-remote', action='store_true', help='test remote connections only')
    parser.add_argument('--test-llm', action='store_true', help='test llm connection')
    parser.add_argument('--compare', action='store_true', help='compare latest snapshots')
    parser.add_argument('--interval', type=int, default=30, help='daemon scan interval in minutes (default: 30)')
    
    args = parser.parse_args()
    
    print("🕷️  spider homelab intelligence system")
    print("=" * 45)
    print(f"[*] starting at {datetime.now()}")
    
    if args.test_llm:
        success = test_llm_connection()
        return 0 if success else 1
    
    elif args.test_remote:
        success = test_remote_connections()
        return 0 if success else 1
    
    elif args.compare:
        success = compare_latest_snapshots()
        return 0 if success else 1
    
    elif args.daemon:
        print(f"[*] running in daemon mode (scan every {args.interval} minutes)...")
        include_remote = args.remote
        include_analysis = args.analyze
        scan_count = 0
        
        while True:
            try:
                scan_count += 1
                print(f"\n[*] starting scheduled scan #{scan_count} at {datetime.now()}")
                success = run_scan(include_remote=include_remote, include_analysis=include_analysis)
                
                if success:
                    print(f"[✓] scan #{scan_count} completed successfully")
                else:
                    print(f"[!] scan #{scan_count} completed with errors")
                
                sleep_seconds = args.interval * 60
                print(f"[*] sleeping for {args.interval} minutes...")
                time.sleep(sleep_seconds)
                
            except KeyboardInterrupt:
                print(f"\n[*] spider daemon shutting down after {scan_count} scans...")
                break
            except Exception as e:
                print(f"[!] daemon error: {e}")
                print("[*] restarting in 60 seconds...")
                time.sleep(60)
    
    elif args.scan:
        print("[*] running single comprehensive scan...")
        success = run_scan(include_remote=args.remote, include_analysis=args.analyze)
        return 0 if success else 1
    
    else:
        print("[*] no action specified. available commands:")
        print("  --scan                    # local scan only")
        print("  --scan --remote           # local + remote servers")
        print("  --scan --analyze          # local scan + ai analysis")
        print("  --scan --remote --analyze # full scan + ai analysis")
        print("  --test-remote             # test remote connections")
        print("  --test-llm                # test llm connection")
        print("  --compare                 # compare latest snapshots")
        print("  --daemon                  # continuous local scanning")
        print("  --daemon --remote         # continuous local + remote")
        print("  --daemon --analyze        # continuous with ai analysis")
        print("  --daemon --interval 15    # custom interval (minutes)")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())