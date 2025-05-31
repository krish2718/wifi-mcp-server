#!/usr/bin/env python3
"""
Standalone test for Wi-Fi functionality without MCP protocol
"""

import asyncio
import sys
import os

# Add the current directory to path so we can import our server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wifi_mcp_server import WiFiMCPServer


async def test_wifi_functions():
    """Test Wi-Fi functions directly"""
    server = WiFiMCPServer()

    print("=== Direct Wi-Fi Function Tests ===\n")

    try:
        print("1. Testing list_interfaces...")
        interfaces = await server.list_interfaces()
        print(f"Interfaces: {interfaces}\n")

        print("2. Testing get_wifi_status...")
        status = await server.get_wifi_status()
        print(f"Status: {status}\n")

        print("3. Testing scan_wifi...")
        scan_results = await server.scan_wifi()
        print(f"Scan results: {scan_results}\n")

        print("4. Testing get_signal_strength...")
        signal = await server.get_signal_strength()
        print(f"Signal: {signal}\n")

    except Exception as e:
        print(f"Error during testing: {e}")


if __name__ == "__main__":
    asyncio.run(test_wifi_functions())
