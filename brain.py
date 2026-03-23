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

# add this at the top of brain.py with other globals
_embed_model = None

def _get_embed_model():
    global _embed_model
    if _embed_model is None:
        from fastembed import TextEmbedding
        _embed_model = TextEmbedding("BAAI/bge-small-en-v1.5")
    return _embed_model

_notes_cache = None

def _get_notes():
    global _notes_cache
    if _notes_cache is None:
        from mcp_client import mcp_list_all_notes, mcp_read_page
        notes = mcp_list_all_notes(limit=100)
        notes = [
            n for n in notes
            if not any(t in n.get("tags", [])
                       for t in ["auto-generated", "summary", "daily",
                                 "weekly-report", "category", "merged"])
        ]
        console.print("[dim]Fetching full note content...[/]")
        for n in notes:
            page_content = mcp_read_page(n["id"])
            if page_content and page_content != "No content blocks found in this page.":
                n["_full_text"] = f"{n['title']}. {n['summary'][:200]} {page_content[:600]}"
            else:
                n["_full_text"] = f"{n['title']}. {n['summary'][:400]}"
        _notes_cache = notes
    return _notes_cache

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
    """Called after saving a note — suggests existing related notes."""
    # invalidate cache so new note is excluded cleanly
    global _notes_cache
    _notes_cache = None

    query = f"{new_note.get('title', '')} {new_note.get('summary', '')[:200]}"
    results = semantic_search(query, top_k=5)

    # filter out the note itself and auto-generated notes
    suggestions = [
        note for note, score in results
        if note["title"] != new_note.get("title")
        and not any(t in note.get("tags", [])
                    for t in ["auto-generated", "summary", "daily",
                              "weekly-report", "category", "merged"])
    ]
    return suggestions[:3]
        
# ── semantic search ───────────────────────────────────────────────────────────
def semantic_search(query: str, top_k: int = 5) -> list:
    import numpy as np

    notes = _get_notes()
    if not notes:
        return []

    model = _get_embed_model()
    texts = [n["_full_text"] for n in notes]

    query_vec = np.array(list(model.embed([query]))[0])
    note_vecs = np.array(list(model.embed(texts)))

    q_norm = query_vec / (np.linalg.norm(query_vec) + 1e-9)
    n_norms = note_vecs / (np.linalg.norm(note_vecs, axis=1, keepdims=True) + 1e-9)
    scores = n_norms @ q_norm

    top_idx = scores.argsort()[::-1][:top_k]

    results = [
        (notes[i], float(scores[i]))
        for i in top_idx
        if scores[i] >= 0.55
    ]
    return results
 
