import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from notionmind import (
    save_note,
    ask_question,
    fetch_notes,
    add_inbox_task
)

load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# ── helpers ───────────────────────────────────────────────────────────────────
def get_today_text() -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    notes = fetch_notes(limit=50)
    todays = [n for n in notes if n["date"] == today]
    if not todays:
        return f"No notes yet for today ({today})."
    lines = [f"📅 *Today's Notes — {today}*\n"]
    for i, n in enumerate(todays, 1):
        tags = ", ".join(n["tags"]) if n["tags"] else "—"
        lines.append(f"*{i}. {n['title']}*")
        lines.append(f"🏷 {tags}")
        lines.append(f"{n['summary'][:150]}\n")
    return "\n".join(lines)


def get_stats_text() -> str:
    from collections import Counter
    notes = fetch_notes(limit=100)
    if not notes:
        return "No notes yet!"
    all_tags = []
    for n in notes:
        all_tags.extend(n.get("tags", []))
    tag_counts = Counter(all_tags)
    top_tags = tag_counts.most_common(5)
    dates = sorted([n["date"] for n in notes if n["date"] != "unknown"])
    first = dates[0] if dates else "N/A"
    latest = dates[-1] if dates else "N/A"
    from datetime import datetime, timedelta
    streak = 0
    today = datetime.now().date()
    for i in range(30):
        day = str(today - timedelta(days=i))
        if day in dates:
            streak += 1
        else:
            break
    tags_display = "  ".join([f"{t} ({c})" for t, c in top_tags]) or "none yet"
    return (
        f"📊 *NotionMind Stats*\n\n"
        f"📝 Total notes: {len(notes)}\n"
        f"📅 First note: {first}\n"
        f"📅 Latest note: {latest}\n"
        f"🔥 Streak: {streak} day(s)\n\n"
        f"🏷 Top tags:\n{tags_display}"
    )


def get_export_text() -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    notes = fetch_notes(limit=100)
    if not notes:
        return "No notes to export."
    lines = [f"# NotionMind Export — {today}\n", f"**Total:** {len(notes)}\n", "---\n"]
    for n in notes:
        tags = ", ".join(n["tags"]) if n["tags"] else "—"
        lines.append(f"## {n['title']}")
        lines.append(f"**Date:** {n['date']}  ")
        lines.append(f"**Tags:** {tags}\n")
        lines.append(f"{n['summary']}\n")
        lines.append("---\n")
    return "\n".join(lines)


# ── /start ────────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 *NotionMind Bot*\n\n"
        "Your Notion-powered AI memory on Telegram\\!\n\n"
        "*Notes*\n"
        "/save `<text>` — save a note\n"
        "/ask `<question>` — ask from your notes\n"
        "/today — today's notes\n"
        "/list — recent notes\n"
        "/search `<keyword>` — keyword search\n"
        "/semantic `<query>` — search by meaning\n"
        "/read `<number>` — read full note content\n"
        "/delete `<number>` — delete a note\n"
        "/stats — streak, count, top tags\n"
        "/export — export all notes\n\n"
        "*Tasks & Inbox*\n"
        "/inbox `<task>` — add research task\n"
        "/results — completed tasks\n"
        "/weekly — generate weekly report\n\n"
        "*Todo List*\n"
        "/todos — list pending todos\n"
        "/addtodo `<task>` — add a todo\n"
        "/donetodo `<number>` — mark todo complete\n\n"
        "*Reminders*\n"
        "/remind `<message>` at `HH:MM` — set reminder\n"
        "/reminders — list pending reminders\n\n"
        "*AI Brain*\n"
        "/think `<question>` — multi-hop reasoning\n"
        "/recall `<topic>` — knowledge evolution\n"
        "/dashboard — analytics summary\n"
        "/insights — AI-powered personal insights\n",
        parse_mode="MarkdownV2"
    )


# ── /save ─────────────────────────────────────────────────────────────────────
async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Usage: /save <your note>")
        return
    await update.message.reply_text("💾 Saving...")
    save_note(text)
    await update.message.reply_text("✅ Note saved to Notion!")


