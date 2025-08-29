#!/bin/bash
# basic spider test

cd /opt/spider

echo "testing spider components..."

echo "1. testing filesystem scanner..."
venv/bin/python -c "from spider.scanners import filesystem_scanner; print('✓ filesystem scanner ok')"

echo "2. testing disk scanner..."
venv/bin/python -c "from spider.scanners import disk_scanner; print('✓ disk scanner ok')"

echo "3. testing network scanner..."
venv/bin/python -c "from spider.scanners import network_scanner; print('✓ network scanner ok')"

echo "4. testing docker scanner..."
venv/bin/python -c "from spider.scanners import docker_scanner; print('✓ docker scanner ok')"

echo "5. testing command executor..."
venv/bin/python -c "from spider.executor import command_executor; print('✓ command executor ok')"

echo "6. testing llm analyzer..."
venv/bin/python -c "from spider.llm import llm_analyzer; print('✓ llm analyzer ok')"

echo "all components loaded successfully!"

echo "running quick test scan..."
venv/bin/python spider/main.py --filesystem /tmp

echo "spider test complete!"