import os
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.syntax import Syntax

load_dotenv()

console = Console()

# ── save to notion ────────────────────────────────────────────────────────────
def kb_save(title: str, summary: str, tags: list):
    from mcp_client import mcp_create_note
    today = datetime.now().strftime("%Y-%m-%d")
    mcp_create_note(
        title=title,
        summary=summary,
        tags=tags,
        date=today
    )

# ── save code snippet ─────────────────────────────────────────────────────────
def save_snippet():
    console.print("\n[bold cyan]Save Code Snippet[/]\n")

    title = Prompt.ask("[green]Snippet title[/]")
    language = Prompt.ask("[green]Language[/]", default="python")
    description = Prompt.ask("[green]Description[/]")

    console.print(f"[dim]Paste your code below. Type 'END' on a new line when done.[/]")
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    code = "\n".join(lines)

    summary = (
        f"TYPE: snippet\n"
        f"LANGUAGE: {language}\n"
        f"DESCRIPTION: {description}\n\n"
        f"CODE:\n{code}"
    )

    kb_save(
        title=f"[Snippet] {title}",
        summary=summary,
        tags=["snippet", language, "kb"]
    )

    # show with syntax highlighting
    console.print(Panel(
        Syntax(code, language, theme="monokai", line_numbers=True),
        title=f"[bold cyan]{title}[/]"
    ))

    console.print(Panel(
        f"[bold green]✓ Snippet saved![/]\n\n"
        f"[cyan]Title:[/]    {title}\n"
        f"[cyan]Language:[/] {language}",
        title="Knowledge Base"
    ))

# ── save terminal command ─────────────────────────────────────────────────────
def save_command():
    console.print("\n[bold cyan]Save Terminal Command[/]\n")

    title = Prompt.ask("[green]Command title[/]")
    command = Prompt.ask("[green]Command[/]")
    description = Prompt.ask("[green]What does it do[/]")
    example = Prompt.ask("[green]Example usage (optional)[/]", default="")

    summary = (
        f"TYPE: command\n"
        f"COMMAND: {command}\n"
        f"DESCRIPTION: {description}\n"
    )
    if example:
        summary += f"EXAMPLE: {example}\n"

    kb_save(
        title=f"[CMD] {title}",
        summary=summary,
        tags=["command", "terminal", "kb"]
    )

    console.print(Panel(
        f"[bold green]✓ Command saved![/]\n\n"
        f"[cyan]Title:[/]       {title}\n"
        f"[cyan]Command:[/]     [bold white]{command}[/]\n"
        f"[cyan]Description:[/] {description}",
        title="Knowledge Base"
    ))

# ── save bookmark ─────────────────────────────────────────────────────────────
def save_bookmark():
    console.print("\n[bold cyan]Save Bookmark[/]\n")

    url = Prompt.ask("[green]URL[/]")
    title = Prompt.ask("[green]Title[/]")
    description = Prompt.ask("[green]Description[/]")

    # auto-fetch page summary if online
    auto_summary = ""
    try:
        import httpx
        from groq import Groq
        groq = Groq(api_key=os.environ["GROQ_API_KEY"])

        console.print("[dim]Fetching page info...[/]")
        resp = httpx.get(url, timeout=5, follow_redirects=True)

        # extract title from HTML if available
        if "<title>" in resp.text:
            start = resp.text.find("<title>") + 7
            end = resp.text.find("</title>")
            page_title = resp.text[start:end].strip()[:100]
            auto_summary = f"Page title: {page_title}\n"
    except:
        pass

    summary = (
        f"TYPE: bookmark\n"
        f"URL: {url}\n"
        f"DESCRIPTION: {description}\n"
    )
    if auto_summary:
        summary += auto_summary

    kb_save(
        title=f"[Bookmark] {title}",
        summary=summary,
        tags=["bookmark", "kb"]
    )

    console.print(Panel(
        f"[bold green]✓ Bookmark saved![/]\n\n"
        f"[cyan]Title:[/]       {title}\n"
        f"[cyan]URL:[/]         {url}\n"
        f"[cyan]Description:[/] {description}",
        title="Knowledge Base"
    ))

