import os
import json
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from rich.console import Console
from rich.panel import Panel
from rich.progress import track
from mcp_client import (
    mcp_list_all_notes,
    mcp_create_note,
    mcp_update_note,
    MCP_TOOLS
)
from search import web_search, format_search_results

load_dotenv()

groq   = Groq(api_key=os.environ["GROQ_API_KEY"])
console = Console()

# ── log rotation — keep only last 7 days ─────────────────────────────────────
def rotate_log():
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "executor.log")
    
    if not os.path.exists(log_path):
        return
    
    with open(log_path, "r") as f:
        lines = f.readlines()
    
    # keep only lines from last 7 days
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=7)
    
    kept = []
    for line in lines:
        kept.append(line)  # keep all for now, add timestamp logic below
    
    # add a dated separator when rotating
    separator = f"\n{'─'*60}\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Log rotation\n{'─'*60}\n"
    
    # if log is bigger than 500KB, trim it
    if os.path.getsize(log_path) > 500 * 1024:
        # keep only last 200 lines
        trimmed = lines[-200:] if len(lines) > 200 else lines
        with open(log_path, "w") as f:
            f.write(f"[Log trimmed — keeping last 200 lines]\n")
            f.writelines(trimmed)
        console.print("[dim]Log rotated — trimmed to last 200 lines[/]")

# ── weekly report ─────────────────────────────────────────────────────────────
def generate_weekly_report():
    from datetime import datetime, timedelta

    today = datetime.now()
    week_start = (today - timedelta(days=today.weekday() + 1)).strftime("%Y-%m-%d")  # last Sunday
    week_end = today.strftime("%Y-%m-%d")

    console.print(Panel(
        f"[bold cyan]Generating Weekly Report[/]\n"
        f"[dim]{week_start} → {week_end}[/]",
        title="Weekly Report"
    ))

    # fetch all notes
    notes = mcp_list_all_notes(limit=100)

    # filter to this week
    weekly_notes = [
        n for n in notes
        if week_start <= n.get("date", "") <= week_end
        and "weekly-report" not in n.get("tags", [])
        and "summary" not in n.get("tags", [])
    ]

    if not weekly_notes:
        console.print("[yellow]No notes found for this week.[/]")
        return

    # build context
    context = "\n\n".join([
        f"[{n['date']}] {n['title']}: {n['summary']}"
        for n in weekly_notes
    ])

    console.print(f"[dim]Summarising {len(weekly_notes)} notes with Groq...[/]")

    # ask Groq to generate a weekly report
    response = groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a personal assistant generating a weekly review report. "
                    "Based on the user's notes, write a clear and structured weekly report with these sections:\n"
                    "1. 🏆 Key Achievements\n"
                    "2. 🛠 Work Done\n"
                    "3. 📚 Things Learned\n"
                    "4. 📥 Pending Tasks\n"
                    "5. 🎯 Focus for Next Week\n\n"
                    "Be concise, specific and friendly. Use the notes as your only source."
                )
            },
            {
                "role": "user",
                "content": f"My notes from this week ({week_start} to {week_end}):\n\n{context}"
            }
        ],
        max_tokens=1500
    )

    report = response.choices[0].message.content.strip()

    # save to Notion
    full_summary = (
        f"Weekly Report: {week_start} to {week_end}\n\n"
        f"{report}"
    )

    mcp_create_note(
        title=f"Weekly Report {week_start}",
        summary=full_summary,
        tags=["weekly-report", "auto-generated"],
        date=week_end
    )

    console.print(Panel(
        f"[bold white]{report}[/]",
        title=f"[bold cyan]Weekly Report — {week_start} to {week_end}[/]"
    ))

    # send to Telegram
    try:
        import httpx as _httpx
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        if token and chat_id:
            msg = f"📊 *Weekly Report — {week_start} to {week_end}*\n\n{report[:3000]}"
            _httpx.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
            )
            console.print("[green]✓ Report sent to Telegram![/]")
    except:
        pass

    console.print(Panel(
        f"[bold green]✓ Weekly report saved to Notion![/]\n"
        f"[dim]Tagged: weekly-report, auto-generated[/]",
        title="Done"
    ))

