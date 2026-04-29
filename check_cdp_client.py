#!/usr/bin/env python3
import sys
sys.path.insert(0, '/opt/hostedtoolcache/Python/3.14.4/x64/lib/python3.14/site-packages')

print("=== Inspecting CDPClient ===")

# Import the client
from cdp_use.client import CDPClient
print(f"CDPClient class: {CDPClient}")
print(f"CDPClient module: {CDPClient.__module__}")

# Create instance
client = CDPClient("http://4.213.114.95:9222")
print(f"\nClient instance: {client}")
print(f"Client type: {type(client)}")

# List all attributes and methods
print("\nAll attributes of CDPClient:")
for attr in dir(client):
    if not attr.startswith('_'):
        print(f"  - {attr}")

print("\n=== Done ===")