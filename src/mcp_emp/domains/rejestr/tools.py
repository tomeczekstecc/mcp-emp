"""Rejestr MCP tool registrations.

register(server) is called from server.py during build_server().
Tools implemented incrementally: M3 (reads), M4 (add), M5 (complete), M6 (delete).
"""

from mcp.server.fastmcp import FastMCP


def register(server: FastMCP) -> None:
    """Register all rejestr tools on *server*."""
    # M3: list_my_tasks, get_task
    # M4: add_my_task
    # M5: complete_task
    # M6: delete_task
