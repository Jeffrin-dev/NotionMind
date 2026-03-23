import os
import json
import httpx
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text

load_dotenv()

NOTION_API_KEY = os.environ["NOTION_API_KEY"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

BASE_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

console = Console()

PRIORITY_COLORS = {
    "high":   "bright_red",
    "medium": "bright_yellow",
    "low":    "bright_green"
}

PRIORITY_ICONS = {
    "high":   "🔴",
    "medium": "🟡",
    "low":    "🟢"
}


# ── fetch all todos from notion ───────────────────────────────────────────────
def fetch_todos(include_done: bool = False) -> list:
    if include_done:
        # fetch both pending and completed — use OR filter
        filter_query = {
            "or": [
                {"property": "Tags", "multi_select": {"contains": "todo"}},
                {"property": "Tags", "multi_select": {"contains": "todo-done"}}
            ]
        }
    else:
        filter_query = {
            "and": [
                {"property": "Tags", "multi_select": {"contains": "todo"}},
                {"property": "Tags", "multi_select": {"does_not_contain": "todo-done"}}
            ]
        }

    response = httpx.post(
        f"{BASE_URL}/databases/{NOTION_DATABASE_ID}/query",
        headers=HEADERS,
        json={
            "filter": filter_query,
            "sorts": [{"property": "Date", "direction": "ascending"}],
            "page_size": 100
        },
        timeout=30.0
    )

    todos = []
    for page in response.json().get("results", []):
        props = page["properties"]
        title = props["Name"]["title"]
        summary = props["Summary"]["rich_text"]
        date = props["Date"]["date"]
        tags = [t["name"] for t in props["Tags"]["multi_select"]]

        raw = summary[0]["plain_text"] if summary else ""
        metadata = _parse_meta(raw)

        todos.append({
            "id":       page["id"],
            "title":    title[0]["plain_text"] if title else "Untitled",
            "summary":  raw,
            "date":     date["start"] if date else "",
            "tags":     tags,
            "done":     "todo-done" in tags,
            "priority": metadata.get("priority", "medium"),
            "due":      metadata.get("due", ""),
            "note":     metadata.get("note", ""),
        })

    priority_order = {"high": 0, "medium": 1, "low": 2}
    todos.sort(key=lambda t: (
        priority_order.get(t["priority"], 1),
        t["due"] or "9999-99-99"
    ))

    return todos

# ── parse metadata from summary field ────────────────────────────────────────
def _parse_meta(raw: str) -> dict:
    meta = {}
    for line in raw.split("\n"):
        if line.startswith("PRIORITY:"):
            meta["priority"] = line.replace("PRIORITY:", "").strip().lower()
        elif line.startswith("DUE:"):
            meta["due"] = line.replace("DUE:", "").strip()
        elif line.startswith("NOTE:"):
            meta["note"] = line.replace("NOTE:", "").strip()
    return meta


# ── build summary string ──────────────────────────────────────────────────────
def _build_summary(priority: str, due: str, note: str) -> str:
    parts = [f"PRIORITY: {priority}"]
    if due:
        parts.append(f"DUE: {due}")
    if note:
        parts.append(f"NOTE: {note}")
    return "\n".join(parts)


# ── add todo ──────────────────────────────────────────────────────────────────
def add_todo():
    console.print("\n[bold cyan]Add Todo[/]\n")

    title = Prompt.ask("[green]What needs to be done[/]")
    priority = Prompt.ask(
        "[green]Priority[/]",
        choices=["high", "medium", "low"],
        default="medium"
    )

    due = Prompt.ask("[green]Due date (YYYY-MM-DD) or press Enter to skip[/]", default="")
    if due:
        try:
            datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            console.print("[red]Invalid date — skipping due date.[/]")
            due = ""

    note = Prompt.ask("[green]Additional note (optional)[/]", default="")
    today = datetime.now().strftime("%Y-%m-%d")

    summary = _build_summary(priority, due, note)
    tags = ["todo", f"priority-{priority}"]

    httpx.post(
        f"{BASE_URL}/pages",
        headers=HEADERS,
        json={
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": {
                "Name":    {"title": [{"text": {"content": title}}]},
                "Date":    {"date": {"start": today}},
                "Tags":    {"multi_select": [{"name": t} for t in tags]},
                "Summary": {"rich_text": [{"text": {"content": summary}}]}
            }
        },
        timeout=30.0
    )

    icon = PRIORITY_ICONS.get(priority, "🟡")
    color = PRIORITY_COLORS.get(priority, "white")

    console.print(Panel(
        f"[bold green]✓ Todo added![/]\n\n"
        f"[cyan]Task:[/]     {title}\n"
        f"[cyan]Priority:[/] [{color}]{icon} {priority.upper()}[/]\n"
        f"[cyan]Due:[/]      {due or '—'}\n"
        f"[cyan]Note:[/]     {note or '—'}",
        title="Todo"
    ))


# ── list todos ────────────────────────────────────────────────────────────────
def list_todos():
    todos = fetch_todos()

    if not todos:
        console.print(Panel(
            "[dim]No pending todos. You're all caught up! ✓[/]",
            title="[bold cyan]Todo List[/]",
            border_style="cyan"
        ))
        return

    _render_todo_table(todos, title="Pending Todos")