# ── /ask ──────────────────────────────────────────────────────────────────────
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = " ".join(context.args)
    if not question:
        await update.message.reply_text("Usage: /ask <your question>")
        return
    await update.message.reply_text("🔍 Searching your notes...")
    answer = ask_question(question, return_text=True)
    await update.message.reply_text(f"🧠 {answer}" if answer else "No answer found.")


# ── /today ────────────────────────────────────────────────────────────────────
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_today_text(), parse_mode="Markdown")


# ── /list ─────────────────────────────────────────────────────────────────────
async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    notes = fetch_notes(limit=10)
    if not notes:
        await update.message.reply_text("No notes yet!")
        return
    lines = ["📋 *Recent Notes*\n"]
    for i, n in enumerate(notes, 1):
        lines.append(f"*{i}. {n['title']}*")
        lines.append(f"📅 {n['date']} | 🏷 {', '.join(n['tags']) if n['tags'] else '—'}\n")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── /search ───────────────────────────────────────────────────────────────────
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = " ".join(context.args)
    if not keyword:
        await update.message.reply_text("Usage: /search <keyword>")
        return
    notes = fetch_notes(limit=50)
    matches = [
        n for n in notes
        if keyword.lower() in n["title"].lower()
        or keyword.lower() in n["summary"].lower()
    ]
    if not matches:
        await update.message.reply_text(f"No notes found for '{keyword}'")
        return
    lines = [f"🔍 *Results for '{keyword}'*\n"]
    for i, n in enumerate(matches[:8], 1):
        lines.append(f"*{i}. {n['title']}*")
        lines.append(f"📅 {n['date']} | {n['summary'][:100]}\n")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── /semantic ─────────────────────────────────────────────────────────────────
async def semantic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Usage: /semantic <query>")
        return
    await update.message.reply_text("🔍 Searching by meaning...")
    try:
        from brain import semantic_search
        results = semantic_search(query, top_k=5)
        if not results:
            await update.message.reply_text(f"No notes found for '{query}'")
            return
        lines = [f"🧠 *Semantic Search: {query}*\n"]
        for i, (note, score) in enumerate(results, 1):
            bar = "█" * int(score * 5) + "░" * (5 - int(score * 5))
            lines.append(f"*{i}. {note['title']}*")
            lines.append(f"Match: {bar} {score:.2f}")
            lines.append(f"📅 {note['date']}\n")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Search failed: {e}")


# ── /read ─────────────────────────────────────────────────────────────────────
async def read(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "Usage: /read <number>\nFirst use /list to see note numbers."
        )
        return
    idx = int(context.args[0])
    notes = fetch_notes(limit=20)
    if not (1 <= idx <= len(notes)):
        await update.message.reply_text(f"Invalid number. Use /list to see available notes.")
        return
    note = notes[idx - 1]
    try:
        from mcp_client import mcp_read_page
        content = mcp_read_page(note["id"])
        if not content or content == "No content blocks found in this page.":
            content = note["summary"] or "No content found."
    except Exception:
        content = note["summary"] or "No content found."

    msg = f"📖 *{note['title']}* — {note['date']}\n\n{content[:3000]}"
    await update.message.reply_text(msg, parse_mode="Markdown")


# ── /delete ───────────────────────────────────────────────────────────────────
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "Usage: /delete <number>\nFirst use /list to see note numbers."
        )
        return
    idx = int(context.args[0])
    notes = fetch_notes(limit=20)
    if not (1 <= idx <= len(notes)):
        await update.message.reply_text("Invalid number.")
        return
    note = notes[idx - 1]
    import httpx
    httpx.patch(
        f"https://api.notion.com/v1/pages/{note['id']}",
        headers={
            "Authorization": f"Bearer {os.environ['NOTION_API_KEY']}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        },
        json={"archived": True},
        timeout=30.0
    )
    await update.message.reply_text(f"🗑 Deleted: *{note['title']}*", parse_mode="Markdown")


# ── /stats ────────────────────────────────────────────────────────────────────
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_stats_text(), parse_mode="Markdown")


