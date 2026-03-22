import os
import sys
import schedule
import time
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

load_dotenv()
console = Console()

VENV_PYTHON = sys.executable

# ── run executor ──────────────────────────────────────────────────────────────
def run_executor():
    console.print(f"\n[dim]{datetime.now().strftime('%H:%M:%S')}[/] [cyan]Running executor...[/]")
    try:
        result = subprocess.run(
            [VENV_PYTHON, "executor.py"],
            capture_output=False,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        console.print(f"[green]✓ Executor completed[/]")
    except Exception as e:
        console.print(f"[red]✗ Executor failed: {e}[/]")

# ── setup cron job ────────────────────────────────────────────────────────────
def setup_cron(hour: int, minute: int):
    project_dir = os.path.dirname(os.path.abspath(__file__))
    python_path = VENV_PYTHON
    executor_path = os.path.join(project_dir, "executor.py")
    log_path = os.path.join(project_dir, "executor.log")

    cron_line = f"{minute} {hour} * * * {python_path} {executor_path} >> {log_path} 2>&1"

    # read existing crontab
    result = subprocess.run(["crontab", "-l"],
                            capture_output=True, text=True)
    existing = result.stdout if result.returncode == 0 else ""

    # check if already added
    if executor_path in existing:
        console.print("[yellow]Cron job already exists. Updating...[/]")
        lines = [l for l in existing.splitlines()
                 if executor_path not in l]
        existing = "\n".join(lines) + "\n"

    new_crontab = existing + cron_line + "\n"

    # write new crontab
    proc = subprocess.Popen(["crontab", "-"],
                            stdin=subprocess.PIPE, text=True)
    proc.communicate(input=new_crontab)

    console.print(Panel(
        f"[bold green]✓ Cron job set![/]\n\n"
        f"[cyan]Schedule:[/] Every day at {hour:02d}:{minute:02d}\n"
        f"[cyan]Log file:[/] {log_path}\n\n"
        f"[dim]Cron entry:\n{cron_line}[/]",
        title="Cron Scheduler"
    ))

# ── remove cron job ───────────────────────────────────────────────────────────
def remove_cron():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    executor_path = os.path.join(project_dir, "executor.py")

    result = subprocess.run(["crontab", "-l"],
                            capture_output=True, text=True)
    if result.returncode != 0 or executor_path not in result.stdout:
        console.print("[yellow]No cron job found.[/]")
        return

    lines = [l for l in result.stdout.splitlines()
             if executor_path not in l]
    new_crontab = "\n".join(lines) + "\n"

    proc = subprocess.Popen(["crontab", "-"],
                            stdin=subprocess.PIPE, text=True)
    proc.communicate(input=new_crontab)
    console.print("[green]✓ Cron job removed.[/]")

# ── python scheduler (runs while app open) ────────────────────────────────────
def start_python_scheduler(hour: int, minute: int):
    schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(run_executor)

    console.print(Panel(
        f"[bold cyan]Python Scheduler Running[/]\n\n"
        f"[cyan]Schedule:[/] Every day at {hour:02d}:{minute:02d}\n"
        f"[dim]Keep this terminal open.\n"
        f"Press Ctrl+C to stop.[/]",
        title="Scheduler"
    ))

    while True:
        schedule.run_pending()
        now = datetime.now().strftime("%H:%M")
        scheduled = f"{hour:02d}:{minute:02d}"
        remaining = schedule.idle_seconds()
        hrs = int(remaining // 3600)
        mins = int((remaining % 3600) // 60)
        console.print(
            f"[dim]Next run in {hrs}h {mins}m — "
            f"press Ctrl+C to stop[/]",
            end="\r"
        )
        time.sleep(60)

# ── interactive menu ──────────────────────────────────────────────────────────
def interactive():
    console.print(Panel(
        "[bold cyan]NotionMind Scheduler[/]\n\n"
        "[dim]Options:\n"
        "  cron    — set a daily cron job (runs even when app is closed)\n"
        "  python  — run scheduler while this terminal is open\n"
        "  run     — trigger executor right now\n"
        "  remove  — remove existing cron job\n"
        "  quit    — exit[/]",
        title="Scheduler"
    ))

    while True:
        cmd = Prompt.ask(
            "\n[bold cyan]>[/] Choose option",
            choices=["cron", "python", "run", "remove", "quit"]
        )

        if cmd == "quit":
            console.print("[dim]Goodbye![/]")
            break

        elif cmd == "run":
            run_executor()

        elif cmd == "remove":
            remove_cron()

        elif cmd in ["cron", "python"]:
            time_str = Prompt.ask(
                "[green]What time to run daily? (HH:MM, 24hr)[/]",
                default="20:00"
            )
            try:
                hour, minute = map(int, time_str.split(":"))
                assert 0 <= hour <= 23 and 0 <= minute <= 59
            except:
                console.print("[red]Invalid time. Use HH:MM format e.g. 20:00[/]")
                continue

            if cmd == "cron":
                setup_cron(hour, minute)
            else:
                start_python_scheduler(hour, minute)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "run":
            run_executor()
        elif sys.argv[1] == "cron" and len(sys.argv) > 2:
            h, m = map(int, sys.argv[2].split(":"))
            setup_cron(h, m)
        elif sys.argv[1] == "remove":
            remove_cron()
    else:
        interactive()
