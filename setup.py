from setuptools import setup, find_packages

setup(
    name="wifi-mcp-server",
    version="1.0.0",
    description="Wi-Fi MCP Server for network monitoring",
    packages=find_packages(),
    install_requires=[
        "mcp>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "wifi-mcp-server=wifi_mcp_server:main",
        ],
    },
    python_requires=">=3.8",
)