# ── /export ───────────────────────────────────────────────────────────────────
async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📤 Exporting notes...")
    content = get_export_text()
    if len(content) > 4000:
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"/tmp/notionmind_export_{today}.md"
        with open(filename, "w") as f:
            f.write(content)
        await update.message.reply_document(
            document=open(filename, "rb"),
            filename=f"notionmind_export_{today}.md"
        )
    else:
        await update.message.reply_text(content, parse_mode="Markdown")


# ── /inbox ────────────────────────────────────────────────────────────────────
async def inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task = " ".join(context.args)
    if not task:
        await update.message.reply_text("Usage: /inbox <research task>")
        return
    add_inbox_task(task)
    await update.message.reply_text(f"📥 Task added to inbox:\n{task}")


# ── /results ──────────────────────────────────────────────────────────────────
async def results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    notes = fetch_notes(limit=50)
    done = [n for n in notes if "done" in n.get("tags", [])]
    if not done:
        await update.message.reply_text("No completed tasks yet.")
        return
    lines = [f"✅ *Completed Tasks ({len(done)})*\n"]
    for n in done[:5]:
        lines.append(f"*{n['title']}*")
        lines.append(f"📅 {n['date']}")
        lines.append(f"{n['summary'][:150]}\n")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── /weekly ───────────────────────────────────────────────────────────────────
async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Generating weekly report...")
    try:
        from executor import generate_weekly_report
        generate_weekly_report()
        await update.message.reply_text("✅ Weekly report generated and saved to Notion!")
    except Exception as e:
        await update.message.reply_text(f"Failed: {e}")


# ── /todos ────────────────────────────────────────────────────────────────────
async def todos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        from todos import fetch_todos
        items = fetch_todos()
        if not items:
            await update.message.reply_text("✅ No pending todos — all caught up!")
            return
        today = datetime.now().strftime("%Y-%m-%d")
        icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        lines = [f"✅ *Pending Todos ({len(items)})*\n"]
        for i, t in enumerate(items, 1):
            icon = icons.get(t["priority"], "🟡")
            due = ""
            if t["due"]:
                if t["due"] < today:
                    due = f" ⚠️ overdue"
                elif t["due"] == today:
                    due = f" ★ today"
                else:
                    due = f" — due {t['due']}"
            lines.append(f"{i}. {icon} *{t['title']}*{due}")
        lines.append("\nUse /donetodo <number> to complete")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Failed: {e}")


