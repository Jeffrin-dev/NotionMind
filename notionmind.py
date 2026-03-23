import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client
from groq import Groq
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

load_dotenv()

notion = Client(auth=os.environ["NOTION_API_KEY"])
groq   = Groq(api_key=os.environ["GROQ_API_KEY"])
DB_ID  = os.environ["NOTION_DATABASE_ID"]

console = Console()

# ── save a note to Notion ─────────────────────────────────────────────────────
def save_note(text):
    today = datetime.now().strftime("%Y-%m-%d")

    # ask Groq to auto-generate a title + tags
    response = groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{
            "role": "user",
            "content": f"""Given this note, return ONLY this format, nothing else:
TITLE: <5 word title>
TAGS: <tag1>,<tag2>,<tag3>

Note: {text}"""
        }]
    )

    raw = response.choices[0].message.content.strip()
    lines = raw.split("\n")
    title = "Untitled"
    tags  = []

    for line in lines:
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
        if line.startswith("TAGS:"):
            tags = [t.strip() for t in line.replace("TAGS:", "").split(",")]

    # write to Notion
    notion.pages.create(
        parent={"database_id": DB_ID},
        properties={
            "Name": {
                "title": [{"text": {"content": title}}]
            },
            "Date": {
                "date": {"start": today}
            },
            "Tags": {
                "multi_select": [{"name": t} for t in tags if t]
            },
            "Summary": {
                "rich_text": [{"text": {"content": text}}]
            }
        }
    )
    console.print(Panel(
        f"[bold green]✓ Saved![/]\n\n"
        f"[cyan]Title:[/] {title}\n"
        f"[cyan]Tags:[/]  {', '.join(tags)}\n"
        f"[cyan]Date:[/]  {today}",
        title="NotionMind"
    ))

# ── fetch recent notes from Notion ───────────────────────────────────────────
def fetch_notes(limit=20):
    results = notion.databases.query(
        database_id=DB_ID,
        sorts=[{"property": "Date", "direction": "descending"}],
        page_size=limit
    )
    notes = []
    for page in results["results"]:
        props = page["properties"]
        title = props["Name"]["title"]
        summary = props["Summary"]["rich_text"]
        date = props["Date"]["date"]

        tags = props["Tags"]["multi_select"]
        notes.append({
            "id":      page["id"],
            "title":   title[0]["plain_text"] if title else "Untitled",
            "summary": summary[0]["plain_text"] if summary else "",
            "date":    date["start"] if date else "unknown",
            "tags":    [t["name"] for t in tags] if tags else []
        })
    return notes

# ── ask a question about your notes ──────────────────────────────────────────
def ask_question(question, return_text=False):
    console.print("[dim]Searching your Notion notes...[/]")
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    all_notes = fetch_notes(limit=50)

    # if question mentions today, filter to today's notes only
    today_keywords = ["today", "this morning", "tonight", "just now"]
    if any(k in question.lower() for k in today_keywords):
        notes = [n for n in all_notes if n.get("date") == today]
        if not notes:
            notes = all_notes  # fallback to all if none today
    else:
        notes = all_notes

    if not notes:
        console.print("[yellow]No notes found in your database yet.[/]")
        return

    # build context from notes
    context = "\n\n".join([
        f"[{n['date']}] {n['title']}: {n['summary']}"
        for n in notes
    ])

    response = groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful personal assistant. "
                    "Answer questions based only on the user's notes below. "
                    "Be concise and specific. If you can't find the answer, say so. "
                    f"Today's date is {today}. Pay attention to dates when answering "
                    "questions about 'today', 'yesterday', 'this week' etc.\n\n"
                    f"NOTES:\n{context}"
                )
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )

    answer = response.choices[0].message.content.strip()
    console.print(Panel(
        f"[bold white]{answer}[/]",
        title="[cyan]NotionMind Answer[/]"
    ))
    if return_text:
        return answer
    

# ── list all notes ────────────────────────────────────────────────────────────
def list_notes():
    from rich.table import Table
    notes = fetch_notes(limit=20)
    if not notes:
        console.print("[yellow]No notes yet. Use 'save' to add some![/]")
        return

    table = Table(title="Your NotionMind Notes", show_lines=True)
    table.add_column("Date", style="cyan", width=12)
    table.add_column("Title", style="white", width=35)
    table.add_column("Summary", style="dim", width=40)

    for n in notes:
        table.add_row(n["date"], n["title"], n["summary"][:80])

    console.print(table)

