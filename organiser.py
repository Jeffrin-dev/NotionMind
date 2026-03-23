import os
import json
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

load_dotenv()

groq = Groq(api_key=os.environ["GROQ_API_KEY"])
console = Console()

# ── helper: update tags in Notion ─────────────────────────────────────────────
def update_tags(page_id: str, tags: list):
    import httpx
    httpx.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers={
            "Authorization": f"Bearer {os.environ['NOTION_API_KEY']}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        },
        json={
            "properties": {
                "Tags": {
                    "multi_select": [{"name": t} for t in tags]
                }
            }
        }
    )

# ── auto tag untagged notes ───────────────────────────────────────────────────
def auto_tag_notes():
    from mcp_client import mcp_list_all_notes
    console.print("\n[dim]Fetching untagged notes...[/]")

    notes = mcp_list_all_notes(limit=100)
    untagged = [n for n in notes if not n.get("tags")]

    if not untagged:
        console.print("[yellow]No untagged notes found![/]")
        return

    console.print(f"[green]Found {len(untagged)} untagged note(s)[/]\n")

    updated = 0
    for note in untagged:
        console.print(f"[dim]→ Tagging: {note['title']}...[/]")

        response = groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": f"""Suggest 2-3 short tags for this note. Return ONLY comma-separated tags, nothing else.

Title: {note['title']}
Content: {note['summary'][:300]}

Tags:"""
            }]
        )

        raw_tags = response.choices[0].message.content.strip()
        tags = [t.strip().lower() for t in raw_tags.split(",") if t.strip()][:3]

        if tags:
            update_tags(note["id"], tags)
            console.print(f"  [green]✓[/] {note['title']} → {', '.join(tags)}")
            updated += 1

    console.print(Panel(
        f"[bold green]✓ Auto-tagged {updated} note(s)![/]",
        title="Auto Tag"
    ))

# ── find duplicate notes ──────────────────────────────────────────────────────
def find_duplicates():
    from mcp_client import mcp_list_all_notes
    console.print("\n[dim]Scanning for duplicates...[/]")

    notes = mcp_list_all_notes(limit=100)
    if len(notes) < 2:
        console.print("[yellow]Not enough notes to compare.[/]")
        return

    # build list of titles + summaries for Groq
    notes_text = "\n".join([
        f"{i+1}. [{n['date']}] {n['title']}: {n['summary'][:100]}"
        for i, n in enumerate(notes)
    ])

    console.print("[dim]Asking Groq to detect duplicates...[/]")

    response = groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""Analyse these notes and find pairs that are duplicates or very similar in content.
Return ONLY JSON array like this, nothing else:
[{{"note1": 1, "note2": 3, "reason": "both about X"}}, ...]
If no duplicates found return: []

Notes:
{notes_text}"""
        }]
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        duplicates = json.loads(raw)
    except:
        console.print("[yellow]No clear duplicates found.[/]")
        return

    if not duplicates:
        console.print("[green]✓ No duplicates found![/]")
        return

    console.print(f"\n[yellow]Found {len(duplicates)} potential duplicate pair(s):[/]\n")

    table = Table(title="Potential Duplicates", show_lines=True)
    table.add_column("Note 1", style="white", width=30)
    table.add_column("Note 2", style="white", width=30)
    table.add_column("Reason", style="dim", width=30)

    pairs = []
    for d in duplicates:
        try:
            n1 = notes[d["note1"] - 1]
            n2 = notes[d["note2"] - 1]
            table.add_row(n1["title"], n2["title"], d["reason"])
            pairs.append((n1, n2))
        except:
            pass

    console.print(table)

    # offer to merge
    if pairs:
        console.print("\n[cyan]Enter pair numbers to merge (comma-separated), or 0 to skip:[/]")
        for i, (n1, n2) in enumerate(pairs, 1):
            console.print(f"  {i}. {n1['title']} + {n2['title']}")

        choice = Prompt.ask("[green]Your choice[/]", default="0")

        if choice != "0":
            selected = [int(x.strip()) for x in choice.split(",") if x.strip().isdigit()]
            selected_pairs = [pairs[i - 1] for i in selected if 1 <= i <= len(pairs)]
            if selected_pairs:
                merge_notes(selected_pairs)

