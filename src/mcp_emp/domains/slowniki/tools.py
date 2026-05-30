"""Słowniki MCP tool registrations.

register(server) is called from server.py during build_server().
Tools implemented in M2: list_task_types, list_tags.
"""

from mcp.server.fastmcp import FastMCP


def register(server: FastMCP) -> None:
    """Register all słowniki tools on *server*."""
    # M2: list_task_types, list_tags
