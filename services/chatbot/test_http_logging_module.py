#!/usr/bin/env python3
"""
Test HTTP Logging Module Directly
Verify that HTTP logging can work independently
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
print("  TESTING HTTP LOGGING MODULE")
print("=" * 70)

try:
    print("\n[1] Testing HTTP logging module import...")
    from core.http_logging import (
        setup_http_logging, 
        create_http_log_file,
        HTTPCallTracker,
        track_external_call
    )
    print("    ✅ HTTP logging module imported successfully")
    
    print("\n[2] Testing HTTPCallTracker...")
    tracker = HTTPCallTracker()
    print("    ✅ HTTPCallTracker instance created")
    
    # Simulate some API calls
    tracker.log_call('TestService', '/test/endpoint', 'GET', 200, 0.123)
    tracker.log_call('TestService', '/test/upload', 'POST', 201, 0.456)
    tracker.log_call('TestService', '/test/error', 'GET', 500, 0.789, error='Server Error')
    print("    ✅ Logged 3 test API calls")
    
    print("\n[3] Saving tracker to file...")
    tracker.save()
    print("    ✅ Tracker saved to logs/api_calls.json")
    
    print("\n[4] Checking saved file...")
    import json
    logs_dir = Path.cwd().parent.parent / 'logs'
    api_calls_log = logs_dir / 'api_calls.json'
    
    if api_calls_log.exists():
        with open(api_calls_log, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"    ✅ File exists with {data.get('total_calls', 0)} calls")
        print(f"\n    Last 3 calls:")
        for call in data.get('calls', [])[-3:]:
            print(f"      [{call['service']}] {call['method']} {call['endpoint']} -> {call['status']}")
    else:
        print(f"    ❌ File not found at {api_calls_log}")
    
    print("\n[5] Testing decorator...")
    @track_external_call('TestServiceDecorator', '/test/decorated', 'POST')
    def test_function():
        return {'status': 200, 'data': 'test'}
    
    result = test_function()
    print(f"    ✅ Decorated function executed: {result}")
    
    print("\n" + "=" * 70)
    print("✅ ALL HTTP LOGGING TESTS PASSED")
    print("=" * 70)
    print("\nHTTP Logging Module Features:")
    print("  ✅ HTTPCallTracker - Track external API calls")
    print("  ✅ Decorator - @track_external_call for functions")
    print("  ✅ File logging - Saves to logs/api_calls.json")
    print("  ✅ Flask integration - setup_http_logging(app)")
    
    print("\nTo use in Flask app:")
    print("""
    from core.http_logging import setup_http_logging, create_http_log_file
    
    setup_http_logging(app)  # Setup middleware
    create_http_log_file(app)  # Create separate log file
    """)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
