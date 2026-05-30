"""Entry point — `mcp-emp` / `python -m mcp_emp`.

Routing:
  mcp-emp auth <subcommand>   → auth CLI (no EMP connection needed)
  mcp-emp                     → start the MCP server
"""

import asyncio
import sys


def main_sync() -> None:
    """Synchronous entry point called by the `mcp-emp` script."""
    args = sys.argv[1:]

    # Route auth sub-commands to the auth CLI (no EMP connection needed)
    if args and args[0] == "auth":
        from mcp_emp.core.mcp_auth.cli import run_auth_cli  # noqa: PLC0415

        run_auth_cli(args[1:])
        return

    # Route template sub-commands
    if args and args[0] == "template":
        from mcp_emp.core.templates.cli import run_template_cli  # noqa: PLC0415

        run_template_cli(args[1:])
        return

    from mcp_emp.server import main  # noqa: PLC0415

    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
