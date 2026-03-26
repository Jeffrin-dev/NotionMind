import os
import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from dotenv import load_dotenv
from groq import Groq
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from rich.rule import Rule
from rich.padding import Padding
from rich.align import Align

load_dotenv()

groq = Groq(api_key=os.environ["GROQ_API_KEY"])
console = Console()

EXCLUDED_TAGS = ["auto-generated", "summary", "daily", "weekly-report", "category", "merged"]

# ── fetch and filter notes ────────────────────────────────────────────────────
def fetch_clean_notes(limit=200):
    from mcp_client import mcp_list_all_notes
    notes = mcp_list_all_notes(limit=limit)
    return [
        n for n in notes
        if not any(t in n.get("tags", []) for t in EXCLUDED_TAGS)
    ]

# ── todo lists ─────────────────────────────────────────────────────────────────
def render_todos():
    from todos import fetch_todos
    from datetime import datetime

    todos = fetch_todos()
    today = datetime.now().strftime("%Y-%m-%d")

    text = Text()
    text.append("\n")

    if not todos:
        text.append("  All caught up — no pending todos ✓\n", style="grey50")
    else:
        for t in todos[:6]:
            icon  = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(t["priority"], "🟡")
            color = {"high": "bright_red", "medium": "bright_yellow", "low": "bright_green"}.get(t["priority"], "white")
            text.append(f"  {icon}  ", style="white")
            text.append(f"{t['title'][:45]}", style=color)
            if t["due"]:
                if t["due"] < today:
                    text.append(f" (overdue)\n", style="bright_red")
                elif t["due"] == today:
                    text.append(f" (today)\n", style="bright_yellow")
                else:
                    text.append(f" (due {t['due']})\n", style="grey50")
            else:
                text.append("\n")

    return Panel(
        text,
        title=f"[bold cyan]✅  Todos ({len(todos)} pending)[/]",
        border_style="cyan",
        padding=(0, 1)
    )

# ── activity heatmap (last 30 days) ──────────────────────────────────────────
def render_heatmap(notes):
    today = datetime.now().date()
    counts = Counter()
    for n in notes:
        try:
            d = datetime.strptime(n["date"], "%Y-%m-%d").date()
            counts[d] += 1
        except Exception:
            pass

    # build 30-day grid — 6 rows of 5 days
    days = [(today - timedelta(days=i)) for i in range(29, -1, -1)]
    max_count = max(counts.values()) if counts else 1

    def heat_char(count):
        if count == 0:   return ("·", "grey30")
        if count == 1:   return ("▪", "cyan")
        if count == 2:   return ("▫", "bright_cyan")
        if count <= 4:   return ("▬", "green")
        return           ("█", "bright_green")

    # header
    text = Text()
    text.append("  Activity — last 30 days\n\n", style="bold white")

    # day labels
    text.append("  ")
    for i, day in enumerate(days):
        char, color = heat_char(counts.get(day, 0))
        text.append(char + " ", style=color)
        if (i + 1) % 10 == 0:
            text.append("\n  ")

    # legend
    text.append("\n\n  ")
    text.append("· ", style="grey30")
    text.append("none  ", style="grey50")
    text.append("▪ ", style="cyan")
    text.append("1  ", style="grey50")
    text.append("▫ ", style="bright_cyan")
    text.append("2  ", style="grey50")
    text.append("▬ ", style="green")
    text.append("3-4  ", style="grey50")
    text.append("█ ", style="bright_green")
    text.append("5+", style="grey50")

    return Panel(
        Padding(text, (1, 2)),
        title="[bold cyan]🗓  Brain Activity[/]",
        border_style="cyan",
        padding=(0, 1)
    )


