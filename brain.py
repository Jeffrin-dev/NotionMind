import os
import json
import time
from datetime import datetime
from itertools import combinations
from dotenv import load_dotenv
from groq import Groq
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.progress import track

load_dotenv()

groq = Groq(api_key=os.environ["GROQ_API_KEY"])
console = Console()

GRAPH_FILE = os.path.expanduser("~/.notionmind_graph.json")

# ── load graph ────────────────────────────────────────────────────────────────
def load_graph() -> dict:
    if not os.path.exists(GRAPH_FILE):
        return {"nodes": {}, "edges": [], "built_at": None}
    with open(GRAPH_FILE, "r") as f:
        return json.load(f)

# ── save graph ────────────────────────────────────────────────────────────────
def save_graph(graph: dict):
    with open(GRAPH_FILE, "w") as f:
        json.dump(graph, f, indent=2)

# ── check relation between two notes ─────────────────────────────────────────
def check_relation(note1: dict, note2: dict) -> dict:
    """Ask Groq if two notes are related. Uses fast 8b model to save tokens."""
    try:
        response = groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": f"""Are these two notes genuinely related in CONTENT — same topic, same concept, same technology, or one directly references the other?

DO NOT relate notes just because:
- They were created around the same time
- They are both part of the same app or project
- They are both productivity-related

Only return related: true if they share actual subject matter.

Return ONLY JSON, nothing else:
{{"related": true/false, "strength": 0.1-1.0, "reason": "one sentence about shared content"}}

