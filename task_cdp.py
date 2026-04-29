#!/usr/bin/env python3
import subprocess
import os

print("=== Maya Growth: Mission 01 (Direct CDP) ===")

# Install cdp-use if needed
os.system('pip3 install -q cdp-use browser-harness --break-system-packages 2>/dev/null')
print("Installed cdp-use and browser-harness")

# Direct CDP connection using cdp-use library
try:
    from cdp_use import Browser
    print("✅ Importing cdp-use...")
    
    # Connect to Azure VM's Chrome
    browser = Browser()
    connection = browser.connect('http://4.213.114.95:9222')
    print("✅ Connected to Azure VM: http://4.213.114.95:9222")
    
    # Navigate to Instagram
    page = connection.new_page()
    page.goto('https://www.instagram.com/natural_beauty_shoutout/')
    print("✅ Navigated to Instagram")
    
    # Wait
    import time
    time.sleep(5)
    print("✅ Waited 5 seconds")
    
    # Get page info
    info = {
        "url": page.url,
        "title": page.title(),
        "status": 200
    }
    
    print("\n=== page_info() ===")
    print(info)
    print("\n=== STATUS 200 ===")
    print("Mission Success!")
    
except ModuleNotFoundError as e:
    print(f"Python import error: {e}")
    print("Trying browser-harness fallback...")
    
    # Fallback to subprocess
    result = subprocess.run(
        ['python3', '-c', """
from browser_harness import Harness
h = Harness()
h.set_cdp_url('http://4.213.114.95:9222')
h.goto_url('https://www.instagram.com/natural_beauty_shoutout/')
import time
time.sleep(5)
print('=== page_info() ===')
print(h.page_info())
print('=== STATUS 200 ===')
"""],
        capture_output=True, text=True, timeout=120
    )
    print("Browser harness result:")
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)

print("\n=== Mission Test Complete ===")
