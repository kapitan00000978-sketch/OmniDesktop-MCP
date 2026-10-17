"""
OmniDesktop-MCP Agent Configuration Helper.
Automatically registers this MCP server into Claude Desktop config,
or generates configurations for Cursor, Antigravity, and VS Code.
"""

from __future__ import annotations

import json
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_PATH = os.path.join(PROJECT_DIR, "venv", "Scripts", "python.exe")
SERVER_SCRIPT = os.path.join(PROJECT_DIR, "server.py")

if not os.path.isfile(PYTHON_PATH):
    PYTHON_PATH = sys.executable


def get_mcp_config_dict() -> dict:
    """Returns the MCP configuration snippet for OmniDesktop-MCP."""
    return {
        "command": PYTHON_PATH.replace("\\", "/"),
        "args": [SERVER_SCRIPT.replace("\\", "/")]
    }


def configure_claude_desktop() -> bool:
    """Detects and registers OmniDesktop-MCP into Claude Desktop config."""
    appdata = os.environ.get("APPDATA")
    if not appdata:
        print("[!] APPDATA environment variable not found.")
        return False

    claude_dir = os.path.join(appdata, "Claude")
    config_path = os.path.join(claude_dir, "claude_desktop_config.json")

    os.makedirs(claude_dir, exist_ok=True)
    config_data = {}
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception:
            config_data = {}

    if "mcpServers" not in config_data:
        config_data["mcpServers"] = {}

    config_data["mcpServers"]["omnidesktop"] = get_mcp_config_dict()

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

    print(f"[OK] Successfully registered OmniDesktop-MCP in Claude Desktop config:")
    print(f"    File: {config_path}")
    return True


def print_generic_config() -> None:
    """Prints config snippet for manual integration."""
    snippet = {
        "mcpServers": {
            "omnidesktop": get_mcp_config_dict()
        }
    }
    print("\n--- MCP CONFIGURATION SNIPPET ---")
    print(json.dumps(snippet, indent=2))
    print("---------------------------------\n")


def main() -> None:
    print("=== OmniDesktop-MCP Agent Configuration ===")
    configured = configure_claude_desktop()
    print_generic_config()
    if configured:
        print("Done! You can now restart Claude Desktop or connect your AI Agent.")


if __name__ == "__main__":
    main()