# ── merge two notes ───────────────────────────────────────────────────────────
def merge_notes(pairs: list = None):
    from mcp_client import mcp_list_all_notes, mcp_create_note, mcp_update_note
    import httpx

    if not pairs:
        # manual selection
        notes = mcp_list_all_notes(limit=50)

        table = Table(title="Select notes to merge", show_lines=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Date", style="white", width=12)
        table.add_column("Title", style="white", width=40)

        for i, n in enumerate(notes, 1):
            table.add_row(str(i), n["date"], n["title"])

        console.print(table)

        idx1 = Prompt.ask("[green]Enter first note number[/]")
        idx2 = Prompt.ask("[green]Enter second note number[/]")

        if not (idx1.isdigit() and idx2.isdigit()):
            console.print("[red]Invalid input.[/]")
            return

        pairs = [(notes[int(idx1) - 1], notes[int(idx2) - 1])]

    for n1, n2 in pairs:
        console.print(f"\n[dim]Merging:[/] {n1['title']} + {n2['title']}")

        

        # ask Groq to merge content
        response = groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": f"""Merge these two notes into one clean, concise note. 
Remove repetition. Keep all unique information.
Return ONLY the merged content, no preamble.

Note 1 ({n1['date']}): {n1['summary']}

Note 2 ({n2['date']}): {n2['summary']}"""
            }]
        )

        merged_content = response.choices[0].message.content.strip()
        merged_tags = list(set(n1.get("tags", []) + n2.get("tags", [])))
        today = datetime.now().strftime("%Y-%m-%d")

        # create merged note
        mcp_create_note(
            title=f"[Merged] {n1['title']}",
            summary=merged_content,
            tags=merged_tags + ["merged"],
            date=today
        )
        
        
        # create merged note
        mcp_create_note(
            title=f"[Merged] {n1['title']}",
            summary=merged_content,
            tags=merged_tags + ["merged"],
            date=today
        )

        # show merged content
        console.print(Panel(
            f"[bold white]{merged_content}[/]",
            title=f"[bold cyan][Merged] {n1['title']}[/]"
        ))

        # archive originals
        for page_id in [n1["id"], n2["id"]]:
            httpx.patch(
                f"https://api.notion.com/v1/pages/{page_id}",
                headers={
                    "Authorization": f"Bearer {os.environ['NOTION_API_KEY']}",
                    "Content-Type": "application/json",
                    "Notion-Version": "2022-06-28"
                },
                json={"archived": True}
            )

        console.print(f"  [green]✓ Merged and originals archived![/]")

# ── auto categorise notes ─────────────────────────────────────────────────────
def auto_categorise():
    from mcp_client import mcp_list_all_notes, mcp_create_note
    console.print("\n[dim]Fetching all notes...[/]")

    notes = mcp_list_all_notes(limit=100)
    if not notes:
        console.print("[yellow]No notes found.[/]")
        return

    notes_text = "\n".join([
        f"{i+1}. {n['title']}: {n['summary'][:100]}"
        for i, n in enumerate(notes)
    ])

    console.print("[dim]Asking Groq to categorise notes...[/]")

    response = groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""Categorise these notes into 3-6 meaningful categories.
Return ONLY JSON like this, nothing else:
{{"categories": [{{"name": "Category Name", "note_indices": [1, 3, 5], "summary": "brief description"}}]}}

Notes:
{notes_text}"""
        }]
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(raw)
        categories = data["categories"]
    except:
        console.print("[red]Could not parse categories.[/]")
        return

    today = datetime.now().strftime("%Y-%m-%d")

    table = Table(title="Auto-detected Categories", show_lines=True)
    table.add_column("Category", style="cyan", width=20)
    table.add_column("Notes", style="white", width=8)
    table.add_column("Summary", style="dim", width=40)

    for cat in categories:
        table.add_row(
            cat["name"],
            str(len(cat.get("note_indices", []))),
            cat.get("summary", "")
        )

    console.print(table)

    if Confirm.ask("\n[green]Save category summaries to Notion?[/]"):
        for cat in categories:
            note_indices = cat.get("note_indices", [])
            referenced = [
                notes[i - 1]["title"]
                for i in note_indices
                if 1 <= i <= len(notes)
            ]
            summary = (
                f"Category: {cat['name']}\n"
                f"Summary: {cat['summary']}\n\n"
                f"Notes in this category:\n" +
                "\n".join([f"- {t}" for t in referenced])
            )
            mcp_create_note(
                title=f"[Category] {cat['name']}",
                summary=summary,
                tags=["category", "auto-generated"],
                date=today
            )
            console.print(f"  [green]✓ Saved:[/] {cat['name']}")

        console.print(Panel(
            f"[bold green]✓ {len(categories)} categories saved to Notion![/]",
            title="Auto Categorise"
        ))

# ── organiser interactive menu ────────────────────────────────────────────────
def run_organiser():
    console.print(Panel(
        "[bold cyan]NotionMind Organiser[/]\n\n"
        "[dim]Options:\n"
        "  1. Auto-tag untagged notes\n"
        "  2. Find duplicate notes\n"
        "  3. Merge two notes manually\n"
        "  4. Auto-categorise all notes\n"
        "  5. Run all (full organise)\n"
        "  0. Back[/]",
        title="Organiser"
    ))

    choice = Prompt.ask("[green]Choose[/]", choices=["0", "1", "2", "3", "4", "5"])

    if choice == "1":
        auto_tag_notes()
    elif choice == "2":
        find_duplicates()
    elif choice == "3":
        merge_notes()
    elif choice == "4":
        auto_categorise()
    elif choice == "5":
        console.print("\n[bold cyan]Running full organise...[/]\n")
        auto_tag_notes()
        find_duplicates()
        auto_categorise()
    elif choice == "0":
        return

if __name__ == "__main__":
    run_organiser()
