#!/usr/bin/env python3
"""
Wi-Fi MCP Server - A Model Context Protocol server for Wi-Fi operations
"""

import sys
import argparse
from aiohttp import web
import asyncio
import json
import re
from typing import Any, Dict, List, Optional

try:
    # Try new MCP structure
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
    )
except ImportError:
    try:
        # Try alternative import structure
        from mcp import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import Tool, TextContent
    except ImportError:
        # Fallback for different MCP versions
        print("Warning: MCP imports not available. Running in standalone mode only.")
        Server = None
        stdio_server = None
        Tool = None
        TextContent = None


class WiFiMCPServer:
    def __init__(self):
        if Server is not None:
            self.server = Server("wifi-server")
            self.setup_handlers()
        else:
            self.server = None

    def setup_handlers(self):
        """Setup MCP server handlers"""
        if self.server is None:
            return

        @self.server.list_tools()
        async def handle_list_tools():
            """List available Wi-Fi tools"""
            return [
                Tool(
                    name="scan_wifi",
                    description="Scan for available Wi-Fi networks",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "interface": {
                                "type": "string",
                                "description": (
                                    "Wi-Fi interface name "
                                    "(optional, defaults to auto-detect)"
                                ),
                            }
                        },
                    },
                ),
                Tool(
                    name="get_wifi_status",
                    description="Get current Wi-Fi connection status",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "interface": {
                                "type": "string",
                                "description": ("Wi-Fi interface name (optional)"),
                            }
                        },
                    },
                ),
                Tool(
                    name="get_signal_strength",
                    description="Get signal strength and quality metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "interface": {
                                "type": "string",
                                "description": ("Wi-Fi interface name (optional)"),
                            }
                        },
                    },
                ),
                Tool(
                    name="list_interfaces",
                    description="List all available network interfaces",
                    inputSchema={"type": "object", "properties": {}},
                ),
            ]

        self.handle_list_tools = handle_list_tools

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]):
            """Handle tool calls"""
            try:
                if name == "scan_wifi":
                    result = await self.scan_wifi(arguments.get("interface"))
                elif name == "get_wifi_status":
                    result = await self.get_wifi_status(arguments.get("interface"))
                elif name == "get_signal_strength":
                    result = await self.get_signal_strength(arguments.get("interface"))
                elif name == "list_interfaces":
                    result = await self.list_interfaces()
                else:
                    raise ValueError(f"Unknown tool: {name}")

                if TextContent is not None:
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                else:
                    return json.dumps(result, indent=2)
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                if TextContent is not None:
                    return [TextContent(type="text", text=error_msg)]
                else:
                    return error_msg

        self.handle_call_tool = handle_call_tool

    async def run_command(self, command: List[str]) -> str:
        """Run a system command and return output"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise RuntimeError(f"Command failed: {stderr.decode()}")

            return stdout.decode()
        except FileNotFoundError:
            raise RuntimeError(f"Command not found: {command[0]}")

    async def get_wifi_interface(self, interface: Optional[str] = None) -> str:
        """Get Wi-Fi interface name"""
        if interface:
            return interface

        # Try to find wireless interface automatically
        try:
            output = await self.run_command(["iwconfig"])
            lines = output.split("\n")
            for line in lines:
                if "IEEE 802.11" in line:
                    return line.split()[0]
        except Exception:
            pass

        # Fallback to common interface names
        for iface in ["wlan0", "wlp2s0", "wifi0"]:
            try:
                await self.run_command(["iwconfig", iface])
                return iface
            except Exception:
                continue

        raise RuntimeError("No Wi-Fi interface found")

    async def scan_wifi(self, interface: Optional[str] = None) -> Dict[str, Any]:
        """Scan for available Wi-Fi networks"""
        iface = await self.get_wifi_interface(interface)

        try:
            # Try using iw first (modern tool)
            output = await self.run_command(["iw", "dev", iface, "scan"])
            networks = self.parse_iw_scan(output)
        except Exception:
            # Fallback to iwlist
            output = await self.run_command(["iwlist", iface, "scan"])
            networks = self.parse_iwlist_scan(output)

        return {
            "interface": iface,
            "networks": networks,
            "scan_time": asyncio.get_event_loop().time(),
        }

    def parse_iw_scan(self, output: str) -> List[Dict[str, Any]]:
        """Parse iw scan output"""
        networks = []
        current_network = {}

        for line in output.split("\n"):
            line = line.strip()

            if line.startswith("BSS "):
                if current_network:
                    networks.append(current_network)
                current_network = {"bssid": line.split()[1].rstrip(":")}
            elif "SSID:" in line:
                current_network["ssid"] = line.split("SSID: ")[1]
            elif "signal:" in line:
                signal_match = re.search(r"signal: ([-\d.]+)", line)
                if signal_match:
                    current_network["signal"] = float(signal_match.group(1))
            elif "freq:" in line:
                freq_match = re.search(r"freq: (\d+)", line)
                if freq_match:
                    current_network["frequency"] = int(freq_match.group(1))

        if current_network:
            networks.append(current_network)

        return networks

    def parse_iwlist_scan(self, output: str) -> List[Dict[str, Any]]:
        """Parse iwlist scan output"""
        networks = []
        current_network = {}

        for line in output.split("\n"):
            line = line.strip()

            if "Cell" in line and "Address:" in line:
                if current_network:
                    networks.append(current_network)
                current_network = {"bssid": line.split("Address: ")[1]}
            elif "ESSID:" in line:
                essid = line.split("ESSID:")[1].strip().strip('"')
                current_network["ssid"] = essid
            elif "Signal level=" in line:
                signal_match = re.search(r"Signal level=([-\d]+)", line)
                if signal_match:
                    current_network["signal"] = int(signal_match.group(1))
            elif "Frequency:" in line:
                freq_match = re.search(r"Frequency:([\d.]+)", line)
                if freq_match:
                    current_network["frequency"] = (
                        float(freq_match.group(1)) * 1000
                    )  # Convert to MHz

        if current_network:
            networks.append(current_network)

        return networks

    async def get_wifi_status(self, interface: Optional[str] = None) -> Dict[str, Any]:
        """Get current Wi-Fi connection status"""
        iface = await self.get_wifi_interface(interface)

        try:
            output = await self.run_command(["iwconfig", iface])
            return self.parse_iwconfig_status(output, iface)
        except Exception as e:
            return {"error": str(e), "interface": iface}

    def parse_iwconfig_status(self, output: str, interface: str) -> Dict[str, Any]:
        """Parse iwconfig output for status information"""
        status = {"interface": interface}

        for line in output.split("\n"):
            if "ESSID:" in line:
                essid_match = re.search(r'ESSID:"([^"]*)"', line)
                if essid_match:
                    status["connected_ssid"] = essid_match.group(1)
            elif "Access Point:" in line:
                ap_match = re.search(r"Access Point: ([A-Fa-f0-9:]{17})", line)
                if ap_match:
                    status["access_point"] = ap_match.group(1)
            elif "Bit Rate=" in line:
                rate_match = re.search(r"Bit Rate=([0-9.]+)", line)
                if rate_match:
                    status["bit_rate"] = float(rate_match.group(1))
            elif "Link Quality=" in line:
                quality_match = re.search(r"Link Quality=(\d+)/(\d+)", line)
                if quality_match:
                    status["link_quality"] = {
                        "current": int(quality_match.group(1)),
                        "max": int(quality_match.group(2)),
                    }
                signal_match = re.search(r"Signal level=([-\d]+)", line)
                if signal_match:
                    status["signal_level"] = int(signal_match.group(1))

        return status

    async def get_signal_strength(
        self, interface: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed signal strength information"""
        status = await self.get_wifi_status(interface)

        # Add additional signal metrics if available
        try:
            iface = status.get("interface", await self.get_wifi_interface(interface))

            # Try to get more detailed info from /proc/net/wireless
            with open("/proc/net/wireless", "r") as f:
                content = f.read()
                for line in content.split("\n"):
                    if iface in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            status.update(
                                {
                                    "wireless_stats": {
                                        "status": parts[1],
                                        "quality": parts[2],
                                        "signal_dbm": parts[3],
                                        "noise_dbm": parts[4]
                                        if len(parts) > 4
                                        else None,
                                    }
                                }
                            )
                        break
        except (FileNotFoundError, PermissionError):
            pass  # /proc/net/wireless might not be available

        return status

    async def list_interfaces(self) -> Dict[str, Any]:
        """List all network interfaces"""
        try:
            # Get list of interfaces
            output = await self.run_command(["ip", "link", "show"])
            interfaces = []

            for line in output.split("\n"):
                if ": " in line and not line.startswith(" "):
                    parts = line.split(": ")
                    if len(parts) >= 2:
                        iface_name = parts[1].split("@")[0]  # Remove VLAN info

                        # Check if it's a wireless interface
                        is_wireless = False
                        try:
                            await self.run_command(["iwconfig", iface_name])
                            is_wireless = True
                        except Exception:
                            pass

                        interfaces.append(
                            {
                                "name": iface_name,
                                "is_wireless": is_wireless,
                                "status": "UP" if "UP" in line else "DOWN",
                            }
                        )

            return {"interfaces": interfaces}
        except Exception as e:
            return {"error": str(e)}