def run_semantic_search():
    """Interactive semantic search — find notes by meaning, not just keywords."""
    console.print(Panel(
        "[bold cyan]Semantic Search[/]\n"
        "[dim]Search your notes by meaning — no exact keywords needed.\n"
        "Type a concept, question, or phrase.[/]",
        title="🔍 Search"
    ))
 
    query = Prompt.ask("[green]What are you looking for[/]")
 
    console.print("[dim]Encoding query and searching...[/]")
    results = semantic_search(query, top_k=10)
 
    if not results:
        console.print("[yellow]No notes found.[/]")
        return
 
    table = Table(title=f'Semantic search: "{query}"', show_lines=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Match", style="cyan", width=14)
    table.add_column("Title", style="white", width=42, overflow="fold")
    table.add_column("Date", style="dim", width=12)
 
    for i, (note, score) in enumerate(results, 1):
        bar = "█" * int(score * 5) + "░" * (5 - int(score * 5))
        table.add_row(str(i), f"{bar} {score:.2f}", note["title"], note["date"])
 
    console.print(table)
 
    idx = Prompt.ask("[green]Enter number to read (or 0 to skip)[/]", default="0")
    if idx == "0" or not idx.isdigit():
        return
 
    idx = int(idx)
    if 1 <= idx <= len(results):
        note, score = results[idx - 1]
        console.print(Panel(
            f"[bold white]{note['summary']}[/]",
            title=f"[bold]{note['title']}[/] — {note['date']}"
        ))
 
# ── think: multi-hop reasoning ────────────────────────────────────────────────
def think():
    console.print(Panel(
        "[bold cyan]Think[/]\n"
        "[dim]Ask a complex question.\n"
        "I'll find relevant notes and trace connections one hop further\n"
        "in your knowledge graph to give you a richer answer.[/]",
        title="🧠 Think"
    ))

    question = Prompt.ask("[green]Your question[/]")

    console.print("[dim]Finding relevant notes...[/]")

    # extract keywords and search separately for better recall
    keywords_response = groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{
            "role": "user",
            "content": f"""Extract 2-4 key search terms from this question. 
Return ONLY a JSON array of strings, nothing else.
Example: ["cricket", "notionmind"]

Question: {question}"""
        }],
        max_tokens=40
    )

    try:
        raw = keywords_response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        keywords = json.loads(raw)
    except Exception:
        keywords = [question]

    # search for each keyword separately and merge results
    seen_ids = set()
    top_notes = []
    for keyword in keywords:
        results = semantic_search(keyword, top_k=4)
        for note, score in results:
            if note["id"] not in seen_ids:
                seen_ids.add(note["id"])
                top_notes.append(note)

    if not top_notes:
        console.print("[yellow]No relevant notes found.[/]")
        return

    seed_ids = {n["id"] for n in top_notes}

    # one-hop expansion via knowledge graph
    graph = load_graph()
    edges = graph.get("edges", [])
    nodes = graph.get("nodes", {})

    hop_ids = set()
    hop_reasons = {}

    for edge in edges:
        if edge["from"] in seed_ids and edge["to"] not in seed_ids:
            hop_ids.add(edge["to"])
            hop_reasons[edge["to"]] = edge["reason"]
        elif edge["to"] in seed_ids and edge["from"] not in seed_ids:
            hop_ids.add(edge["from"])
            hop_reasons[edge["from"]] = edge["reason"]

    hop_notes = []
    if hop_ids:
        from mcp_client import mcp_list_all_notes
        all_notes = mcp_list_all_notes(limit=100)
        all_notes_map = {n["id"]: n for n in all_notes}
        hop_notes = [
            all_notes_map[nid]
            for nid in hop_ids
            if nid in all_notes_map
        ][:4]

    # build context
    context_parts = []
    context_parts.append("=== DIRECTLY RELEVANT NOTES ===")
    for note in top_notes:
        context_parts.append(
            f"[{note['date']}] \"{note['title']}\"\n{note['summary'][:400]}"
        )

    if hop_notes:
        context_parts.append("\n=== CONNECTED NOTES (one graph hop away) ===")
        for note in hop_notes:
            reason = hop_reasons.get(note["id"], "related topic")
            context_parts.append(
                f"[{note['date']}] \"{note['title']}\"\n"
                f"Connected because: {reason}\n"
                f"{note['summary'][:300]}"
            )

    connection_lines = []
    for edge in edges:
        n1_id, n2_id = edge["from"], edge["to"]
        if n1_id in seed_ids or n2_id in seed_ids:
            t1 = nodes.get(n1_id, {}).get("title", "?")
            t2 = nodes.get(n2_id, {}).get("title", "?")
            connection_lines.append(f'"{t1}" ↔ "{t2}": {edge["reason"]}')

    if connection_lines:
        context_parts.append("\n=== KNOWN KNOWLEDGE CONNECTIONS ===")
        context_parts.extend(connection_lines[:12])

    full_context = "\n\n".join(context_parts)

    console.print(
        f"[dim]Reasoning across {len(top_notes)} relevant + "
        f"{len(hop_notes)} connected note(s)...[/]"
    )

    response = groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a personal AI assistant. Answer the question using ONLY the notes provided in the context. "
                    "NEVER invent or assume note titles that are not shown. "
                    "NEVER reference notes that don't appear in the context. "
                    "Only cite notes by their exact title as shown. "
                    "If the context doesn't contain enough to answer, say so honestly.\n"
                    f"Today: {datetime.now().strftime('%Y-%m-%d')}"
                )
            },
            {
                "role": "user",
                "content": f"Question: {question}\n\nContext:\n{full_context}"
            }
        ],
        max_tokens=900
    )

    answer = response.choices[0].message.content.strip()

    console.print(Panel(
        f"[bold white]{answer}[/]",
        title="[bold cyan]🧠 Reasoning Result[/]"
    ))

    note_titles = [f"  • {n['title']}" for n in top_notes]
    if hop_notes:
        note_titles += [f"  • {n['title']} (connected)" for n in hop_notes]
    console.print("\n[dim]Sources used:\n" + "\n".join(note_titles) + "[/]")
 