# ── browse knowledge base ─────────────────────────────────────────────────────
def browse_kb():
    from mcp_client import mcp_list_all_notes

    console.print("\n[bold cyan]Browse Knowledge Base[/]\n")
    console.print("  1. All KB items")
    console.print("  2. Snippets only")
    console.print("  3. Commands only")
    console.print("  4. Bookmarks only")
    console.print("  5. Search KB")

    choice = Prompt.ask("[green]Choose[/]", choices=["1", "2", "3", "4", "5"])

    notes = mcp_list_all_notes(limit=100)
    kb_notes = [n for n in notes if "kb" in n.get("tags", [])]

    if choice == "1":
        filtered = kb_notes
        label = "All KB Items"
    elif choice == "2":
        filtered = [n for n in kb_notes if "snippet" in n.get("tags", [])]
        label = "Snippets"
    elif choice == "3":
        filtered = [n for n in kb_notes if "command" in n.get("tags", [])]
        label = "Commands"
    elif choice == "4":
        filtered = [n for n in kb_notes if "bookmark" in n.get("tags", [])]
        label = "Bookmarks"
    elif choice == "5":
        keyword = Prompt.ask("[green]Search keyword[/]")
        filtered = [
            n for n in kb_notes
            if keyword.lower() in n["title"].lower()
            or keyword.lower() in n["summary"].lower()
        ]
        label = f"Search: {keyword}"

    if not filtered:
        console.print(f"[yellow]No items found.[/]")
        return

    table = Table(title=label, show_lines=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Type", style="cyan", width=10)
    table.add_column("Title", style="white", width=35)
    table.add_column("Date", style="dim", width=12)

    for i, n in enumerate(filtered, 1):
        # detect type from tags
        if "snippet" in n.get("tags", []):
            kb_type = "snippet"
        elif "command" in n.get("tags", []):
            kb_type = "command"
        elif "bookmark" in n.get("tags", []):
            kb_type = "bookmark"
        else:
            kb_type = "note"

        table.add_row(str(i), kb_type, n["title"], n["date"])

    console.print(table)

    # view full content
    idx = Prompt.ask("[green]Enter number to view (or 0 to skip)[/]", default="0")
    if idx == "0" or not idx.isdigit():
        return

    selected = filtered[int(idx) - 1]
    summary = selected["summary"]

    # render snippets with syntax highlighting
    if "snippet" in selected.get("tags", []) and "CODE:" in summary:
        parts = summary.split("CODE:\n", 1)
        meta = parts[0]
        code = parts[1].strip() if len(parts) > 1 else ""

        # detect language
        lang = "python"
        for line in meta.split("\n"):
            if line.startswith("LANGUAGE:"):
                lang = line.replace("LANGUAGE:", "").strip()
                break

        console.print(Panel(meta.strip(), title="[cyan]Info[/]"))
        console.print(Panel(
            Syntax(code, lang, theme="monokai", line_numbers=True),
            title="[bold cyan]Code[/]"
        ))
    else:
        console.print(Panel(
            f"[bold white]{summary}[/]",
            title=f"[bold]{selected['title']}[/]"
        ))

# ── knowledge base menu ───────────────────────────────────────────────────────
def run_kb():
    console.print(Panel(
        "[bold cyan]NotionMind Knowledge Base[/]\n\n"
        "[dim]Options:\n"
        "  1. Save code snippet\n"
        "  2. Save terminal command\n"
        "  3. Save bookmark\n"
        "  4. Browse knowledge base\n"
        "  0. Back[/]",
        title="Knowledge Base"
    ))

    choice = Prompt.ask("[green]Choose[/]", choices=["0", "1", "2", "3", "4"])

    if choice == "1":
        save_snippet()
    elif choice == "2":
        save_command()
    elif choice == "3":
        save_bookmark()
    elif choice == "4":
        browse_kb()
    elif choice == "0":
        return

if __name__ == "__main__":
    run_kb()
