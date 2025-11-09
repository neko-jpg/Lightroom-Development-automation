"""Quick test for email notifier"""
import sys
sys.path.insert(0, '.')

from email_notifier import EmailNotifier, EmailNotificationType

print("=== Testing Email Notifier ===\n")

# Test 1: Initialize
print("Test 1: Initialize notifier")
notifier = EmailNotifier()
print(f"✓ EmailNotifier initialized")
print(f"  Enabled: {notifier.config.is_enabled()}")
print(f"  SMTP Server: {notifier.config.get('smtp_server')}")
print(f"  SMTP Port: {notifier.config.get('smtp_port')}")

# Test 2: Get configuration
print("\nTest 2: Get configuration")
config = notifier.get_config()
print(f"✓ Configuration retrieved")
print(f"  Keys: {list(config.keys())}")

# Test 3: Check notification types
print("\nTest 3: Check notification types")
for notif_type in EmailNotificationType:
    enabled = notifier.config.is_type_enabled(notif_type)
    print(f"  {notif_type.value}: {enabled}")

print("\n✓ All tests passed!")