def _render_todo_table(todos, title="Todos"):
    today = datetime.now().strftime("%Y-%m-%d")

    table = Table(title=title, show_lines=True)
    table.add_column("#",        style="cyan",  width=4)
    table.add_column("P",        width=3)
    table.add_column("Task",     style="white", width=38, overflow="fold")
    table.add_column("Due",      width=12)
    table.add_column("Note",     style="dim",   width=24, overflow="fold")

    for i, t in enumerate(todos, 1):
        icon  = PRIORITY_ICONS.get(t["priority"], "🟡")
        color = PRIORITY_COLORS.get(t["priority"], "white")

        # highlight overdue in red
        due_display = t["due"] or "—"
        if t["due"] and t["due"] < today:
            due_display = f"[bright_red]{t['due']} ⚠[/]"
        elif t["due"] == today:
            due_display = f"[bright_yellow]{t['due']} ★[/]"

        table.add_row(
            str(i),
            icon,
            f"[{color}]{t['title']}[/]",
            due_display,
            t["note"][:22] if t["note"] else "—"
        )

    console.print(table)
    console.print(f"\n[green]{len(todos)} pending todo(s)[/]")


# ── mark complete ─────────────────────────────────────────────────────────────
def complete_todo():
    todos = fetch_todos()
    if not todos:
        console.print("[yellow]No pending todos.[/]")
        return

    _render_todo_table(todos, title="Select todo to complete")

    idx = Prompt.ask("[green]Enter number to mark complete (or 0 to cancel)[/]")
    if not idx.isdigit() or int(idx) == 0:
        console.print("[yellow]Cancelled.[/]")
        return

    idx = int(idx)
    if not (1 <= idx <= len(todos)):
        console.print("[red]Invalid number.[/]")
        return

    todo = todos[idx - 1]
    confirmed = Confirm.ask(
        f"[green]Mark '[bold]{todo['title']}[/]' as complete?[/]"
    )
    if not confirmed:
        console.print("[yellow]Cancelled.[/]")
        return

    # update tags — remove todo, add todo-done
    new_tags = [t for t in todo["tags"] if t != "todo"] + ["todo-done"]

    httpx.patch(
        f"{BASE_URL}/pages/{todo['id']}",
        headers=HEADERS,
        json={
            "properties": {
                "Tags": {
                    "multi_select": [{"name": t} for t in new_tags]
                }
            }
        },
        timeout=30.0
    )

    console.print(Panel(
        f"[bold green]✓ Done![/]\n\n[dim]{todo['title']}[/]",
        title="Todo Complete"
    ))


# ── delete todo ───────────────────────────────────────────────────────────────
def delete_todo():
    todos = fetch_todos()
    if not todos:
        console.print("[yellow]No pending todos.[/]")
        return

    _render_todo_table(todos, title="Select todo to delete")

    idx = Prompt.ask("[green]Enter number to delete (or 0 to cancel)[/]")
    if not idx.isdigit() or int(idx) == 0:
        console.print("[yellow]Cancelled.[/]")
        return

    idx = int(idx)
    if not (1 <= idx <= len(todos)):
        console.print("[red]Invalid number.[/]")
        return

    todo = todos[idx - 1]
    confirmed = Confirm.ask(
        f"[red]Delete '[bold]{todo['title']}[/]'?[/]"
    )
    if not confirmed:
        console.print("[yellow]Cancelled.[/]")
        return

    httpx.patch(
        f"{BASE_URL}/pages/{todo['id']}",
        headers=HEADERS,
        json={"archived": True},
        timeout=30.0
    )

    console.print(Panel(
        f"[bold green]✓ Deleted![/]\n\n[dim]{todo['title']}[/]",
        title="Todo"
    ))


# ── view completed todos ──────────────────────────────────────────────────────
def view_completed():
    todos = fetch_todos(include_done=True)
    done = [t for t in todos if t["done"]]

    if not done:
        console.print("[yellow]No completed todos yet.[/]")
        return

    table = Table(title="Completed Todos", show_lines=True)
    table.add_column("#",    style="cyan",  width=4)
    table.add_column("Task", style="dim",   width=45, overflow="fold")
    table.add_column("Date", style="dim",   width=12)

    for i, t in enumerate(done, 1):
        table.add_row(str(i), f"[dim]✓ {t['title']}[/]", t["date"])

    console.print(table)
    console.print(f"\n[dim]{len(done)} completed todo(s)[/]")


# ── todo interactive menu ─────────────────────────────────────────────────────
def run_todos():
    console.print(Panel(
        "[bold cyan]NotionMind Todo List[/]\n\n"
        "[dim]Options:\n"
        "  1. Add todo\n"
        "  2. List pending todos\n"
        "  3. Mark complete\n"
        "  4. Delete\n"
        "  5. View completed\n"
        "  0. Back[/]",
        title="✅ Todos"
    ))

    choice = Prompt.ask("[green]Choose[/]", choices=["0", "1", "2", "3", "4", "5"])

    if choice == "1":
        add_todo()
    elif choice == "2":
        list_todos()
    elif choice == "3":
        complete_todo()
    elif choice == "4":
        delete_todo()
    elif choice == "5":
        view_completed()
    elif choice == "0":
        return


if __name__ == "__main__":
    run_todos()
