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
