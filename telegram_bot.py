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
    search_notes as _search_notes,
    add_inbox_task
)

load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# ── helper: fetch today's notes as text ──────────────────────────────────────
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

# ── helper: fetch stats as text ───────────────────────────────────────────────
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

# ── helper: export all notes as markdown text ─────────────────────────────────
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
        "Control your Notion workspace from Telegram!\n\n"
        "Commands:\n"
        "/save `<text>` — save a note\n"
        "/ask `<question>` — ask from your notes\n"
        "/today — show today's notes\n"
        "/list — show recent notes\n"
        "/search `<keyword>` — search notes\n"
        "/stats — show stats\n"
        "/inbox `<task>` — add research task\n"
        "/export — export all notes",
        parse_mode="Markdown"
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
    for i, n in enumerate(matches, 1):
        lines.append(f"*{i}. {n['title']}*")
        lines.append(f"📅 {n['date']} | {n['summary'][:100]}\n")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# ── /stats ────────────────────────────────────────────────────────────────────
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_stats_text(), parse_mode="Markdown")

# ── /inbox ────────────────────────────────────────────────────────────────────
async def inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task = " ".join(context.args)
    if not task:
        await update.message.reply_text("Usage: /inbox <research task>")
        return
    add_inbox_task(task)
    await update.message.reply_text(f"📥 Task added to inbox:\n{task}")

# ── /export ───────────────────────────────────────────────────────────────────
async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📤 Exporting notes...")
    content = get_export_text()

    # send as file if too long
    if len(content) > 4000:
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"/tmp/notionmind_export_{today}.md"
        with open(filename, "w") as f:
            f.write(content)
        await update.message.reply_document(document=open(filename, "rb"),
                                             filename=f"notionmind_export_{today}.md")
    else:
        await update.message.reply_text(content, parse_mode="Markdown")

# ── main ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("save",   save))
    app.add_handler(CommandHandler("ask",    ask))
    app.add_handler(CommandHandler("today",  today))
    app.add_handler(CommandHandler("list",   list_cmd))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("stats",  stats))
    app.add_handler(CommandHandler("inbox",  inbox))
    app.add_handler(CommandHandler("export", export))

    print("🤖 NotionMind Telegram Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