# ── extended tools including web search ──────────────────────────────────────
EXECUTOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information on any topic",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
                    }
                },
                "required": ["query"]
            }
        }
    }
]
def dispatch_executor_tool(name: str, args: dict):
    """Dispatch tool calls including web search"""
    from mcp_client import dispatch_tool
    if name == "web_search":
        results = web_search(args["query"])
        return format_search_results(results)
    else:
        return dispatch_tool(name, args)

def execute_task(task: str) -> str:
    """Execute a single task — search web then summarise"""
    console.print(f"  [dim]→ searching web...[/]")
    
    # step 1: search the web directly
    results = web_search(task, max_results=5)
    search_context = format_search_results(results)

    # step 2: ask Groq to summarise using search results
    response = groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a research assistant. "
                    "Use the web search results provided to answer the task. "
                    "Be clear, concise and well structured. "
                    "Today's date: " + datetime.now().strftime("%Y-%m-%d")
                )
            },
            {
                "role": "user",
                "content": (
                    f"Task: {task}\n\n"
                    f"Web search results:\n{search_context}\n\n"
                    f"Please complete the task using these results."
                )
            }
        ],
        max_tokens=1000
    )

    return response.choices[0].message.content or "Task completed."

def run_inbox():
    rotate_log()
    """Read pending tasks from Notion and execute them"""
    console.print(Panel(
        "[bold cyan]NotionMind Executor[/]\n"
        "[dim]Reading your Notion inbox...[/]",
        title="Starting"
    ))

    # fetch all notes tagged "inbox" or "todo"
    notes = mcp_list_all_notes(limit=50)
    pending = [
        n for n in notes
        if any(t.lower() in ["inbox", "todo", "task"]
               for t in n.get("tags", []))
    ]

    if not pending:
        console.print(
            "[yellow]No pending tasks found.\n"
            "Add notes with tag 'inbox', 'todo' or 'task' to get started![/]"
        )
        return

    console.print(f"[green]Found {len(pending)} pending task(s)[/]\n")

    results = []
    for note in pending:
        task = note["summary"] or note["title"]
        console.print(f"[bold]Task:[/] {task}")

        result = execute_task(task)

        # update the note with result
        updated_summary = (
            f"TASK: {task}\n\n"
            f"RESULT:\n{result}\n\n"
            f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        mcp_update_note(note["id"], updated_summary)

        # mark as done — remove inbox tag, add done tag
        import httpx
        httpx.patch(
            f"https://api.notion.com/v1/pages/{note['id']}",
            headers={
                "Authorization": f"Bearer {os.environ['NOTION_API_KEY']}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            },
            json={
                "properties": {
                    "Tags": {
                        "multi_select": [{"name": "done"}]
                    }
                }
            }
        )
        # re-tag as done
        console.print(f"  [green]✓ Done[/]\n")
        results.append({"task": task, "result": result})

    # create daily summary note
    create_daily_summary(results)

def create_daily_summary(results: list):
    """Create a daily summary note in Notion"""
    today = datetime.now().strftime("%Y-%m-%d")

    summary_parts = [f"Daily Summary — {today}\n"]
    for i, r in enumerate(results, 1):
        summary_parts.append(f"{i}. {r['task']}\n→ {r['result'][:200]}\n")

    full_summary = "\n".join(summary_parts)

    mcp_create_note(
        title=f"Daily Summary {today}",
        summary=full_summary,
        tags=["summary", "daily", "auto-generated"],
        date=today
    )

    console.print(Panel(
        f"[bold green]✓ All tasks completed![/]\n\n"
        f"[cyan]Daily summary saved to Notion.[/]\n"
        f"[dim]Check your MindLog Notes database.[/]",
        title="Done"
    ))

if __name__ == "__main__":
    run_inbox()
