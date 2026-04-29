import subprocess
import json

print("=== Testing Module Imports ===")

# Test 1: browser_harness attributes
print("\n1. Testing browser_harness module...")
try:
    import browser_harness
    print(f"Module: {browser_harness.__file__}")
    print(f"Version: {getattr(browser_harness, '__version__', 'unknown')}")
    print(f"Dir: {dir(browser_harness)}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: cdp_use attributes
print("\n2. Testing cdp_use module...")
try:
    import cdp_use
    print(f"Module: {cdp_use.__file__}")
    print(f"Dir: {dir(cdp_use)}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Check if browser-harness CLI exists
print("\n3. Checking browser-harness CLI...")
try:
    result = subprocess.run(['which', 'browser-harness'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Found at: {result.stdout.strip()}")
    else:
        print("Not found in PATH")
        # Try to find it
        result = subprocess.run(['find', '/opt', '-name', 'browser-harness'], capture_output=True, text=True)
        print(f"Search results: {result.stdout}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== Test Complete ===")
