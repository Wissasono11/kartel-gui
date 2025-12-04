#!/usr/bin/env python3
"""
Test script untuk fitur enkripsi kredensial
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from config import save_user_credentials, load_user_credentials, clear_user_credentials

def test_credential_security():
    print("🧪 Testing credential security features...\n")
    
    # Test 1: Save credentials
    print("📝 Test 1: Saving credentials...")
    result = save_user_credentials('kartel', 'kartel123')
    print(f"✅ Save result: {result}\n")
    
    # Test 2: Load credentials
    print("📖 Test 2: Loading credentials...")
    creds = load_user_credentials()
    if creds:
        print(f"✅ Loaded successfully:")
        print(f"   - Username: {creds.get('username')}")
        print(f"   - Method: {creds.get('method', 'unknown')}")
        print(f"   - Remember: {creds.get('remember')}")
    else:
        print("❌ No credentials loaded")
    print()
    
    # Test 3: Check files created
    print("📁 Test 3: Checking files...")
    encrypted_file = "user_credentials.enc"
    if os.path.exists(encrypted_file):
        with open(encrypted_file, 'r') as f:
            content = f.read()
        print(f"✅ Encrypted file exists:")
        print(f"   - File: {encrypted_file}")
        print(f"   - Content (encrypted): {content[:50]}...")
        print(f"   - Length: {len(content)} chars")
    else:
        print("❌ No encrypted file found")
    print()
    
    # Test 4: Clear credentials
    print("🗑️ Test 4: Clearing credentials...")
    clear_result = clear_user_credentials()
    print(f"✅ Clear result: {clear_result}")
    
    # Test 5: Load after clear
    print("\n📖 Test 5: Loading after clear...")
    creds_after = load_user_credentials()
    if creds_after:
        print(f"⚠️ Still has credentials: {creds_after}")
    else:
        print("✅ No credentials found (as expected)")
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    test_credential_security()