# ── recall: knowledge evolution ───────────────────────────────────────────────
def recall():
    """
    Show how your understanding of a topic evolved over time.
    Finds semantically relevant notes, sorts chronologically,
    asks Groq to narrate the evolution of your thinking.
    """
    console.print(Panel(
        "[bold cyan]Recall[/]\n"
        "[dim]Pick a topic and see how your understanding evolved\n"
        "over time, based on what you saved in your notes.[/]",
        title="🧠 Recall"
    ))
 
    topic = Prompt.ask("[green]Topic to recall[/]")
 
    console.print("[dim]Searching for notes on this topic...[/]")
    results = semantic_search(topic, top_k=12)
 
    if not results:
        console.print("[yellow]No notes found.[/]")
        return
 
    # filter to meaningfully relevant notes
    relevant = [(n, s) for n, s in results if s >= 0.28]
 
    if not relevant:
        console.print(
            f"[yellow]No strongly relevant notes found for '{topic}'.\n"
            f"Top result was '{results[0][0]['title']}' ({results[0][1]:.2f} relevance).[/]"
        )
        return
 
    # sort chronologically
    relevant.sort(key=lambda x: x[0]["date"])
 
    # show timeline table
    table = Table(
        title=f"Your notes on '{topic}' — chronological",
        show_lines=True
    )
    table.add_column("Date", style="cyan", width=12)
    table.add_column("Title", style="white", width=42, overflow="fold")
    table.add_column("Relevance", style="dim", width=14)
 
    for note, score in relevant:
        bar = "█" * int(score * 5) + "░" * (5 - int(score * 5))
        table.add_row(note["date"], note["title"], f"{bar} {score:.2f}")
 
    console.print(table)
    console.print(f"\n[green]{len(relevant)} note(s) found on this topic[/]\n")
 
    # build chronological context
    timeline = "\n\n".join([
        f"[{n['date']}] {n['title']}:\n{n['summary'][:350]}"
        for n, _ in relevant
    ])
 
    console.print("[dim]Analysing knowledge evolution...[/]")
 
    response = groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a personal knowledge assistant. "
                    "Analyse the user's notes chronologically to show how their understanding of a topic evolved. "
                    "Look for a narrative arc: initial curiosity → experiments/questions → insights → current depth. "
                    "Be specific — reference actual note titles and dates. "
                    "If there's only one note, describe what was captured and suggest 2-3 natural next questions to explore. "
                    "End with one sentence on where this topic seems headed based on the trajectory."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Topic: {topic}\n\n"
                    f"My notes on this topic, chronologically:\n\n{timeline}"
                )
            }
        ],
        max_tokens=700
    )
 
    evolution = response.choices[0].message.content.strip()
 
    console.print(Panel(
        f"[bold white]{evolution}[/]",
        title=f"[bold cyan]🧠 Knowledge Evolution: {topic}[/]"
    ))
 

# ── graph interactive menu ────────────────────────────────────────────────────
def run_graph():
    console.print(Panel(
        "[bold cyan]NotionMind Knowledge Graph[/]\n\n"
        "[dim]Options:\n"
        "  1. Build graph   — analyse all notes, find connections\n"
        "  2. View graph    — ASCII visualisation of your knowledge\n"
        "  3. Relate        — manually link two notes\n"
        "  4. Neighbours    — show all connections of a note\n"
        "  5. Path          — find connection between two notes\n"
        "  6. Strongest     — top connections in your brain\n"
        "  ─────────────────── Part 2: AI Memory ──────────────────\n"
        "  7. Search        — semantic search by meaning (not keyword)\n"
        "  8. Think         — multi-hop reasoning across your notes\n"
        "  9. Recall        — how your understanding of a topic evolved\n"
        "  0. Back[/]",
        title="🧠 Brain"
    ))
 
    choice = Prompt.ask(
        "[green]Choose[/]",
        choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    )
 
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
    elif choice == "7":
        run_semantic_search()
    elif choice == "8":
        think()
    elif choice == "9":
        recall()
    elif choice == "0":
        return
 

if __name__ == "__main__":
    run_graph()