Note 1: {note1['title']} — {note1['summary'][:150]}
Note 2: {note2['title']} — {note2['summary'][:150]}"""
            }],
            max_tokens=100
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        return {
            "related": bool(data.get("related", False)),
            "strength": float(data.get("strength", 0.0)),
            "reason": str(data.get("reason", ""))
        }
    except:
        return {"related": False, "strength": 0.0, "reason": ""}

# ── build knowledge graph ─────────────────────────────────────────────────────
def build_graph():
    from mcp_client import mcp_list_all_notes

    console.print(Panel(
        "[bold cyan]Building Knowledge Graph[/]\n"
        "[dim]This analyses all your notes and finds connections.\n"
        "Uses Groq free tier — may take a few minutes for large note sets.[/]",
        title="🧠 Brain"
    ))

    notes = mcp_list_all_notes(limit=100)

    # filter out auto-generated notes
    notes = [
        n for n in notes
        if not any(t in n.get("tags", [])
                   for t in ["auto-generated", "summary", "category", "weekly-report"])
    ]

    console.print(f"[green]Analysing {len(notes)} notes...[/]")

    graph = load_graph()

    # update nodes
    graph["nodes"] = {
        n["id"]: {
            "title": n["title"],
            "tags": n.get("tags", []),
            "date": n["date"]
        }
        for n in notes
    }

    # get existing edge pairs to avoid re-checking
    existing_pairs = set(
        (e["from"], e["to"]) for e in graph.get("edges", [])
    )

    # generate all pairs
    all_pairs = list(combinations(notes, 2))
    new_pairs = [
        (n1, n2) for n1, n2 in all_pairs
        if (n1["id"], n2["id"]) not in existing_pairs
        and (n2["id"], n1["id"]) not in existing_pairs
    ]

    if not new_pairs:
        console.print("[yellow]Graph is already up to date![/]")
        return graph

    console.print(f"[dim]Checking {len(new_pairs)} new note pairs...[/]\n")

    new_edges = 0
    for n1, n2 in track(new_pairs, description="Analysing..."):
        result = check_relation(n1, n2)
        if result.get("related") and result.get("strength", 0) >= 0.5:
            graph["edges"].append({
                "from": n1["id"],
                "to": n2["id"],
                "reason": result.get("reason", ""),
                "strength": result.get("strength", 0.5)
            })
            new_edges += 1
        # small delay to respect rate limits
        time.sleep(0.2)

    graph["built_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_graph(graph)

    console.print(Panel(
        f"[bold green]✓ Knowledge Graph Built![/]\n\n"
        f"[cyan]Notes analysed:[/]  {len(notes)}\n"
        f"[cyan]Pairs checked:[/]   {len(new_pairs)}\n"
        f"[cyan]New connections:[/] {new_edges}\n"
        f"[cyan]Total edges:[/]     {len(graph['edges'])}\n"
        f"[cyan]Built at:[/]        {graph['built_at']}",
        title="🧠 Graph Built"
    ))

    return graph

# ── ascii graph view ──────────────────────────────────────────────────────────
def view_graph():
    graph = load_graph()

    if not graph["nodes"]:
        console.print("[yellow]No graph found. Run 'graph build' first![/]")
        return

    edges = graph["edges"]
    nodes = graph["nodes"]

    if not edges:
        console.print("[yellow]No connections found yet. Try adding more notes![/]")
        return

    # sort edges by strength
    edges_sorted = sorted(edges, key=lambda e: e["strength"], reverse=True)

    # build adjacency for display
    adjacency = {}
    for e in edges_sorted:
        n1 = e["from"]
        n2 = e["to"]
        if n1 not in adjacency:
            adjacency[n1] = []
        if n2 not in adjacency:
            adjacency[n2] = []
        adjacency[n1].append((n2, e["strength"], e["reason"]))
        adjacency[n2].append((n1, e["strength"], e["reason"]))

    # find most connected node as root
    root = max(adjacency, key=lambda n: len(adjacency[n]))

    console.print(Panel(
        f"[bold cyan]Knowledge Graph[/]\n"
        f"[dim]{len(nodes)} notes · {len(edges)} connections[/]",
        title="🧠 Brain"
    ))

    # ASCII tree from root
    root_title = nodes[root]["title"] if root in nodes else "Unknown"
    console.print(f"\n[bold cyan]  [{root_title}][/]")

    seen = {root}
    root_connections = sorted(
        adjacency.get(root, []),
        key=lambda x: x[1],
        reverse=True
    )[:8]

    for i, (nid, strength, reason) in enumerate(root_connections):
        is_last = i == len(root_connections) - 1
        prefix = "  └──" if is_last else "  ├──"
        title = nodes[nid]["title"] if nid in nodes else "Unknown"
        bar = "█" * int(strength * 5) + "░" * (5 - int(strength * 5))
        console.print(
            f"[dim]{prefix}[/] [white]{title}[/] "
            f"[dim]{bar} {strength:.2f}[/]"
        )

        if nid not in seen:
            seen.add(nid)
            sub_connections = sorted(
                adjacency.get(nid, []),
                key=lambda x: x[1],
                reverse=True
            )
            sub_connections = [
                s for s in sub_connections
                if s[0] not in seen
            ][:3]

            for j, (snid, sstrength, sreason) in enumerate(sub_connections):
                is_sub_last = j == len(sub_connections) - 1
                sub_prefix = "       └──" if is_sub_last else "       ├──"
                stitle = nodes[snid]["title"] if snid in nodes else "Unknown"
                console.print(
                    f"[dim]{sub_prefix}[/] [dim]{stitle}[/] "
                    f"[dim]{sstrength:.2f}[/]"
                )
                seen.add(snid)

    # top connections table
    console.print(f"\n[bold cyan]Top Connections:[/]\n")

    table = Table(show_lines=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Note 1", style="white", width=40, overflow="fold")
    table.add_column("Note 2", style="white", width=40, overflow="fold")
    table.add_column("Strength", style="cyan", width=12)

    for i, e in enumerate(edges_sorted[:10], 1):
        n1_title = nodes.get(e["from"], {}).get("title", "?")
        n2_title = nodes.get(e["to"], {}).get("title", "?")
        bar = "█" * int(e["strength"] * 5) + "░" * (5 - int(e["strength"] * 5))
        table.add_row(str(i), n1_title, n2_title, f"{bar} {e['strength']:.2f}")

    console.print(table)

    # reasons below table
    console.print("\n[bold cyan]Connection Reasons:[/]\n")
    for i, e in enumerate(edges_sorted[:10], 1):
        n1 = nodes.get(e["from"], {}).get("title", "?")
        n2 = nodes.get(e["to"], {}).get("title", "?")
        console.print(f"[cyan]{i}.[/] [white]{n1}[/] ↔ [white]{n2}[/]")
        console.print(f"   [dim]{e['reason']}[/]\n")

# ── manually relate two notes ─────────────────────────────────────────────────
def relate_notes():
    from mcp_client import mcp_list_all_notes

    notes = mcp_list_all_notes(limit=50)
    notes = [
        n for n in notes
        if not any(t in n.get("tags", [])
                   for t in ["auto-generated", "summary", "category"])
    ]

    table = Table(title="Select notes to relate", show_lines=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Date", style="white", width=12)
    table.add_column("Title", style="white", width=55, overflow="fold")

    for i, n in enumerate(notes, 1):
        table.add_row(str(i), n["date"], n["title"])

    console.print(table)

    idx1 = Prompt.ask("[green]First note number[/]")
    idx2 = Prompt.ask("[green]Second note number[/]")

    if not (idx1.isdigit() and idx2.isdigit()):
        console.print("[red]Invalid input.[/]")
        return

    n1 = notes[int(idx1) - 1]
    n2 = notes[int(idx2) - 1]

    reason = Prompt.ask("[green]Why are these related[/]")
    strength = Prompt.ask("[green]Strength (0.1 - 1.0)[/]", default="0.8")

    try:
        strength = float(strength)
        strength = max(0.1, min(1.0, strength))
    except:
        strength = 0.8

    graph = load_graph()

    # remove existing edge if any
    graph["edges"] = [
        e for e in graph["edges"]
        if not (
            (e["from"] == n1["id"] and e["to"] == n2["id"]) or
            (e["from"] == n2["id"] and e["to"] == n1["id"])
        )
    ]

    graph["edges"].append({
        "from": n1["id"],
        "to": n2["id"],
        "reason": reason,
        "strength": strength
    })

    save_graph(graph)

    console.print(Panel(
        f"[bold green]✓ Notes linked![/]\n\n"
        f"[cyan]Note 1:[/]   {n1['title']}\n"
        f"[cyan]Note 2:[/]   {n2['title']}\n"
        f"[cyan]Reason:[/]   {reason}\n"
        f"[cyan]Strength:[/] {strength}",
        title="🧠 Relation Added"
    ))

# ── show neighbours of a note ─────────────────────────────────────────────────
def show_neighbours():
    graph = load_graph()

    if not graph["nodes"]:
        console.print("[yellow]No graph found. Run 'graph build' first![/]")
        return

    nodes = graph["nodes"]
    edges = graph["edges"]
    node_list = list(nodes.items())

    table = Table(title="Select a note", show_lines=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Title", style="white", width=55, overflow="fold")
    table.add_column("Connections", style="cyan", width=12)

    for i, (nid, node) in enumerate(node_list, 1):
        conn_count = sum(
            1 for e in edges
            if e["from"] == nid or e["to"] == nid
        )
        table.add_row(str(i), node["title"], str(conn_count))

    console.print(table)

    idx = Prompt.ask("[green]Enter number[/]")
    if not idx.isdigit() or not (1 <= int(idx) <= len(node_list)):
        console.print("[red]Invalid number.[/]")
        return

    nid, node = node_list[int(idx) - 1]

    neighbours = []
    for e in edges:
        if e["from"] == nid:
            neighbours.append((e["to"], e["strength"], e["reason"]))
        elif e["to"] == nid:
            neighbours.append((e["from"], e["strength"], e["reason"]))

    if not neighbours:
        console.print(f"[yellow]No connections found for '{node['title']}'[/]")
        return

    neighbours_sorted = sorted(neighbours, key=lambda x: x[1], reverse=True)

    console.print(Panel(
        f"[bold cyan]{node['title']}[/]\n"
        f"[dim]{len(neighbours)} connection(s)[/]",
        title="🧠 Neighbours"
    ))

    table = Table(show_lines=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Connected Note", style="white", width=55, overflow="fold")
    table.add_column("Strength", style="cyan", width=12)

    for i, (nbr_id, strength, reason) in enumerate(neighbours_sorted, 1):
        nbr_title = nodes.get(nbr_id, {}).get("title", "Unknown")
        bar = "█" * int(strength * 5) + "░" * (5 - int(strength * 5))
        table.add_row(str(i), nbr_title, f"{bar} {strength:.2f}")

    console.print(table)

    # reasons below table
    console.print("\n[bold cyan]Connection Reasons:[/]\n")
    for i, (nbr_id, strength, reason) in enumerate(neighbours_sorted, 1):
        nbr_title = nodes.get(nbr_id, {}).get("title", "Unknown")
        console.print(f"[cyan]{i}.[/] [white]{nbr_title}[/]")
        console.print(f"   [dim]{reason}[/]\n")

# ── find path between two notes ───────────────────────────────────────────────
def find_path():
    graph = load_graph()

    if not graph["nodes"]:
        console.print("[yellow]No graph found. Run 'graph build' first![/]")
        return

    nodes = graph["nodes"]
    edges = graph["edges"]
    node_list = list(nodes.items())

    table = Table(title="Select notes", show_lines=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Title", style="white", width=55, overflow="fold")

    for i, (nid, node) in enumerate(node_list, 1):
        table.add_row(str(i), node["title"])

    console.print(table)

    idx1 = Prompt.ask("[green]Start note number[/]")
    idx2 = Prompt.ask("[green]End note number[/]")

    if not (idx1.isdigit() and idx2.isdigit()):
        console.print("[red]Invalid input.[/]")
        return

    start_id = node_list[int(idx1) - 1][0]
    end_id = node_list[int(idx2) - 1][0]

    if start_id == end_id:
        console.print("[yellow]Same note selected![/]")
        return

    # BFS to find shortest path
    from collections import deque

    adjacency = {}
    for e in edges:
        if e["from"] not in adjacency:
            adjacency[e["from"]] = []
        if e["to"] not in adjacency:
            adjacency[e["to"]] = []
        adjacency[e["from"]].append(e["to"])
        adjacency[e["to"]].append(e["from"])

    queue = deque([[start_id]])
    visited = {start_id}

    path = None
    while queue:
        current_path = queue.popleft()
        current = current_path[-1]

        if current == end_id:
            path = current_path
            break

        for neighbour in adjacency.get(current, []):
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append(current_path + [neighbour])

    if not path:
        console.print(Panel(
            f"[yellow]No connection path found between these notes.[/]\n"
            f"[dim]Try building the graph first or adding more notes.[/]",
            title="🧠 Path"
        ))
        return

    console.print(Panel(
        f"[bold green]Path found! {len(path)} hop(s)[/]",
        title="🧠 Connection Path"
    ))

    for i, nid in enumerate(path):
        title = nodes.get(nid, {}).get("title", "Unknown")
        if i == 0:
            console.print(f"  [bold cyan]START → {title}[/]")
        elif i == len(path) - 1:
            console.print(f"  [bold green]  END → {title}[/]")
        else:
            console.print(f"  [dim]       → {title}[/]")

        if i < len(path) - 1:
            next_id = path[i + 1]
            for e in edges:
                if (e["from"] == nid and e["to"] == next_id) or \
                   (e["from"] == next_id and e["to"] == nid):
                    console.print(f"  [dim]         ↕ {e['reason']}[/]")
                    break

# ── strongest connections ─────────────────────────────────────────────────────
def show_strongest():
    graph = load_graph()

    if not graph["edges"]:
        console.print("[yellow]No connections found. Run 'graph build' first![/]")
        return

    nodes = graph["nodes"]
    edges = sorted(graph["edges"], key=lambda e: e["strength"], reverse=True)

    console.print(Panel(
        f"[bold cyan]Strongest Connections in Your Brain[/]\n"
        f"[dim]Top {min(15, len(edges))} connections by strength[/]",
        title="🧠 Strongest"
    ))

    table = Table(show_lines=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Note 1", style="white", width=40, overflow="fold")
    table.add_column("Note 2", style="white", width=40, overflow="fold")
    table.add_column("Strength", style="cyan", width=12)

    for i, e in enumerate(edges[:15], 1):
        n1 = nodes.get(e["from"], {}).get("title", "?")
        n2 = nodes.get(e["to"], {}).get("title", "?")
        bar = "█" * int(e["strength"] * 5) + "░" * (5 - int(e["strength"] * 5))
        table.add_row(str(i), n1, n2, f"{bar} {e['strength']:.2f}")

    console.print(table)

    # reasons below table
    console.print("\n[bold cyan]Connection Reasons:[/]\n")
    for i, e in enumerate(edges[:15], 1):
        n1 = nodes.get(e["from"], {}).get("title", "?")
        n2 = nodes.get(e["to"], {}).get("title", "?")
        console.print(f"[cyan]{i}.[/] [white]{n1}[/] ↔ [white]{n2}[/]")
        console.print(f"   [dim]{e['reason']}[/]\n")

# ── suggest related notes when saving ────────────────────────────────────────
def suggest_related(new_note: dict) -> list:
    """Called after saving a note — suggests existing related notes"""
    graph = load_graph()
    if not graph["nodes"]:
        return []

    from mcp_client import mcp_list_all_notes
    notes = mcp_list_all_notes(limit=50)
    notes = [n for n in notes if n["id"] != new_note.get("id")][:20]

    if not notes:
        return []

    notes_text = "\n".join([
        f"{i+1}. {n['title']}: {n['summary'][:100]}"
        for i, n in enumerate(notes)
    ])

    try:
        response = groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": f"""Given this new note, which existing notes are most related?