# ── knowledge growth bar chart ────────────────────────────────────────────────
def render_growth(notes):
    today = datetime.now().date()
    daily = defaultdict(int)
    for n in notes:
        try:
            d = datetime.strptime(n["date"], "%Y-%m-%d").date()
            daily[d] += 1
        except Exception:
            pass

    # last 14 days
    days = [(today - timedelta(days=i)) for i in range(13, -1, -1)]
    max_val = max((daily.get(d, 0) for d in days), default=1)
    max_val = max(max_val, 1)

    BAR_WIDTH = 16
    COLORS = ["bright_cyan", "cyan", "bright_cyan", "green", "bright_green"]

    text = Text()
    text.append("  Notes saved per day — last 14 days\n\n", style="bold white")

    for i, day in enumerate(days):
        count = daily.get(day, 0)
        bar_len = int((count / max_val) * BAR_WIDTH)
        color = COLORS[min(count, len(COLORS) - 1)]

        label = day.strftime("%d %b")
        text.append(f"  {label}  ", style="grey70")
        if bar_len > 0:
            text.append("█" * bar_len, style=color)
        text.append(f"  {count}\n" if count > 0 else "  ·\n", style="grey50")

    return Panel(
        Padding(text, (1, 1)),
        title="[bold cyan]📈  Knowledge Growth[/]",
        border_style="cyan",
        padding=(0, 1)
    )


# ── topic velocity ────────────────────────────────────────────────────────────
def render_velocity(notes):
    today = datetime.now().date()
    week_start = today - timedelta(days=7)
    prev_start = today - timedelta(days=14)

    this_week = defaultdict(int)
    last_week = defaultdict(int)

    for n in notes:
        try:
            d = datetime.strptime(n["date"], "%Y-%m-%d").date()
            for tag in n.get("tags", []):
                if tag in EXCLUDED_TAGS:
                    continue
                if week_start <= d <= today:
                    this_week[tag] += 1
                elif prev_start <= d < week_start:
                    last_week[tag] += 1
        except Exception:
            pass

    # get all tags from this week, sort by count
    all_tags = sorted(this_week.keys(), key=lambda t: this_week[t], reverse=True)[:8]

    if not all_tags:
        return Panel(
            "[dim]No tag activity this week.[/]",
            title="[bold cyan]⚡  Topic Velocity[/]",
            border_style="cyan"
        )

    max_count = max(this_week.values()) if this_week else 1

    text = Text()
    text.append("  This week vs last week\n\n", style="bold white")

    for tag in all_tags:
        curr = this_week.get(tag, 0)
        prev = last_week.get(tag, 0)

        if curr > prev:
            trend = "↑"
            trend_style = "bright_green"
        elif curr < prev:
            trend = "↓"
            trend_style = "bright_red"
        else:
            trend = "→"
            trend_style = "grey50"

        bar_len = int((curr / max_count) * 12)
        bar = "█" * bar_len + "░" * (12 - bar_len)

        text.append(f"  {tag[:14]:<14}", style="white")
        text.append(f"  {bar}", style="cyan")
        text.append(f"  {curr:>2}", style="bright_white")
        text.append(f"  {trend}\n", style=trend_style)

    return Panel(
        Padding(text, (1, 1)),
        title="[bold cyan]⚡  Topic Velocity[/]",
        border_style="cyan",
        padding=(0, 1)
    )


# ── quick stats panel ─────────────────────────────────────────────────────────
def render_stats(notes):
    today = datetime.now().date()
    total = len(notes)

    # streak
    streak = 0
    for i in range(60):
        d = str(today - timedelta(days=i))
        if any(n["date"] == d for n in notes):
            streak += 1
        else:
            break

    # this week
    week_start = str(today - timedelta(days=7))
    this_week = sum(1 for n in notes if n["date"] >= week_start)

    # today
    today_count = sum(1 for n in notes if n["date"] == str(today))

    # top tag
    all_tags = []
    for n in notes:
        all_tags.extend([t for t in n.get("tags", []) if t not in EXCLUDED_TAGS])
    top_tag = Counter(all_tags).most_common(1)[0][0] if all_tags else "none"

    # avg per day (last 30)
    days_30 = defaultdict(int)
    for n in notes:
        try:
            d = datetime.strptime(n["date"], "%Y-%m-%d").date()
            if (today - d).days <= 30:
                days_30[d] += 1
        except Exception:
            pass
    avg = round(sum(days_30.values()) / 30, 1)

    text = Text()
    text.append("\n")

    def stat_row(icon, label, value, value_style="bright_cyan"):
        text.append(f"  {icon}  ", style="white")
        text.append(f"{label:<18}", style="grey70")
        text.append(f"{value}\n", style=value_style)

    stat_row("🗒 ", "Total notes", str(total))
    stat_row("📅", "Today", str(today_count), "bright_green" if today_count > 0 else "grey50")
    stat_row("📊", "This week", str(this_week))
    stat_row("🔥", "Streak", f"{streak} day{'s' if streak != 1 else ''}", "bright_yellow" if streak > 2 else "bright_cyan")
    stat_row("📈", "Avg / day (30d)", str(avg))
    stat_row("🏷 ", "Top tag", top_tag, "bright_magenta")

    return Panel(
        text,
        title="[bold cyan]📊  Quick Stats[/]",
        border_style="cyan",
        padding=(0, 1)
    )

