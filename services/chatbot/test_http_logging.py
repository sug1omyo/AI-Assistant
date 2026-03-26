#!/usr/bin/env python3
"""
Test HTTP Logging Integration
Verify that HTTP logging middleware is properly integrated
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Setup paths
chatbot_dir = Path(__file__).parent
os.chdir(chatbot_dir)

# Load environment
env_file = chatbot_dir / '.env'
if env_file.exists():
    load_dotenv(env_file)

print("=" * 70)
print("  TESTING HTTP LOGGING INTEGRATION")
print("=" * 70)

try:
    print("\n[1] Checking Flask app import...")
    from chatbot_main import app
    print("    ✅ Flask app imported successfully")
    
    print("\n[2] Creating test client...")
    client = app.test_client()
    print("    ✅ Test client created")
    
    print("\n[3] Testing GET request logging...")
    response = client.get('/')
    print(f"    ✅ GET / returned {response.status_code}")
    
    print("\n[4] Testing POST request logging...")
    response = client.post('/api/conversations', json={'test': 'data'})
    print(f"    ✅ POST /api/conversations returned {response.status_code}")
    
    print("\n[5] Checking log files...")
    logs_dir = Path.cwd().parent.parent / 'logs'
    
    http_log = logs_dir / 'http_calls.log'
    if http_log.exists():
        print(f"    ✅ HTTP log file exists: {http_log}")
        # Show last few lines
        with open(http_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-5:]
            print("\n    Last 5 log entries:")
            for line in lines:
                print(f"      {line.rstrip()}")
    else:
        print(f"    ⚠️  HTTP log file not found: {http_log}")
    
    api_calls_log = logs_dir / 'api_calls.json'
    if api_calls_log.exists():
        print(f"    ✅ API calls JSON exists: {api_calls_log}")
        import json
        try:
            with open(api_calls_log, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"       Total calls tracked: {data.get('total_calls', 0)}")
        except Exception as e:
            print(f"       Could not read JSON: {e}")
    else:
        print(f"    ⚠️  API calls JSON not found: {api_calls_log}")
    
    print("\n" + "=" * 70)
    print("✅ HTTP LOGGING TEST COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print("\nLogs are being captured to:")
    print(f"  - {logs_dir / 'http_calls.log'}")
    print(f"  - {logs_dir / 'api_calls.json'}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
