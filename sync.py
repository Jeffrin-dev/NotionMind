import os
import json
import time
import subprocess
import tempfile
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

load_dotenv()

console = Console()
CACHE_FILE = os.path.expanduser("~/.notionmind_cache.json")

# ── load cache ────────────────────────────────────────────────────────────────
def load_cache() -> list:
    if not os.path.exists(CACHE_FILE):
        return []
    with open(CACHE_FILE, "r") as f:
        return json.load(f)

# ── save cache ────────────────────────────────────────────────────────────────
def save_cache(notes: list):
    with open(CACHE_FILE, "w") as f:
        json.dump(notes, f, indent=2)

# ── sync pull ─────────────────────────────────────────────────────────────────
def sync_pull():
    from mcp_client import mcp_list_all_notes
    console.print("\n[dim]Pulling notes from Notion...[/]")

    notes = mcp_list_all_notes(limit=100)
    old_cache = load_cache()
    old_ids = {n["id"]: n for n in old_cache}

    new_count = 0
    updated_count = 0

    for note in notes:
        if note["id"] not in old_ids:
            new_count += 1
        elif note["summary"] != old_ids[note["id"]].get("summary"):
            updated_count += 1

    save_cache(notes)

    console.print(Panel(
        f"[bold green]✓ Sync Pull Complete![/]\n\n"
        f"[cyan]Total notes:[/]   {len(notes)}\n"
        f"[cyan]New notes:[/]     {new_count}\n"
        f"[cyan]Updated notes:[/] {updated_count}\n"
        f"[cyan]Cache:[/]         {CACHE_FILE}",
        title="Sync Pull"
    ))

    return notes

# ── sync push ─────────────────────────────────────────────────────────────────
def sync_push():
    import httpx
    console.print("\n[dim]Checking for local edits to push...[/]")

    cache = load_cache()
    edited = [n for n in cache if n.get("edited", False)]

    if not edited:
        console.print("[yellow]No local edits found to push.[/]")
        return

    console.print(f"[green]Found {len(edited)} edited note(s) to push[/]\n")

    for note in edited:
        console.print(f"[dim]→ Pushing: {note['title']}...[/]")
        httpx.patch(
            f"https://api.notion.com/v1/pages/{note['id']}",
            headers={
                "Authorization": f"Bearer {os.environ['NOTION_API_KEY']}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            },
            json={
                "properties": {
                    "Summary": {
                        "rich_text": [{"text": {"content": note["summary"]}}]
                    },
                    "Tags": {
                        "multi_select": [{"name": t} for t in note.get("tags", [])]
                    }
                }
            }
        )
        note["edited"] = False
        console.print(f"  [green]✓ Pushed:[/] {note['title']}")

    save_cache(cache)

    console.print(Panel(
        f"[bold green]✓ Pushed {len(edited)} note(s) to Notion![/]",
        title="Sync Push"
    ))

# ── edit note locally ─────────────────────────────────────────────────────────
def edit_note():
    cache = load_cache()

    if not cache:
        console.print("[yellow]Cache empty. Run sync pull first![/]")
        return

    table = Table(title="Select a note to edit", show_lines=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Date", style="white", width=12)
    table.add_column("Title", style="white", width=40)
    table.add_column("Tags", style="dim", width=20)

    for i, n in enumerate(cache, 1):
        table.add_row(
            str(i),
            n["date"],
            n["title"],
            ", ".join(n.get("tags", [])) or "—"
        )

    console.print(table)

    idx = Prompt.ask("[green]Enter number[/]")
    if not idx.isdigit() or not (1 <= int(idx) <= len(cache)):
        console.print("[red]Invalid number.[/]")
        return

    note = cache[int(idx) - 1]

    # write to temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False
    ) as tmp:
        tmp.write(f"# {note['title']}\n")
        tmp.write(f"Date: {note['date']}\n")
        tmp.write(f"Tags: {', '.join(note.get('tags', []))}\n")
        tmp.write(f"\n---\n\n")
        tmp.write(note["summary"])
        tmpfile = tmp.name

    # detect editor
    editor = os.environ.get("EDITOR", "nano")
    console.print(f"[dim]Opening in {editor}...[/]")
    subprocess.run([editor, tmpfile])

    # read back edited content
    with open(tmpfile, "r") as f:
        content = f.read()

    # extract summary (everything after ---)
    if "---" in content:
        new_summary = content.split("---", 1)[1].strip()
    else:
        new_summary = content.strip()

    os.unlink(tmpfile)

    if new_summary == note["summary"]:
        console.print("[yellow]No changes detected.[/]")
        return

    # mark as edited in cache
    cache[int(idx) - 1]["summary"] = new_summary
    cache[int(idx) - 1]["edited"] = True
    save_cache(cache)

    console.print(Panel(
        f"[bold green]✓ Note edited locally![/]\n\n"
        f"[cyan]Title:[/] {note['title']}\n"
        f"[dim]Run 'sync push' to save changes to Notion.[/]",
        title="Edit Note"
    ))

# ── watch mode ────────────────────────────────────────────────────────────────
def watch_mode():
    from mcp_client import mcp_list_all_notes

    console.print(Panel(
        "[bold cyan]Watch Mode Active[/]\n"
        "[dim]Polling Notion every 30 seconds for changes.\n"
        "Press Ctrl+C to stop.[/]",
        title="Sync Watch"
    ))

    last_cache = {n["id"]: n for n in load_cache()}

    try:
        while True:
            notes = mcp_list_all_notes(limit=100)
            current = {n["id"]: n for n in notes}

            # detect changes
            for nid, note in current.items():
                if nid not in last_cache:
                    console.print(
                        f"[green]✨ New note:[/] {note['title']} "
                        f"[dim]({note['date']})[/]"
                    )
                elif note["summary"] != last_cache[nid].get("summary"):
                    console.print(
                        f"[cyan]✏️  Updated:[/] {note['title']} "
                        f"[dim]({note['date']})[/]"
                    )

            # detect deletions
            for nid in last_cache:
                if nid not in current:
                    console.print(
                        f"[red]🗑️  Deleted:[/] {last_cache[nid]['title']}"
                    )

            last_cache = current
            save_cache(notes)

            now = datetime.now().strftime("%H:%M:%S")
            console.print(f"[dim]{now} — watching... (Ctrl+C to stop)[/]", end="\r")
            time.sleep(30)

    except KeyboardInterrupt:
        console.print("\n[dim]Watch mode stopped.[/]")

# ── sync interactive menu ─────────────────────────────────────────────────────
def run_sync():
    console.print(Panel(
        "[bold cyan]NotionMind Sync[/]\n\n"
        "[dim]Options:\n"
        "  1. Pull — fetch latest from Notion to local cache\n"
        "  2. Push — push local edits back to Notion\n"
        "  3. Edit — edit a note locally then push\n"
        "  4. Watch — monitor Notion for real-time changes\n"
        "  0. Back[/]",
        title="Sync"
    ))

    choice = Prompt.ask("[green]Choose[/]", choices=["0", "1", "2", "3", "4"])

    if choice == "1":
        sync_pull()
    elif choice == "2":
        sync_push()
    elif choice == "3":
        sync_pull()
        edit_note()
    elif choice == "4":
        sync_pull()
        watch_mode()
    elif choice == "0":
        return

if __name__ == "__main__":
    run_sync()