# ── list today notes ──────────────────────────────────────────────────────────
def show_today():
    from rich.table import Table
    today = datetime.now().strftime("%Y-%m-%d")
    notes = fetch_notes(limit=50)
    todays = [n for n in notes if n["date"] == today]

    if not todays:
        console.print(Panel(
            f"[yellow]No notes yet for today ({today}).\n"
            f"Use 'save' to add your first note![/]",
            title="Today"
        ))
        return

    table = Table(title=f"Today's Notes — {today}", show_lines=True)
    table.add_column("Title", style="white", width=35)
    table.add_column("Tags", style="cyan", width=20)
    table.add_column("Summary", style="dim", width=40)

    for n in todays:
        table.add_row(
            n["title"],
            ", ".join(n["tags"]) if n["tags"] else "—",
            n["summary"][:80]
        )

    console.print(table)
    console.print(f"\n[green]{len(todays)} note(s) today[/]")
    
# ── search notes by keyword ───────────────────────────────────────────────────
def search_notes(keyword):
    notes = fetch_notes(limit=50)
    keyword_lower = keyword.lower()

    matches = [
        n for n in notes
        if keyword_lower in n["title"].lower()
        or keyword_lower in n["summary"].lower()
    ]

    if not matches:
        console.print(f"[yellow]No notes found matching '{keyword}'[/]")
        return

    from rich.table import Table
    table = Table(title=f"Results for '{keyword}'", show_lines=True)
    table.add_column("Date", style="cyan", width=12)
    table.add_column("Title", style="white", width=35)
    table.add_column("Summary", style="dim", width=40)

    for n in matches:
        table.add_row(n["date"], n["title"], n["summary"][:80])

    console.print(table)
    console.print(f"\n[green]Found {len(matches)} note(s)[/]")
    
    
    # ── stats ─────────────────────────────────────────────────────────────────────
def show_stats():
    from rich.table import Table
    from collections import Counter

    notes = fetch_notes(limit=100)

    if not notes:
        console.print("[yellow]No notes yet![/]")
        return

    # count tags
    all_tags = []
    for n in notes:
        all_tags.extend(n.get("tags", []))
    tag_counts = Counter(all_tags)
    top_tags = tag_counts.most_common(5)

    # basic stats
    total = len(notes)
    dates = [n["date"] for n in notes if n["date"] != "unknown"]
    dates.sort()
    first = dates[0] if dates else "N/A"
    latest = dates[-1] if dates else "N/A"

    # streak calculation
    from datetime import datetime, timedelta
    streak = 0
    today = datetime.now().date()
    for i in range(30):
        day = str(today - timedelta(days=i))
        if day in dates:
            streak += 1
        else:
            break

    tags_display = "  ".join([f"[green]{t}[/] ({c})" for t,c in top_tags]) or "none yet"

    console.print(Panel(
        f"[bold cyan]Total notes:[/]    {total}\n"
        f"[bold cyan]First note:[/]     {first}\n"
        f"[bold cyan]Latest note:[/]    {latest}\n"
        f"[bold cyan]Streak:[/]         {streak} day(s) 🔥\n\n"
        f"[bold cyan]Top tags:[/]\n  {tags_display}",
        title="[bold]NotionMind Stats[/]"
    ))
    
# ── add inbox task ────────────────────────────────────────────────────────────
def add_inbox_task(task: str):
    today = datetime.now().strftime("%Y-%m-%d")
    notion.pages.create(
        parent={"database_id": DB_ID},
        properties={
            "Name": {
                "title": [{"text": {"content": task[:50]}}]
            },
            "Date": {
                "date": {"start": today}
            },
            "Tags": {
                "multi_select": [{"name": "inbox"}]
            },
            "Summary": {
                "rich_text": [{"text": {"content": task}}]
            }
        }
    )
    console.print(Panel(
        f"[bold green]✓ Added to inbox![/]\n\n"
        f"[cyan]Task:[/] {task}\n"
        f"[dim]Run executor.py to process it[/]",
        title="Inbox"
    ))
    