async def main():
    """Main function to run the MCP server with stdio or HTTP"""
    parser = argparse.ArgumentParser(description="Wi-Fi MCP Server")
    parser.add_argument(
        "--mode",
        choices=["stdio", "http"],
        default="stdio",
        help="Run server in stdio or http mode (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for HTTP mode (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for HTTP mode (default: 8080)",
    )
    args = parser.parse_args()

    server = WiFiMCPServer()

    if server.server is None:
        print(
            "Error: MCP libraries not available. Install with: pip install mcp",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.mode == "stdio":
        try:
            # Run the server using stdio
            async with stdio_server() as (read_stream, write_stream):
                await server.server.run(
                    read_stream,
                    write_stream,
                    server.server.create_initialization_options(),
                )
        except Exception as e:
            print(f"Error running MCP server: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.mode == "http":
        # HTTP mode using aiohttp
        app = web.Application()

        async def list_tools_handler(request):
            try:
                # No input expected
                result = await server.handle_list_tools()
                # If result is a list of TextContent, extract text
                if isinstance(result, list) and hasattr(result[0], "text"):
                    result = [x.text for x in result]
                return web.json_response({"result": result})
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)

        async def call_tool_handler(request):
            try:
                data = await request.json()
                name = data.get("tool_name") or data.get("name")
                arguments = data.get("tool_args") or data.get("arguments", {})
                if not name:
                    return web.json_response({"error": "Missing tool_name"}, status=400)
                result = await server.handle_call_tool(name, arguments)
                # If result is a list of TextContent, extract text
                if isinstance(result, list) and hasattr(result[0], "text"):
                    result = [x.text for x in result]
                return web.json_response(
                    result if isinstance(result, dict) else {"result": result}
                )
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)

        async def mcp_handler(request):
            try:
                data = await request.json()
                # Simulate MCP protocol: expects {"method": ..., "params": ...}
                method = data.get("method")
                params = data.get("params", {})
                if method == "list_tools":
                    result = await server.handle_list_tools()
                elif method == "call_tool":
                    name = params.get("name")
                    arguments = params.get("arguments", {})
                    result = await server.handle_call_tool(name, arguments)
                else:
                    return web.json_response({"error": "Unknown method"}, status=400)
                # If result is a list of TextContent, extract text
                if isinstance(result, list) and hasattr(result[0], "text"):
                    result = [x.text for x in result]
                return web.json_response({"result": result})
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)

        # Standard MCP endpoints
        app.router.add_post("/mcp", mcp_handler)
        app.router.add_post("/list_tools", list_tools_handler)
        app.router.add_post("/call_tool", call_tool_handler)
        app.router.add_post(
            "/execute", call_tool_handler
        )  # For wifi_agent.py compatibility

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, args.host, args.port)
        print(f"Serving HTTP on {args.host}:{args.port}")
        await site.start()
        # Run forever
        while True:
            await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
