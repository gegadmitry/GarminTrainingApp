#!/usr/bin/env python3
"""Validate and optionally exercise the local read-only Garmin MCP server."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
from typing import Any


DEFAULT_CONFIG = Path("config/garmin-mcp.json")
WRITE_MARKERS = ("create", "delete", "edit", "schedule", "upload", "write")


def load_server(config_path: Path) -> dict[str, Any]:
    document = json.loads(config_path.read_text(encoding="utf-8"))
    server = document.get("mcpServers", {}).get("garmin")
    if not isinstance(server, dict):
        raise ValueError("config must define mcpServers.garmin")
    return server


def validate_server(server: dict[str, Any]) -> tuple[list[str], dict[str, str]]:
    command = server.get("command")
    arguments = server.get("args")
    environment = server.get("env")
    if command != "uvx" or not isinstance(arguments, list):
        raise ValueError("garmin server must use uvx with an argument list")
    if "3.12" not in arguments or "garmin-mcp" not in arguments:
        raise ValueError("garmin server must pin the Python 3.12 uvx entry point")
    if not isinstance(environment, dict):
        raise ValueError("garmin server must define an environment allowlist")

    tools = [tool.strip() for tool in environment.get("GARMIN_ENABLED_TOOLS", "").split(",")]
    tools = [tool for tool in tools if tool]
    if not tools:
        raise ValueError("GARMIN_ENABLED_TOOLS must be a non-empty allowlist")
    unsafe_tools = [tool for tool in tools if any(marker in tool.lower() for marker in WRITE_MARKERS)]
    if unsafe_tools:
        raise ValueError(f"write-capable tools are not allowed: {', '.join(unsafe_tools)}")

    token_template = str(environment.get("GARMINTOKENS", ""))
    if not token_template:
        raise ValueError("GARMINTOKENS must point to an external token directory")
    return [str(command), *[str(argument) for argument in arguments]], environment


def resolve_token_path(environment: dict[str, str]) -> Path:
    token_value = os.environ.get("GARMINTOKENS", environment["GARMINTOKENS"])
    token_path = Path(os.path.expandvars(os.path.expanduser(token_value))).resolve()
    repository = Path.cwd().resolve()
    if token_path == repository or repository in token_path.parents:
        raise ValueError("GARMINTOKENS must point outside the repository")
    return token_path


def read_message(process: subprocess.Popen[str], timeout: float = 20.0) -> dict[str, Any]:
    selector = selectors.DefaultSelector()
    assert process.stdout is not None
    selector.register(process.stdout, selectors.EVENT_READ)
    events = selector.select(timeout)
    selector.close()
    if not events:
        raise TimeoutError("timed out waiting for a response from garmin-mcp")
    line = process.stdout.readline()
    if not line:
        raise RuntimeError("garmin-mcp exited before returning an MCP response")
    response = json.loads(line)
    if not isinstance(response, dict):
        raise RuntimeError("garmin-mcp returned an invalid MCP response")
    return response


def send_message(process: subprocess.Popen[str], message: dict[str, Any]) -> None:
    assert process.stdin is not None
    process.stdin.write(json.dumps(message) + "\n")
    process.stdin.flush()


def run_live_smoke(command: list[str], environment: dict[str, str], token_path: Path) -> None:
    if not token_path.is_dir():
        raise FileNotFoundError(
            f"token directory does not exist: {token_path}; run scripts/garmin_mcp_auth.sh first"
        )

    process_environment = os.environ.copy()
    process_environment.update(environment)
    process_environment["GARMINTOKENS"] = str(token_path)
    process = subprocess.Popen(
        command,
        env=process_environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        send_message(
            process,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "garmin-training-smoke-test", "version": "0.1.0"},
                },
            },
        )
        initialize_response = read_message(process)
        if "error" in initialize_response:
            raise RuntimeError(f"MCP initialization failed: {initialize_response['error']}")
        send_message(process, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        send_message(
            process,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "get_activities", "arguments": {}},
            },
        )
        activity_response = read_message(process)
        if "error" in activity_response:
            raise RuntimeError(f"get_activities failed: {activity_response['error']}")
        print(json.dumps(activity_response.get("result", {}), indent=2))
    finally:
        process.terminate()
        process.wait(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="validate the read-only configuration without accessing Garmin",
    )
    arguments = parser.parse_args()
    try:
        command, environment = validate_server(load_server(arguments.config))
        token_path = resolve_token_path(environment)
        if arguments.check_config:
            print(f"valid read-only Garmin MCP configuration; tokens: {token_path}")
        else:
            run_live_smoke(command, environment, token_path)
    except (FileNotFoundError, OSError, RuntimeError, TimeoutError, ValueError, json.JSONDecodeError) as error:
        print(f"garmin MCP smoke test failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())