# ── show completed task results ───────────────────────────────────────────────
def show_results():
    from rich.table import Table
    notes = fetch_notes(limit=50)
    done = [n for n in notes if "done" in n.get("tags", [])]

    if not done:
        console.print("[yellow]No completed tasks yet.[/]")
        return

    console.print(f"\n[bold cyan]Completed Tasks ({len(done)})[/]\n")
    for n in done:
        console.print(Panel(
            f"[cyan]Date:[/] {n['date']}\n\n"
            f"{n['summary']}",
            title=f"[bold]{n['title']}[/]"
        ))

# ── delete a note ─────────────────────────────────────────────────────────────
def delete_note():
    from rich.table import Table
    notes = fetch_notes(limit=20)

    if not notes:
        console.print("[yellow]No notes to delete.[/]")
        return

    # show numbered list
    table = Table(title="Select a note to delete", show_lines=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Date", style="white", width=12)
    table.add_column("Title", style="white", width=40)

    for i, n in enumerate(notes, 1):
        table.add_row(str(i), n["date"], n["title"])

    console.print(table)

    # ask which number to delete
    choice = Prompt.ask("[red]Enter number to delete (or 0 to cancel)[/]")

    if not choice.isdigit():
        console.print("[yellow]Cancelled.[/]")
        return

    idx = int(choice)
    if idx == 0:
        console.print("[yellow]Cancelled.[/]")
        return

    if idx < 1 or idx > len(notes):
        console.print("[red]Invalid number.[/]")
        return

    selected = notes[idx - 1]

    # confirm before deleting
    from rich.prompt import Confirm
    confirmed = Confirm.ask(
        f"[red]Delete '[bold]{selected['title']}[/]'?[/]"
    )

    if not confirmed:
        console.print("[yellow]Cancelled.[/]")
        return

    # archive the page (Notion API doesn't hard delete, it archives)
    notion.pages.update(
        page_id=selected["id"],
        archived=True
    )

    console.print(Panel(
        f"[bold green]✓ Deleted![/]\n\n"
        f"[dim]{selected['title']}[/]",
        title="NotionMind"
    ))
            
# ── export notes to markdown ──────────────────────────────────────────────────
def export_notes():
    console.print("\n[bold cyan]Export Options:[/]")
    console.print("  1. All notes")
    console.print("  2. Today's notes only")
    console.print("  3. Filter by tag")
    console.print("  4. Filter by date range")
    console.print("  5. Select a specific note")

    choice = Prompt.ask("[green]Choose[/]", choices=["1", "2", "3", "4","5"])

    notes = fetch_notes(limit=100)
    today = datetime.now().strftime("%Y-%m-%d")

    if choice == "1":
        filtered = notes
        label = "all"

    elif choice == "2":
        filtered = [n for n in notes if n["date"] == today]
        label = f"today_{today}"

    elif choice == "3":
        tag = Prompt.ask("[green]Enter tag[/]")
        filtered = [n for n in notes if tag.lower() in [t.lower() for t in n["tags"]]]
        label = f"tag_{tag}"

    elif choice == "4":
        start = Prompt.ask("[green]Start date (YYYY-MM-DD)[/]")
        end = Prompt.ask("[green]End date (YYYY-MM-DD)[/]")
        filtered = [n for n in notes if start <= n["date"] <= end]
        label = f"{start}_to_{end}"
        
    elif choice == "5":
        from rich.table import Table
        table = Table(title="Select a note to export", show_lines=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Date", style="white", width=12)
        table.add_column("Title", style="white", width=40)

        for i, n in enumerate(notes, 1):
            table.add_row(str(i), n["date"], n["title"])

        console.print(table)

        idx = Prompt.ask("[green]Enter number[/]")
        if not idx.isdigit() or not (1 <= int(idx) <= len(notes)):
            console.print("[red]Invalid number.[/]")
            return

        filtered = [notes[int(idx) - 1]]
        label = f"note_{filtered[0]['title'][:20].replace(' ', '_')}"

    if not filtered:
        console.print("[yellow]No notes found for that filter.[/]")
        return

    filename = f"notionmind_export_{label}.md"

    lines = [
        f"# NotionMind Export — {label}\n",
        f"**Total notes:** {len(filtered)}\n",
        "---\n"
    ]

    for n in filtered:
        tags = ", ".join(n["tags"]) if n["tags"] else "—"
        lines.append(f"## {n['title']}")
        lines.append(f"**Date:** {n['date']}  ")
        lines.append(f"**Tags:** {tags}\n")
        lines.append(f"{n['summary']}\n")
        lines.append("---\n")

    with open(filename, "w") as f:
        f.write("\n".join(lines))

    console.print(Panel(
        f"[bold green]✓ Exported![/]\n\n"
        f"[cyan]File:[/]  {filename}\n"
        f"[cyan]Notes:[/] {len(filtered)}",
        title="Export"
    ))
    
# ── read full page content ────────────────────────────────────────────────────
def read_page():
    from rich.table import Table
    from rich.markdown import Markdown
    from mcp_client import mcp_read_page

    notes = fetch_notes(limit=20)
    if not notes:
        console.print("[yellow]No notes found.[/]")
        return

    table = Table(title="Select a note to read", show_lines=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Date", style="white", width=12)
    table.add_column("Title", style="white", width=40)

    for i, n in enumerate(notes, 1):
        table.add_row(str(i), n["date"], n["title"])

    console.print(table)

    idx = Prompt.ask("[green]Enter number[/]")
    if not idx.isdigit() or not (1 <= int(idx) <= len(notes)):
        console.print("[red]Invalid number.[/]")
        return

    selected = notes[int(idx) - 1]
    console.print(f"\n[dim]Reading page: {selected['title']}...[/]")

    content = mcp_read_page(selected["id"])

    # fallback to summary property if no blocks found
    if content == "No content blocks found in this page.":
        content = selected["summary"] or "No content found."

    console.print(Panel(
        Markdown(content),
        title=f"[bold]{selected['title']}[/] — {selected['date']}"
    ))
        
# ── save image note ───────────────────────────────────────────────────────────
def save_image_note():
    from image import upload_image_to_notion, grab_clipboard_image

    console.print("\n[bold cyan]Image Source:[/]")
    console.print("  1. File path")
    console.print("  2. Clipboard")

    choice = Prompt.ask("[green]Choose[/]", choices=["1", "2"])

    if choice == "1":
        path = Prompt.ask("[green]Image file path[/]")
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            console.print("[red]File not found.[/]")
            return
        image_path = path
    else:
        console.print("[dim]Grabbing image from clipboard...[/]")
        image_path = grab_clipboard_image()
        if not image_path:
            console.print("[red]No image found in clipboard.[/]")
            return

    caption = Prompt.ask("[green]Caption / note for this image[/]")

    # first save a text note to get a page_id
    console.print("[dim]Creating note in Notion...[/]")
    save_note(f"[Image Note] {caption}")

    # fetch the page_id of the note just created
    notes = fetch_notes(limit=1)
    if not notes:
        console.print("[red]Could not retrieve page ID.[/]")
        return

    page_id = notes[0]["id"]

    # upload image to Notion and attach to page
    try:
        upload_image_to_notion(image_path, caption, page_id)
        console.print(Panel(
            f"[bold green]✓ Image note saved![/]\n\n"
            f"[cyan]Caption:[/] {caption}\n"
            f"[cyan]Stored:[/]  Privately in your Notion workspace",
            title="Image Note"
        ))
    except Exception as e:
        console.print(f"[red]Upload failed: {e}[/]")
        
# ── generate weekly report ────────────────────────────────────────────────────
def weekly_report():
    from executor import generate_weekly_report
    generate_weekly_report()        
        
# ── interactive mode ──────────────────────────────────────────────────────────
def interactive():
    notes = fetch_notes(limit=100)
    count = len(notes)

    from voice import is_online, get_language
    online = is_online()
    lang = get_language()
    voice_status = f"[green]online — {lang['name']} neural voice (Edge TTS)[/]" if online else f"[yellow]offline — {lang['name']} espeak fallback[/]"

    console.print(Panel(
        f"[bold cyan]NotionMind[/] — Your Notion-powered AI memory\n"
        f"[dim]You have [bold white]{count}[/] note(s) in your brain.\n"
        f"🔊 Voice: {voice_status}\n\n"
        f"Commands:\n"
        f"  save    — save a new note\n"
        f"  ask     — ask a question about your notes\n"
        f"  list    — show all notes\n"
        f"  search  — filter by keyword\n"
        f"  stats   — streak, note count, top tags\n"
        f"  export  — export all notes to a markdown file\n"
        f"  read    — read full content of a note\n"
        f"  inbox   — add a research task for the agent\n"
        f"  weekly  — generate this week's report\n"
        f"  results — view completed task results\n"
        f"  today   — show only today's notes\n"
        f"  sync    — two-way sync with Notion\n"
        f"  image   — save a screenshot or image to Notion\n"
        f"  voice   — speak instead of type (input + output)\n"
        f"  remind    — set a new reminder\n"
        f"  reminders — list pending reminders\n"
        f"  delete  — remove a note\n"
        f"  organise — AI auto-organise your Notion workspace\n"
        f"  lang    — change voice language\n"
        f"  quit    — exit[/]",
        title="Welcome"
    ))

    while True:
        cmd = Prompt.ask("\n[bold cyan]>[/] What do you want to do",
                         choices=["save", "ask", "list", "search", "stats", "export","read", "inbox", "results", "today", "voice","remind","reminders","weekly","image","organise","sync" ,"delete","lang", "quit"])
                         
        if cmd == "quit":
            console.print("[dim]Goodbye![/]")
            break
        elif cmd == "save":
            text = Prompt.ask("[green]What happened today[/]")
            save_note(text)
        elif cmd == "ask":
            question = Prompt.ask("[green]What do you want to know[/]")
            ask_question(question)
        elif cmd == "list":
            list_notes()
        elif cmd == "search":
            keyword = Prompt.ask("[green]Search by tag or keyword[/]")
            search_notes(keyword)
        elif cmd == "stats":
            show_stats()
        elif cmd == "inbox":
            task = Prompt.ask("[green]What task should the agent research[/]")
            add_inbox_task(task)
        elif cmd == "results":
            show_results()
        elif cmd == "today":
    	    show_today()
        elif cmd == "export":
    	    export_notes()
        elif cmd == "read":
            read_page()
        elif cmd == "weekly":
            weekly_report()
        elif cmd == "sync":
            from sync import run_sync
            run_sync()
        elif cmd == "organise":
            from organiser import run_organiser
            run_organiser()
        elif cmd == "image":
            save_image_note()
        elif cmd == "remind":
            from reminders import add_reminder
            add_reminder()
        elif cmd == "reminders":
            from reminders import list_reminders
            list_reminders()
        elif cmd == "lang":
            from voice import select_language
            select_language()
        elif cmd == "delete":
            delete_note()
        elif cmd == "voice":
            from voice import listen, speak
            from rich.prompt import Confirm
            action = Prompt.ask("Voice for", choices=["save", "ask", "inbox"])
            text = listen()
            if text:
                confirmed = Confirm.ask(f"Heard: '[cyan]{text}[/]' — use this?")
                if confirmed:
                    if action == "save":
                        save_note(text)
                    elif action == "ask":
                        answer = ask_question(text, return_text=True)
                        if answer:
                            speak(answer)
                    elif action == "inbox":
                        add_inbox_task(text)
                else:
                    console.print("[dim]Discarded. Try again.[/]")
                    
# ── CLI entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) == 1:
        interactive()
    elif sys.argv[1] == "save" and len(sys.argv) > 2:
        save_note(" ".join(sys.argv[2:]))
    elif sys.argv[1] == "ask" and len(sys.argv) > 2:
        ask_question(" ".join(sys.argv[2:]))
    elif sys.argv[1] == "inbox" and len(sys.argv) > 2:
        add_inbox_task(" ".join(sys.argv[2:]))
    elif sys.argv[1] == "today":
        show_today()
    elif sys.argv[1] == "export":
        export_notes()
    elif sys.argv[1] == "read":
        read_page()
    elif sys.argv[1] == "weekly":
        weekly_report()
    elif sys.argv[1] == "image":
        save_image_note()
    elif sys.argv[1] == "sync":
        from sync import run_sync
        run_sync()
    elif sys.argv[1] == "organise":
        from organiser import run_organiser
        run_organiser()
    elif sys.argv[1] == "remind" and len(sys.argv) > 2:
        from reminders import add_reminder
        parts = " ".join(sys.argv[2:]).split(" at ")
        msg = parts[0]
        time_str = parts[1] if len(parts) > 1 else None
        add_reminder(message=msg, time_str=time_str)
    else:
        console.print("[red]Usage:[/] python notionmind.py [save|ask|weekly|inbox|sync|organise|today|export|image|read|remind] [text]")
   
