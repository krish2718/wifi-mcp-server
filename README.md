# WiFi MCP Server

A Model Context Protocol (MCP) server that provides WiFi network monitoring and management tools. This server can be integrated with Continue.dev, Claude Desktop, or any MCP-compatible client to give AI assistants real-time access to WiFi information.

## Features

- 📡 **WiFi Network Scanning**: Discover available wireless networks
- 📊 **Connection Status**: Get current WiFi connection details
- 📶 **Signal Strength**: Monitor signal quality and strength metrics
- 🔌 **Interface Management**: List and manage network interfaces
- 🔄 **Real-time Updates**: Live monitoring of network conditions

## Prerequisites

- Python 3.8 or higher
- Linux system with WiFi capabilities
- Network management tools: `iw`, `iwconfig`, `ip` (usually pre-installed)
- Root/sudo access for some network operations

## Installation

### Quick Setup

```bash
# Clone or navigate to the project directory
cd ~/wifi-mcp-server

# Install dependencies
pip install -r requirements.txt

# Optional: Install in development mode
pip install -e .
```

### Alternative Setup with Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Demo

### 1. Standalone Testing

Test the WiFi tools without MCP integration:

```bash
# Run standalone tests
python3 standalone_test.py

# Or use the Makefile
make test-standalone
```

### 2. MCP Server Testing

Test the full MCP server functionality:

```bash
# Test all MCP tools
python3 test_wifi_server.py ./wifi_mcp_server.py

# Or use the Makefile
make test-mcp
```

### 3. Running the MCP Server

Start the server in stdio mode (for integration with MCP clients):

```bash
# Run the server directly
python3 wifi_mcp_server.py

# Or using the provided script
./run_server.sh
```

## Integration Examples
### VS Code MCP Integration

To integrate the WiFi MCP Server with Visual Studio Code, add the following to your VS Code settings (`~/.config/Code/User/settings.json`):

```json
{
    "mcp": {
        "servers": {
            "wifi-mcp-server": {
                "type": "stdio",
                "command": "~/wifi-mcp-server/wifi_mcp_server.py",
                "args": []
            }
        }
    }
}
```

This enables MCP-based WiFi tools directly within VS Code.

## Available Tools

### 1. `scan_wifi`
Scan for available WiFi networks

**Parameters:**
- `interface` (optional): WiFi interface name (e.g., "wlan0")

**Example usage:**
```bash
# In Continue.dev chat:
"Scan for available WiFi networks"
```

### 2. `get_wifi_status`
Get current WiFi connection status

**Parameters:**
- `interface` (optional): WiFi interface name

**Example usage:**
```bash
# In Continue.dev chat:
"What's my current WiFi status?"
```

### 3. `get_signal_strength`
Get detailed signal strength and quality metrics

**Parameters:**
- `interface` (optional): WiFi interface name

**Example usage:**
```bash
# In Continue.dev chat:
"Check my WiFi signal strength"
```

### 4. `list_interfaces`
List all available network interfaces

**Example usage:**
```bash
# In Continue.dev chat:
"Show me all network interfaces"
```

## Demo Scenarios

### Basic Network Monitoring

1. **Check Current Status:**
   ```
   "What's my current WiFi status?"
   ```

2. **Scan for Networks:**
   ```
   "Scan and list available WiFi networks"
   ```

3. **Monitor Signal Quality:**
   ```
   "How strong is my WiFi signal?"
   ```

### Troubleshooting Workflow

1. **Network Diagnostics:**
   ```
   "Help me diagnose my WiFi connection issues"
   ```

2. **Compare Networks:**
   ```
   "Show me all available networks and their signal strengths"
   ```

3. **Interface Information:**
   ```
   "List all my network interfaces and their status"
   ```

## Development

### Project Structure

```
wifi-mcp-server/
├── wifi_mcp_server.py          # Main MCP server implementation
├── test_wifi_server.py         # MCP server test suite
├── standalone_test.py          # Standalone functionality tests
├── requirements.txt            # Python dependencies
├── setup.py                    # Package setup configuration
├── Makefile                    # Build and test commands
└── README.md                   # This file
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test suites
make test-standalone  # Test WiFi functions directly
make test-mcp        # Test MCP server functionality

# Run with verbose output
python3 test_wifi_server.py ./wifi_mcp_server.py
```

