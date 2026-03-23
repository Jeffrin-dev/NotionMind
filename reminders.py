import os
import json
import time
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

console = Console()
REMINDERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reminders.json")

# ── load reminders ────────────────────────────────────────────────────────────
def load_reminders() -> list:
    if not os.path.exists(REMINDERS_FILE):
        return []
    with open(REMINDERS_FILE, "r") as f:
        return json.load(f)

# ── save reminders ────────────────────────────────────────────────────────────
def save_reminders(reminders: list):
    with open(REMINDERS_FILE, "w") as f:
        json.dump(reminders, f, indent=2)

# ── add reminder ──────────────────────────────────────────────────────────────
def add_reminder(message: str = None, time_str: str = None, repeat: str = None):
    if not message:
        message = Prompt.ask("[green]Reminder message[/]")
    if not time_str:
        time_str = Prompt.ask("[green]Time (HH:MM, 24hr)[/]")

    # ask for date
    today = datetime.now().strftime("%Y-%m-%d")
    date_str = Prompt.ask("[green]Date (YYYY-MM-DD) or press Enter for today[/]", default=today)

    # validate date
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        console.print("[red]Invalid date format. Use YYYY-MM-DD e.g. 2026-03-25[/]")
        return

    # validate time
    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        console.print("[red]Invalid time format. Use HH:MM e.g. 18:30[/]")
        return

    if not repeat:
        repeat = Prompt.ask("[green]Repeat[/]", choices=["once", "daily"], default="once")

    reminders = load_reminders()
    new_id = str(len(reminders) + 1)

    reminders.append({
        "id": new_id,
        "message": message,
        "date": date_str,
        "time": time_str,
        "repeat": repeat,
        "done": False
    })

    save_reminders(reminders)

    console.print(Panel(
        f"[bold green]✓ Reminder set![/]\n\n"
        f"[cyan]Message:[/] {message}\n"
        f"[cyan]Date:[/]    {date_str}\n"
        f"[cyan]Time:[/]    {time_str}\n"
        f"[cyan]Repeat:[/]  {repeat}",
        title="Reminder"
    ))
    
# ── list reminders ────────────────────────────────────────────────────────────
def list_reminders():
    reminders = load_reminders()
    pending = [r for r in reminders if not r["done"]]

    if not pending:
        console.print("[yellow]No pending reminders.[/]")
        return

    table = Table(title="Pending Reminders", show_lines=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Date", style="white", width=12)
    table.add_column("Time", style="white", width=8)
    table.add_column("Repeat", style="cyan", width=8)
    table.add_column("Message", style="white", width=40)

    for r in pending:
        table.add_row(r["id"], r.get("date", "—"), r["time"], r["repeat"], r["message"])

    console.print(table)

# ── delete reminder ───────────────────────────────────────────────────────────
def delete_reminder():
    reminders = load_reminders()
    pending = [r for r in reminders if not r["done"]]

    if not pending:
        console.print("[yellow]No pending reminders.[/]")
        return

    table = Table(title="Select reminder to delete", show_lines=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Time", style="white", width=8)
    table.add_column("Message", style="white", width=40)

    for i, r in enumerate(pending, 1):
        table.add_row(str(i), r["time"], r["message"])

    console.print(table)

    idx = Prompt.ask("[red]Enter number to delete (or 0 to cancel)[/]")
    if not idx.isdigit() or int(idx) == 0:
        console.print("[yellow]Cancelled.[/]")
        return

    selected = pending[int(idx) - 1]
    confirmed = Confirm.ask(f"[red]Delete reminder: '[bold]{selected['message']}[/]'?[/]")
    if not confirmed:
        console.print("[yellow]Cancelled.[/]")
        return

    reminders = [r for r in reminders if r["id"] != selected["id"]]
    save_reminders(reminders)
    console.print("[green]✓ Reminder deleted.[/]")

# ── check and trigger reminders ───────────────────────────────────────────────
def check_reminders():
    reminders = load_reminders()
    now_time = datetime.now().strftime("%H:%M")
    now_date = datetime.now().strftime("%Y-%m-%d")
    triggered = False

    for r in reminders:
        if r["done"]:
            continue

        # support old reminders without date field
        r_date = r.get("date", now_date)

        if r["time"] == now_time and r_date == now_date:
            triggered = True
            console.print(Panel(
                f"[bold yellow]⏰ Reminder![/]\n\n"
                f"{r['message']}",
                title="NotionMind Reminder"
            ))

            # voice notification
            try:
                from voice import speak
                speak(f"Reminder: {r['message']}")
            except:
                pass

            # telegram notification
            try:
                import httpx
                token = os.environ.get("TELEGRAM_BOT_TOKEN")
                chat_id = os.environ.get("TELEGRAM_CHAT_ID")
                if token and chat_id:
                    httpx.post(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        json={"chat_id": chat_id, "text": f"⏰ Reminder: {r['message']}"}
                    )
            except:
                pass

            # mark done if once, advance date if daily
            if r["repeat"] == "once":
                r["done"] = True
            elif r["repeat"] == "daily":
                from datetime import timedelta
                next_date = datetime.strptime(r_date, "%Y-%m-%d") + timedelta(days=1)
                r["date"] = next_date.strftime("%Y-%m-%d")

    if triggered:
        save_reminders(reminders)

# ── run reminder daemon ───────────────────────────────────────────────────────
def run_daemon():
    console.print(Panel(
        "[bold cyan]Reminder Daemon Running[/]\n"
        "[dim]Checking reminders every minute.\n"
        "Press Ctrl+C to stop.[/]",
        title="Reminders"
    ))
    try:
        while True:
            check_reminders()
            time.sleep(60)
    except KeyboardInterrupt:
        console.print("\n[dim]Reminder daemon stopped.[/]")

if __name__ == "__main__":
    run_daemon()