# ── upcoming reminders panel ──────────────────────────────────────────────────
def render_reminders():
    from reminders import load_reminders
    from datetime import datetime

    reminders = load_reminders()
    today = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M")

    pending = [
        r for r in reminders
        if not r.get("done")
        and r.get("date", today) >= today
    ]

    # sort by date then time
    pending.sort(key=lambda r: (r.get("date", today), r.get("time", "00:00")))

    text = Text()
    text.append("\n")

    if not pending:
        text.append("  No upcoming reminders.\n", style="grey50")
    else:
        for r in pending[:5]:
            date = r.get("date", today)
            time = r.get("time", "--:--")
            msg = r["message"]
            repeat = r.get("repeat", "once")

            # highlight if today
            if date == today:
                date_style = "bright_yellow"
                date_label = "today"
            else:
                date_style = "grey70"
                date_label = date

            text.append(f"  ⏰  ", style="white")
            text.append(f"{date_label} {time}", style=date_style)
            text.append(f"  {msg[:45]}", style="white")
            if repeat == "daily":
                text.append("  ↻", style="grey50")
            text.append("\n")

    return Panel(
        text,
        title="[bold cyan]⏰  Upcoming Reminders[/]",
        border_style="cyan",
        padding=(0, 1)
    )


# ── main dashboard ────────────────────────────────────────────────────────────
def run_dashboard():
    console.print()
    console.print(
        Align.center(
            Text("◆  N O T I O N M I N D  B R A I N  D A S H B O A R D  ◆", style="bold bright_cyan")
        )
    )
    console.print(
        Align.center(
            Text(datetime.now().strftime("%A, %d %B %Y  ·  %H:%M"), style="grey50")
        )
    )
    console.print()

    console.print("[dim]Fetching notes...[/]")
    notes = fetch_clean_notes()

    if not notes:
        console.print("[yellow]No notes found.[/]")
        return

    # row 1 — heatmap + stats side by side
    heatmap = render_heatmap(notes)
    stats = render_stats(notes)
    console.print(Columns([heatmap, stats], equal=False, expand=True))

    console.print()

    # row 2 — growth + velocity side by side
    growth = render_growth(notes)
    velocity = render_velocity(notes)
    console.print(Columns([growth, velocity], equal=True, expand=True))

    console.print()

    # row 3 — reminders + todos side by side
    console.print(Columns([render_reminders(), render_todos()], equal=True, expand=True))

    console.print()
    console.print(
        Align.center(
            Text("── run  graph → insights  for AI-powered personal insights ──", style="grey50")
        )
    )
    console.print()