### Development Setup

```bash
# Set up development environment
make dev-setup

# Install in development mode
make install

# Format code
make lint
```

## Troubleshooting

### Common Issues

1. **Permission Errors:**
   ```bash
   # Some WiFi operations require sudo
   sudo python3 wifi_mcp_server.py
   ```

2. **Missing Dependencies:**
   ```bash
   pip install mcp
   ```

3. **Network Tools Not Found:**
   ```bash
   # Install wireless tools (Ubuntu/Debian)
   sudo apt install wireless-tools iw net-tools

   # Install wireless tools (CentOS/RHEL)
   sudo yum install wireless-tools iw net-tools
   ```

4. **MCP Server Not Starting:**
   ```bash
   # Check if MCP library is installed
   python3 -c "import mcp; print('MCP installed successfully')"

   # Run server with debug output
   python3 wifi_mcp_server.py 2>&1 | tee debug.log
   ```

### Debug Mode

Enable debug logging by setting environment variable:

```bash
export DEBUG=1
python3 wifi_mcp_server.py
```

### Checking Integration

1. **Test MCP Server Directly:**
   ```bash
   echo '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}' | python3 wifi_mcp_server.py
   ```

2. **Verify Continue.dev Integration:**
   - Check Continue.dev logs: `~/.continue/logs/continue.log`
   - Look for MCP server loading messages
   - Test with simple WiFi queries

3. **Check Network Interface:**
   ```bash
   # List wireless interfaces
   iw dev

   # Check interface status
   ip link show
   ```

## License

This project is licensed under the terms specified in the LICENSE file.

## Examples Output
### WiFi Status Example
```json
{
    "interface": "wlan0",
    "connected_ssid": "ExampleSSID",
    "access_point": "00:11:22:33:44:55",
    "bit_rate": 300.0,
    "link_quality": {
        "current": 40,
        "max": 70
    },
    "signal_level": -60
}
```

### Network Scan Example
```json
{
    "interface": "wlan0",
    "networks": [
        {
            "bssid": "00:11:22:33:44:55",
            "frequency": 5180.0,
            "signal": -60,
            "ssid": "ExampleSSID"
        },
        {
            "bssid": "66:77:88:99:AA:BB",
            "frequency": 2412.0,
            "signal": -50,
            "ssid": "GuestNetwork"
        }
    ],
    "scan_time": 1234567.890123
}
```

---

## Quick Start Demo

### 1. Setup and Installation

```bash
# Clone or navigate to the project directory
cd ~/wifi-mcp-server

# Option A: Quick setup (system Python)
pip install -r requirements.txt

# Option B: Development setup with virtual environment
make dev-setup
source venv/bin/activate  # Activate the virtual environment
```

### 2. Test WiFi Functions

```bash
# Test standalone WiFi functions (no MCP required)
python3 standalone_test.py

# Expected output: Lists interfaces, shows WiFi status, etc.
```

### 3. Test MCP Server

```bash
# Test the full MCP server with all tools
python3 test_wifi_server.py ./wifi_mcp_server.py

# Expected output: JSON responses for scan, status, signal strength
```

### 4. Run the MCP Server

```bash
# Start the server in stdio mode
python3 wifi_mcp_server.py

# The server will wait for JSON-RPC commands via stdin
# Press Ctrl+C to stop
```
### 5. Integration with VS Code

Add the following to your VS Code settings (`~/.config/Code/User/settings.json`):

```json
{
    "mcp": {
        "servers": {
            "wifi-mcp-server": {
                "type": "stdio",
                "command": "~/wifi-mcp-server/wifi_mcp_server.py",
                "args": []
            }
        }
    }
}
```

### 6. Demo Commands

Once integrated, try these commands in the VS Code chat:

```
"What's my current WiFi status?"
"Scan for available WiFi networks"
"Check my WiFi signal strength"
"List all network interfaces"
```