Return ONLY JSON array of indices (max 3), nothing else: [1, 4, 7]
If none are related return: []

New note: {new_note.get('title', '')} — {new_note.get('summary', '')[:200]}

Existing notes:
{notes_text}"""
            }],
            max_tokens=50
        )

        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        indices = json.loads(raw)
        return [notes[i - 1] for i in indices if 1 <= i <= len(notes)]
    except:
        return []

# ── graph interactive menu ────────────────────────────────────────────────────
def run_graph():
    console.print(Panel(
        "[bold cyan]NotionMind Knowledge Graph[/]\n\n"
        "[dim]Options:\n"
        "  1. Build graph — analyse all notes and find connections\n"
        "  2. View graph — ASCII visualisation of your knowledge\n"
        "  3. Relate — manually link two notes\n"
        "  4. Neighbours — show all connections of a note\n"
        "  5. Path — find connection between two notes\n"
        "  6. Strongest — show top connections in your brain\n"
        "  0. Back[/]",
        title="🧠 Brain"
    ))

    choice = Prompt.ask("[green]Choose[/]", choices=["0", "1", "2", "3", "4", "5", "6"])

    if choice == "1":
        build_graph()
    elif choice == "2":
        view_graph()
    elif choice == "3":
        relate_notes()
    elif choice == "4":
        show_neighbours()
    elif choice == "5":
        find_path()
    elif choice == "6":
        show_strongest()
    elif choice == "0":
        return

if __name__ == "__main__":
    run_graph()