# ── insights: AI-powered analysis ────────────────────────────────────────────
def run_insights():
    console.print()
    console.print(
        Align.center(
            Text("◆  A I   I N S I G H T S  ◆", style="bold bright_magenta")
        )
    )
    console.print(
        Align.center(
            Text("Groq analyses your notes and surfaces what matters", style="grey50")
        )
    )
    console.print()

    console.print("[dim]Fetching notes for analysis...[/]")
    notes = fetch_clean_notes(limit=100)

    if not notes:
        console.print("[yellow]No notes found.[/]")
        return

    today = datetime.now()

    # build rich context for Groq
    notes_by_date = sorted(notes, key=lambda n: n["date"])
    context = "\n".join([
        f"[{n['date']}] {n['title']} [tags: {', '.join(n.get('tags', [])) or 'none'}]: {n['summary'][:200]}"
        for n in notes_by_date
    ])

    # tag frequency by week
    weekly_tags = defaultdict(Counter)
    for n in notes:
        try:
            d = datetime.strptime(n["date"], "%Y-%m-%d")
            week = d.strftime("%Y-W%W")
            for tag in n.get("tags", []):
                if tag not in EXCLUDED_TAGS:
                    weekly_tags[week][tag] += 1
        except Exception:
            pass

    tag_summary = "\n".join([
        f"Week {w}: " + ", ".join([f"{t}({c})" for t, c in tags.most_common(5)])
        for w, tags in sorted(weekly_tags.items())[-4:]
    ])

    console.print("[dim]Running AI analysis...[/]\n")

    response = groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a personal knowledge analyst. Analyse the user's notes and generate sharp, specific insights. "
                    "Be direct and specific — reference actual note titles and dates. "
                    "Never be generic. Every insight must be grounded in the actual notes provided."
                )
            },
            {
                "role": "user",
                "content": f"""Analyse my notes and give me exactly these 4 sections:

1. PEAK PRODUCTIVITY
When am I most productive? Look at dates with most notes. Be specific about days/periods.

2. KNOWLEDGE GAPS  
What topics am I avoiding or underexploring? What's missing given what I'm working on?

3. FADING TOPICS
What topics did I explore before but have drifted away from recently?

4. ONE SHARP RECOMMENDATION
One specific, actionable thing I should do this week based on my note patterns.

Keep each section to 2-3 sentences max. Be brutally specific.

My notes:
{context}

Weekly tag activity:
{tag_summary}

Today: {today.strftime('%Y-%m-%d')}"""
            }
        ],
        max_tokens=700
    )

    raw = response.choices[0].message.content.strip()

    # parse and render each section beautifully
    sections = {
        "PEAK PRODUCTIVITY": ("🔥", "bright_yellow", "Peak Productivity"),
        "KNOWLEDGE GAPS":    ("🕳 ", "bright_red",    "Knowledge Gaps"),
        "FADING TOPICS":     ("📉", "bright_blue",   "Fading Topics"),
        "ONE SHARP RECOMMENDATION": ("⚡", "bright_green", "This Week's Action"),
    }

    current_section = None
    current_lines = []
    parsed = {}

    # strip markdown bold markers before parsing
    clean_raw = raw.replace("**", "")

    for line in clean_raw.split("\n"):
        stripped = line.strip()
        matched = False
        for key in sections:
            if key in stripped.upper():
                if current_section and current_lines:
                    parsed[current_section] = " ".join(current_lines).strip()
                current_section = key
                current_lines = []
                matched = True
                break
        if not matched and current_section and stripped:
            # strip leading numbers, dots, dashes
            clean = stripped.lstrip("1234567890.-) ").strip()
            if clean:
                current_lines.append(clean)

    if current_section and current_lines:
        parsed[current_section] = " ".join(current_lines).strip()

    # render each insight as a styled panel
    for key, (icon, color, title) in sections.items():
        content = parsed.get(key, "")
        if not content:
            continue

        text = Text()
        text.append(f"\n  {content}\n", style="white")

        console.print(Panel(
            text,
            title=f"[bold {color}]{icon}  {title}[/]",
            border_style=color,
            padding=(0, 2)
        ))
        console.print()
    
    # fallback — if nothing parsed, print raw response
    if not parsed:
        console.print(Panel(
            f"[bold white]{raw}[/]",
            title="[bold bright_magenta]◆  AI Insights[/]",
            border_style="bright_magenta",
            padding=(1, 2)
        ))
    
    console.print(
        Align.center(
            Text(f"── analysed {len(notes)} notes ──", style="grey50")
        )
    )
    console.print()
