#!/usr/bin/env python3
"""
Test script for Wi-Fi MCP Server
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any


class MCPTester:
    """Simple MCP server tester"""

    def __init__(self, server_command: str):
        self.server_command = server_command

    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the MCP server"""
        process = await asyncio.create_subprocess_exec(
            *self.server_command.split(),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Send request
        request_json = json.dumps(request) + "\n"
        stdout, stderr = await process.communicate(request_json.encode())

        if process.returncode != 0:
            print(f"Server error: {stderr.decode()}")
            return {"error": "Server failed"}

        try:
            return json.loads(stdout.decode())
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Raw output: {stdout.decode()}")
            return {"error": "Invalid JSON response"}

    async def initialize_server(self, process):
        """Initialize the MCP server with proper handshake"""
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }

        init_json = json.dumps(init_request) + "\n"
        process.stdin.write(init_json.encode())
        await process.stdin.drain()

        # Read initialize response
        response_line = await process.stdout.readline()
        if response_line:
            try:
                init_response = json.loads(response_line.decode())
                print(f"Initialize response: {init_response}")
            except json.JSONDecodeError:
                print(f"Failed to parse init response: {response_line.decode()}")

        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }

        notification_json = json.dumps(initialized_notification) + "\n"
        process.stdin.write(notification_json.encode())
        await process.stdin.drain()

    async def send_request_to_running_server(
        self, process, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send a request to an already running server"""
        request_json = json.dumps(request) + "\n"
        process.stdin.write(request_json.encode())
        await process.stdin.drain()

        # Read response
        response_line = await process.stdout.readline()
        if not response_line:
            return {"error": "No response"}

        try:
            return json.loads(response_line.decode())
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Raw output: {response_line.decode()}")
            return {"error": "Invalid JSON response"}

    async def test_list_tools(self):
        """Test listing available tools"""
        print("Testing list_tools...")
        request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

        # Start server process
        process = await asyncio.create_subprocess_exec(
            *self.server_command.split(),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            # Initialize server
            await self.initialize_server(process)

            # Send the actual request
            response = await self.send_request_to_running_server(process, request)
            print(f"Response: {json.dumps(response, indent=2)}")
            return response
        finally:
            process.terminate()
            await process.wait()

    async def test_tool_call(self, tool_name: str, arguments: Dict[str, Any] = None):
        """Test calling a specific tool"""
        print(f"Testing tool call: {tool_name}")
        if arguments is None:
            arguments = {}

        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        # Start server process
        process = await asyncio.create_subprocess_exec(
            *self.server_command.split(),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            # Initialize server
            await self.initialize_server(process)

            # Send the actual request
            response = await self.send_request_to_running_server(process, request)
            print(f"Response: {json.dumps(response, indent=2)}")
            return response
        finally:
            process.terminate()
            await process.wait()

    async def run_all_tests(self):
        """Run all tests"""
        print("=== MCP Wi-Fi Server Tests ===\n")

        # Test 1: List tools
        await self.test_list_tools()
        print("\n" + "=" * 50 + "\n")

        # Test 2: List interfaces
        await self.test_tool_call("list_interfaces")
        print("\n" + "=" * 50 + "\n")

        # Test 3: Get Wi-Fi status
        await self.test_tool_call("get_wifi_status")
        print("\n" + "=" * 50 + "\n")

        # Test 4: Scan Wi-Fi networks
        await self.test_tool_call("scan_wifi")
        print("\n" + "=" * 50 + "\n")

        # Test 5: Get signal strength
        await self.test_tool_call("get_signal_strength")


async def main():
    """Main function to run tests"""
    if len(sys.argv) < 2:
        print("Usage: python test_wifi_server.py <server_command>")
        print("Example: python test_wifi_server.py 'python wifi_server.py'")
        sys.exit(1)

    server_command = " ".join(sys.argv[1:])
    tester = MCPTester(server_command)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
