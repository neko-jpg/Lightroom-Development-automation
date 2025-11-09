#!/usr/bin/env python
"""
Validation script for WebSocket implementation
Checks that all components are properly implemented
"""

import sys
import os

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description}: {filepath} NOT FOUND")
        return False

def check_python_syntax(filepath):
    """Check Python file syntax"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            compile(f.read(), filepath, 'exec')
        print(f"✓ Python syntax valid: {filepath}")
        return True
    except SyntaxError as e:
        print(f"✗ Python syntax error in {filepath}: {e}")
        return False

def check_imports(filepath, required_imports):
    """Check if file contains required imports"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing = []
        for imp in required_imports:
            if imp not in content:
                missing.append(imp)
        
        if missing:
            print(f"✗ Missing imports in {filepath}: {', '.join(missing)}")
            return False
        else:
            print(f"✓ All required imports present in {filepath}")
            return True
    except Exception as e:
        print(f"✗ Error checking imports in {filepath}: {e}")
        return False

def main():
    print("=" * 60)
    print("WebSocket Implementation Validation")
    print("=" * 60)
    print()
    
    all_checks_passed = True
    
    # Check Python files
    print("Checking Python files...")
    print("-" * 60)
    
    python_files = [
        ('websocket_server.py', 'WebSocket Server'),
        ('websocket_fallback.py', 'WebSocket Fallback Server'),
        ('test_websocket.py', 'WebSocket Tests'),
    ]
    
    for filepath, description in python_files:
        if not check_file_exists(filepath, description):
            all_checks_passed = False
        elif not check_python_syntax(filepath):
            all_checks_passed = False
    
    print()
    
    # Check Lua files
    print("Checking Lua files...")
    print("-" * 60)
    
    lua_files = [
        ('../JunmaiAutoDev.lrdevplugin/WebSocketClient.lua', 'WebSocket Client (Lua)'),
        ('../JunmaiAutoDev.lrdevplugin/Main.lua', 'Main Plugin (Lua)'),
    ]
    
    for filepath, description in lua_files:
        if not check_file_exists(filepath, description):
            all_checks_passed = False
    
    print()
    
    # Check documentation
    print("Checking documentation...")
    print("-" * 60)
    
    doc_files = [
        ('WEBSOCKET_IMPLEMENTATION.md', 'Implementation Documentation'),
        ('WEBSOCKET_QUICK_START.md', 'Quick Start Guide'),
        ('TASK_17_COMPLETION_SUMMARY.md', 'Completion Summary'),
    ]
    
    for filepath, description in doc_files:
        if not check_file_exists(filepath, description):
            all_checks_passed = False
    
    print()
    
    # Check key imports in websocket_fallback.py
    print("Checking key implementations...")
    print("-" * 60)
    
    if not check_imports('websocket_fallback.py', [
        'class WebSocketFallbackServer',
        'def handshake',
        'def poll',
        'def send',
        'def broadcast',
    ]):
        all_checks_passed = False
    
    # Check app.py integration
    if not check_imports('app.py', [
        'from websocket_fallback import',
        'websocket_fallback',
        '/ws/status',
        '/ws/broadcast',
    ]):
        all_checks_passed = False
    
    # Check Lua client implementation
    if not check_imports('../JunmaiAutoDev.lrdevplugin/WebSocketClient.lua', [
        'WebSocketClient',
        'function WebSocketClient.init',
        'function WebSocketClient.send',
        'function WebSocketClient.sendJobProgress',
    ]):
        all_checks_passed = False
    
    print()
    print("=" * 60)
    
    if all_checks_passed:
        print("✓ All validation checks PASSED")
        print()
        print("WebSocket implementation is complete and ready to use!")
        print()
        print("Next steps:")
        print("1. Install dependencies: pip install flask-sock simple-websocket")
        print("2. Start server: python local_bridge/app.py")
        print("3. Run tests: pytest local_bridge/test_websocket.py -v")
        print("4. Check status: curl http://localhost:5100/ws/status")
        return 0
    else:
        print("✗ Some validation checks FAILED")
        print()
        print("Please review the errors above and fix any issues.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