# ── /addtodo ──────────────────────────────────────────────────────────────────
async def addtodo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /addtodo <task>\n"
            "Optional: /addtodo <task> priority:high due:2026-03-25"
        )
        return

    raw = " ".join(context.args)
    priority = "medium"
    due = ""

    # parse optional priority and due
    parts = raw.split()
    text_parts = []
    for part in parts:
        if part.startswith("priority:"):
            p = part.replace("priority:", "").lower()
            if p in ["high", "medium", "low"]:
                priority = p
        elif part.startswith("due:"):
            due = part.replace("due:", "")
        else:
            text_parts.append(part)

    title = " ".join(text_parts)
    if not title:
        await update.message.reply_text("Please provide a task title.")
        return

    try:
        from todos import _build_summary
        import httpx
        today = datetime.now().strftime("%Y-%m-%d")
        summary = _build_summary(priority, due, "")
        tags = ["todo", f"priority-{priority}"]
        httpx.post(
            f"https://api.notion.com/v1/pages",
            headers={
                "Authorization": f"Bearer {os.environ['NOTION_API_KEY']}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            },
            json={
                "parent": {"database_id": os.environ["NOTION_DATABASE_ID"]},
                "properties": {
                    "Name":    {"title": [{"text": {"content": title}}]},
                    "Date":    {"date": {"start": today}},
                    "Tags":    {"multi_select": [{"name": t} for t in tags]},
                    "Summary": {"rich_text": [{"text": {"content": summary}}]}
                }
            },
            timeout=30.0
        )
        icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        await update.message.reply_text(
            f"✅ Todo added!\n\n"
            f"{icons[priority]} *{title}*\n"
            f"Priority: {priority}\n"
            f"Due: {due or '—'}",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Failed: {e}")


# ── /donetodo ─────────────────────────────────────────────────────────────────
async def donetodo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /donetodo <number>\nUse /todos to see numbers.")
        return
    idx = int(context.args[0])
    try:
        from todos import fetch_todos
        import httpx
        items = fetch_todos()
        if not (1 <= idx <= len(items)):
            await update.message.reply_text("Invalid number. Use /todos to see pending items.")
            return
        todo = items[idx - 1]
        new_tags = [t for t in todo["tags"] if t != "todo"] + ["todo-done"]
        httpx.patch(
            f"https://api.notion.com/v1/pages/{todo['id']}",
            headers={
                "Authorization": f"Bearer {os.environ['NOTION_API_KEY']}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            },
            json={"properties": {"Tags": {"multi_select": [{"name": t} for t in new_tags]}}},
            timeout=30.0
        )
        await update.message.reply_text(f"✅ Done: *{todo['title']}*", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Failed: {e}")


# ── /remind ───────────────────────────────────────────────────────────────────
async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = " ".join(context.args)
    if not raw or " at " not in raw:
        await update.message.reply_text(
            "Usage: /remind <message> at HH:MM\n"
            "Example: /remind study JEE at 18:30"
        )
        return
    parts = raw.split(" at ")
    message = parts[0].strip()
    time_str = parts[1].strip() if len(parts) > 1 else ""

    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        await update.message.reply_text("Invalid time format. Use HH:MM e.g. 18:30")
        return

    from reminders import load_reminders, save_reminders
    today = datetime.now().strftime("%Y-%m-%d")
    reminders = load_reminders()
    reminders.append({
        "id": str(len(reminders) + 1),
        "message": message,
        "date": today,
        "time": time_str,
        "repeat": "once",
        "done": False
    })
    save_reminders(reminders)
    await update.message.reply_text(
        f"⏰ Reminder set!\n\n*{message}*\nToday at {time_str}",
        parse_mode="Markdown"
    )


# ── /reminders ────────────────────────────────────────────────────────────────
async def reminders_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from reminders import load_reminders
    today = datetime.now().strftime("%Y-%m-%d")
    items = [
        r for r in load_reminders()
        if not r.get("done") and r.get("date", today) >= today
    ]
    items.sort(key=lambda r: (r.get("date", today), r.get("time", "00:00")))
    if not items:
        await update.message.reply_text("⏰ No upcoming reminders.")
        return
    lines = [f"⏰ *Pending Reminders ({len(items)})*\n"]
    for r in items:
        repeat = " ↻" if r.get("repeat") == "daily" else ""
        date = r.get("date", today)
        label = "today" if date == today else date
        lines.append(f"• {label} {r['time']} — {r['message']}{repeat}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── /think ────────────────────────────────────────────────────────────────────
async def think(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = " ".join(context.args)
    if not question:
        await update.message.reply_text("Usage: /think <question>")
        return
    await update.message.reply_text("🧠 Thinking across your notes...")
    try:
        from brain import think as brain_think
        import io, sys
        # capture console output from brain.think()
        # instead call the core logic directly
        from brain import semantic_search, load_graph
        from groq import Groq
        import json as _json

        groq = Groq(api_key=os.environ["GROQ_API_KEY"])

        # extract keywords
        kr = groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": f'Extract 2-4 key search terms. Return ONLY JSON array: ["term1", "term2"]\nQuestion: {question}'}],
            max_tokens=40
        )
        try:
            keywords = _json.loads(kr.choices[0].message.content.strip().replace("```json","").replace("```",""))
        except Exception:
            keywords = [question]

        seen_ids = set()
        top_notes = []
        for kw in keywords:
            for note, score in semantic_search(kw, top_k=4):
                if note["id"] not in seen_ids:
                    seen_ids.add(note["id"])
                    top_notes.append(note)

        if not top_notes:
            await update.message.reply_text("No relevant notes found.")
            return

        context_text = "\n\n".join([
            f"[{n['date']}] \"{n['title']}\"\n{n['summary'][:300]}"
            for n in top_notes
        ])

        response = groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Answer using ONLY the notes provided. Never invent note titles. Be specific and cite exact titles."},
                {"role": "user", "content": f"Question: {question}\n\nNotes:\n{context_text}"}
            ],
            max_tokens=600
        )
        answer = response.choices[0].message.content.strip()
        await update.message.reply_text(f"🧠 *Think Result*\n\n{answer}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Failed: {e}")


# ── /recall ───────────────────────────────────────────────────────────────────
async def recall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(context.args)
    if not topic:
        await update.message.reply_text("Usage: /recall <topic>")
        return
    await update.message.reply_text(f"🧠 Recalling your knowledge on '{topic}'...")
    try:
        from brain import semantic_search
        from groq import Groq

        groq = Groq(api_key=os.environ["GROQ_API_KEY"])
        results = semantic_search(topic, top_k=10)
        relevant = [(n, s) for n, s in results if s >= 0.28]

        if not relevant:
            await update.message.reply_text(f"No notes found on '{topic}'.")
            return

        relevant.sort(key=lambda x: x[0]["date"])
        timeline = "\n\n".join([
            f"[{n['date']}] {n['title']}:\n{n['summary'][:250]}"
            for n, _ in relevant
        ])

        response = groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Analyse notes chronologically. Show how understanding evolved. Be specific, cite titles and dates. 3-4 sentences max."},
                {"role": "user", "content": f"Topic: {topic}\n\nNotes:\n{timeline}"}
            ],
            max_tokens=400
        )
        evolution = response.choices[0].message.content.strip()
        await update.message.reply_text(
            f"🧠 *Knowledge Evolution: {topic}*\n\n{evolution}\n\n_{len(relevant)} note(s) found_",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Failed: {e}")


# ── /dashboard ────────────────────────────────────────────────────────────────
async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Building dashboard...")
    try:
        from collections import Counter, defaultdict
        from datetime import timedelta

        notes = fetch_notes(limit=100)
        EXCLUDED = ["auto-generated", "summary", "daily", "weekly-report", "category", "merged"]
        notes = [n for n in notes if not any(t in n.get("tags", []) for t in EXCLUDED)]

        today = datetime.now().date()
        today_str = str(today)
        week_start = str(today - timedelta(days=7))

        total = len(notes)
        today_count = sum(1 for n in notes if n["date"] == today_str)
        week_count = sum(1 for n in notes if n["date"] >= week_start)

        streak = 0
        dates = [n["date"] for n in notes]
        for i in range(30):
            d = str(today - timedelta(days=i))
            if d in dates:
                streak += 1
            else:
                break

        all_tags = []
        for n in notes:
            all_tags.extend([t for t in n.get("tags", []) if t not in EXCLUDED])
        tag_counts = Counter(all_tags).most_common(5)
        top_tags = "  ".join([f"{t}({c})" for t, c in tag_counts]) or "none"

        # topic velocity
        this_week_tags = Counter()
        last_week_start = str(today - timedelta(days=14))
        for n in notes:
            if n["date"] >= week_start:
                for t in n.get("tags", []):
                    if t not in EXCLUDED:
                        this_week_tags[t] += 1

        velocity_lines = []
        for tag, count in this_week_tags.most_common(5):
            velocity_lines.append(f"  {tag}: {count} ↑")

        lines = [
            "📊 *NotionMind Dashboard*\n",
            f"🗒 Total notes: {total}",
            f"📅 Today: {today_count}",
            f"📊 This week: {week_count}",
            f"🔥 Streak: {streak} day(s)",
            f"\n🏷 Top tags: {top_tags}",
            f"\n⚡ Topic velocity this week:"
        ]
        lines.extend(velocity_lines or ["  No activity yet"])

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Failed: {e}")


# ── /insights ─────────────────────────────────────────────────────────────────
async def insights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔮 Running AI analysis on your notes...")
    try:
        from groq import Groq
        from datetime import timedelta

        groq = Groq(api_key=os.environ["GROQ_API_KEY"])
        EXCLUDED = ["auto-generated", "summary", "daily", "weekly-report", "category", "merged"]
        notes = fetch_notes(limit=100)
        notes = [n for n in notes if not any(t in n.get("tags", []) for t in EXCLUDED)]

        if not notes:
            await update.message.reply_text("No notes found for analysis.")
            return

        context_text = "\n".join([
            f"[{n['date']}] {n['title']} [tags: {', '.join(n.get('tags', [])) or 'none'}]: {n['summary'][:150]}"
            for n in sorted(notes, key=lambda x: x["date"])
        ])

        response = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Personal knowledge analyst. Be specific, cite actual note titles and dates. Never be generic."},
                {"role": "user", "content": f"""Give me these 4 insights in 1-2 sentences each:
1. PEAK PRODUCTIVITY — when am I most active?
2. KNOWLEDGE GAPS — what am I underexploring?
3. FADING TOPICS — what did I explore but drifted from?
4. THIS WEEK'S ACTION — one specific thing to do

Notes:
{context_text}

Today: {datetime.now().strftime('%Y-%m-%d')}"""}
            ],
            max_tokens=500
        )

        result = response.choices[0].message.content.strip()
        await update.message.reply_text(
            f"🔮 *AI Insights*\n\n{result}",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Failed: {e}")

# ── /menu ─────────────────────────────────────────────────────────────────────
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 *NotionMind — All Commands*\n\n"
        "📝 *Notes*\n"
        "/save `<text>` — save a note\n"
        "/ask `<question>` — ask from your notes\n"
        "/today — today's notes\n"
        "/list — recent 10 notes\n"
        "/search `<keyword>` — keyword search\n"
        "/semantic `<query>` — search by meaning\n"
        "/read `<number>` — read full note content\n"
        "/delete `<number>` — delete a note\n"
        "/stats — streak, count, top tags\n"
        "/export — export all notes as markdown\n\n"
        "📥 *Tasks & Inbox*\n"
        "/inbox `<task>` — add research task\n"
        "/results — view completed tasks\n"
        "/weekly — generate weekly report\n\n"
        "✅ *Todo List*\n"
        "/todos — list pending todos\n"
        "/addtodo `<task>` — add a todo\n"
        "          optional: `priority:high due:2026-03-25`\n"
        "/donetodo `<number>` — mark todo complete\n\n"
        "⏰ *Reminders*\n"
        "/remind `<message>` at `HH:MM` — set reminder\n"
        "/reminders — list upcoming reminders\n\n"
        "🧠 *AI Brain*\n"
        "/think `<question>` — multi-hop reasoning\n"
        "/recall `<topic>` — knowledge evolution\n"
        "/semantic `<query>` — semantic search\n\n"
        "📊 *Analytics*\n"
        "/dashboard — stats and topic velocity\n"
        "/insights — AI-powered personal insights\n\n"
        "/menu — show this menu\n"
        "/start — welcome message",
        parse_mode="Markdown"
    )
