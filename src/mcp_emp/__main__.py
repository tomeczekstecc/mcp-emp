"""Entry point — `mcp-emp` / `python -m mcp_emp`."""

import asyncio


def main_sync() -> None:
    """Synchronous entry point called by the `mcp-emp` script."""
    from mcp_emp.server import main  # noqa: PLC0415

    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
