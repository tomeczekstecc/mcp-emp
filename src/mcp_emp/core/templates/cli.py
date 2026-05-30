"""CLI for task template management.

Usage:
    mcp-emp template list [--search <q>]
    mcp-emp template add <name> --task-type-id <id> [options]
    mcp-emp template show <name>
    mcp-emp template delete <name>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _get_db_path() -> Path:
    from mcp_emp.core.config import get_settings  # noqa: PLC0415

    try:
        s = get_settings()
        return Path(s.templates_db_path).expanduser()
    except Exception:  # noqa: BLE001
        return Path("~/.mcp_emp/templates.db").expanduser()


def cmd_list(args: argparse.Namespace) -> None:
    from mcp_emp.core.templates.db import list_templates, open_templates_db  # noqa: PLC0415

    conn = open_templates_db(_get_db_path())
    templates = list_templates(conn, search=args.search or "")
    if not templates:
        print("No templates found.")
        return
    print(f"{'NAME':<24} {'TYPE_ID':<10} {'SUBJECT TEMPLATE':<40} {'DEADLINE'}")
    print("-" * 85)
    for t in templates:
        dl = f"+{t.deadline_offset_days}d" if t.deadline_offset_days else ""
        subj = (t.subject_template or "")[:38]
        print(f"{t.name:<24} {t.task_type_id:<10} {subj:<40} {dl}")


def cmd_add(args: argparse.Namespace) -> None:
    from mcp_emp.core.templates.db import add_template, open_templates_db  # noqa: PLC0415

    tag_ids: list[int] = []
    if args.tags:
        try:
            tag_ids = [int(x.strip()) for x in args.tags.split(",") if x.strip()]
        except ValueError:
            print("ERROR: --tags must be comma-separated integers, e.g. '1,5,8'")
            sys.exit(1)

    conn = open_templates_db(_get_db_path())
    try:
        t = add_template(
            conn,
            args.name,
            args.task_type_id,
            subject_template=args.subject,
            notes_template=args.notes,
            deadline_offset_days=args.deadline_days,
            tag_ids=tag_ids,
        )
        print(f"Template '{t.name}' created (id={t.id}).")
        print(f"  task_type_id:  {t.task_type_id}")
        print(f"  subject:       {t.subject_template or '(none)'}")
        print(f"  notes:         {t.notes_template or '(none)'}")
        print(f"  deadline:      +{t.deadline_offset_days}d" if t.deadline_offset_days else "  deadline:      (none)")
        print(f"  tags:          {t.tag_ids or '(none)'}")
        print()
        print("Tip: subject/notes may contain {today}, {date}, {cycle} placeholders.")
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_show(args: argparse.Namespace) -> None:
    from mcp_emp.core.templates.db import get_template, open_templates_db  # noqa: PLC0415

    conn = open_templates_db(_get_db_path())
    t = get_template(conn, args.name)
    if not t:
        print(f"Template '{args.name}' not found.")
        sys.exit(1)
    print(json.dumps({
        "id": t.id, "name": t.name, "task_type_id": t.task_type_id,
        "subject_template": t.subject_template,
        "notes_template": t.notes_template,
        "deadline_offset_days": t.deadline_offset_days,
        "tag_ids": t.tag_ids,
        "created_at": t.created_at,
    }, indent=2, ensure_ascii=False))


def cmd_delete(args: argparse.Namespace) -> None:
    from mcp_emp.core.templates.db import delete_template, open_templates_db  # noqa: PLC0415

    conn = open_templates_db(_get_db_path())
    if delete_template(conn, args.name):
        print(f"Deleted template '{args.name}'.")
    else:
        print(f"Template '{args.name}' not found.")
        sys.exit(1)


def run_template_cli(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="mcp-emp template",
                                     description="Manage task templates")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List templates")
    p_list.add_argument("--search", default="", help="Filter by name substring")

    p_add = sub.add_parser("add", help="Create a template")
    p_add.add_argument("name", help="Template name (unique)")
    p_add.add_argument("--task-type-id", type=int, required=True,
                       help="EMP task type ID (from list_task_types)")
    p_add.add_argument("--subject", default=None,
                       help="Subject template. Supports {today}, {date}, {cycle}.")
    p_add.add_argument("--notes", default=None, help="Notes template.")
    p_add.add_argument("--deadline-days", type=int, default=None,
                       help="Days from today for the deadline (e.g. 7).")
    p_add.add_argument("--tags", default=None,
                       help="Comma-separated tag IDs (e.g. '1,5,8').")

    p_show = sub.add_parser("show", help="Show template details")
    p_show.add_argument("name")

    p_del = sub.add_parser("delete", help="Delete a template")
    p_del.add_argument("name")

    args = parser.parse_args(argv)
    handlers = {
        "list": cmd_list, "add": cmd_add,
        "show": cmd_show, "delete": cmd_delete,
    }
    handlers[args.command](args)