# ── main ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",      start))
    app.add_handler(CommandHandler("menu",       menu))
    app.add_handler(CommandHandler("save",       save))
    app.add_handler(CommandHandler("ask",        ask))
    app.add_handler(CommandHandler("today",      today))
    app.add_handler(CommandHandler("list",       list_cmd))
    app.add_handler(CommandHandler("search",     search))
    app.add_handler(CommandHandler("semantic",   semantic))
    app.add_handler(CommandHandler("read",       read))
    app.add_handler(CommandHandler("delete",     delete))
    app.add_handler(CommandHandler("stats",      stats))
    app.add_handler(CommandHandler("export",     export))
    app.add_handler(CommandHandler("inbox",      inbox))
    app.add_handler(CommandHandler("results",    results))
    app.add_handler(CommandHandler("weekly",     weekly))
    app.add_handler(CommandHandler("todos",      todos))
    app.add_handler(CommandHandler("addtodo",    addtodo))
    app.add_handler(CommandHandler("donetodo",   donetodo))
    app.add_handler(CommandHandler("remind",     remind))
    app.add_handler(CommandHandler("reminders",  reminders_cmd))
    app.add_handler(CommandHandler("think",      think))
    app.add_handler(CommandHandler("recall",     recall))
    app.add_handler(CommandHandler("dashboard",  dashboard))
    app.add_handler(CommandHandler("insights",   insights))

    print("🤖 NotionMind Telegram Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
