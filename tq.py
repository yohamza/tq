#!/usr/bin/env python3
"""
tq — Tutorial Queue
A smart CLI + TUI tutorial tracker.

Usage:
  python tq.py                         # Open full TUI
  python tq.py add "Title" -d 45       # Add tutorial
  python tq.py list                    # List queue
  python tq.py pick                    # Smart pick next
  python tq.py done <id>               # Mark as done
  python tq.py progress <id> 75        # Set progress %
  python tq.py schedule <id> today     # Schedule for a day
  python tq.py stats                   # Streak & summary
  python tq.py goal 60                 # Set daily goal (mins)
"""

import json
import sys
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# ── Config ────────────────────────────────────────────────────────────────────

DATA_PATH     = Path.home() / ".config" / "tq" / "data.json"
STATUS_LABELS = {"todo": "To Watch", "in_progress": "In Progress", "done": "Done"}
STATUS_COLORS = {"todo": "dim",      "in_progress": "yellow",      "done": "green"}
STATUS_ICONS  = {"todo": "○",        "in_progress": "▶",           "done": "✅"}

# ── Storage ───────────────────────────────────────────────────────────────────

def load_data() -> dict:
    if not DATA_PATH.exists():
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        d = {
            "tutorials": [],
            "settings": {
                "daily_goal_mins": 60,
                "streak": {"count": 0, "last_date": None},
            },
        }
        DATA_PATH.write_text(json.dumps(d, indent=2))
        return d
    return json.loads(DATA_PATH.read_text())

def save_data(data: dict) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(data, indent=2))

def today_str() -> str:
    return date.today().isoformat()

def parse_date(s: str) -> str:
    s = s.strip().lower()
    if s in ("today", ""):  return today_str()
    if s == "tomorrow":     return (date.today() + timedelta(days=1)).isoformat()
    try:
        from datetime import datetime
        datetime.strptime(s, "%Y-%m-%d")
        return s
    except ValueError:
        raise typer.BadParameter(f"Use 'today', 'tomorrow', or YYYY-MM-DD — got '{s}'")

def update_streak(data: dict) -> None:
    st        = data["settings"].setdefault("streak", {"count": 0, "last_date": None})
    tod       = today_str()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    if st["last_date"] == tod:
        return
    st["count"]     = (st["count"] + 1) if st["last_date"] == yesterday else 1
    st["last_date"] = tod

# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt_mins(m: int) -> str:
    if not m: return "?"
    h, r = divmod(m, 60)
    return f"{h}h {r}m" if h and r else f"{h}h" if h else f"{r}m"

def short_id(tid: str) -> str:
    return tid[:6]

def fmt_bar(pct: int, w: int = 18) -> str:
    f = int(w * pct / 100)
    return f"[green]{'█' * f}[/green][dim]{'░' * (w - f)}[/dim] {pct}%"

# ── Smart Pick ────────────────────────────────────────────────────────────────

def smart_pick(tutorials: list) -> Optional[dict]:
    """
    Priority order:
      1. Resume highest-progress in-progress tutorial
      2. Scheduled for today (shortest first)
      3. Shortest todo (quick win)
    """
    pool = [t for t in tutorials if t["status"] != "done"]
    if not pool:
        return None
    ip = [t for t in pool if t["status"] == "in_progress"]
    if ip:
        return sorted(ip, key=lambda t: t.get("progress", 0), reverse=True)[0]
    sched = [t for t in pool if t.get("scheduled") == today_str()]
    if sched:
        return sorted(sched, key=lambda t: t.get("duration_mins", 999))[0]
    return sorted(pool, key=lambda t: t.get("duration_mins", 999))[0]

# ── CLI App ───────────────────────────────────────────────────────────────────

cli = typer.Typer(
    name="tq",
    invoke_without_command=True,
    no_args_is_help=False,
    help="📚 tq — Tutorial Queue, your smart learning tracker",
)

@cli.callback(invoke_without_command=True)
def _default(ctx: typer.Context):
    """Open TUI when called with no subcommand."""
    if ctx.invoked_subcommand is None:
        _launch_tui()

@cli.command()
def add(
    title:    str = typer.Argument(...,                                       help="Tutorial title"),
    url:      str = typer.Option("",      "--url",      "-u",                help="URL"),
    duration: int = typer.Option(0,       "--duration", "-d",                help="Duration in minutes"),
    topic:    str = typer.Option("Other", "--topic",    "-t",                help="Topic tag"),
    schedule: str = typer.Option("",      "--schedule", "-s",                help="today / tomorrow / YYYY-MM-DD"),
):
    """📥 Add a new tutorial to the queue."""
    data = load_data()
    tid  = str(uuid.uuid4())
    data["tutorials"].append({
        "id":            tid,
        "title":         title,
        "url":           url,
        "topic":         topic,
        "duration_mins": duration,
        "status":        "todo",
        "progress":      0,
        "added":         today_str(),
        "scheduled":     parse_date(schedule) if schedule else "",
        "completed_date": None,
    })
    save_data(data)
    rprint(f"[green]✓[/green] Added [bold]{title}[/bold]  [dim]id:{short_id(tid)}[/dim]")
    if schedule:
        rprint(f"  [cyan]📅 Scheduled → {parse_date(schedule)}[/cyan]")

@cli.command("list")
def list_cmd(
    topic:  str = typer.Option("", "--topic",  "-t", help="Filter by topic"),
    status: str = typer.Option("", "--status", "-s", help="todo / in_progress / done"),
):
    """📋 List your tutorial queue."""
    data = load_data()
    tuts = data["tutorials"]
    if topic:  tuts = [t for t in tuts if t["topic"].lower() == topic.lower()]
    if status: tuts = [t for t in tuts if t["status"] == status]

    def _section(rows, title):
        if not rows: return
        tbl = Table(title=title, box=None, header_style="bold cyan", show_lines=False)
        tbl.add_column("ID",       width=7,  style="dim")
        tbl.add_column("Title",    max_width=34, style="bold")
        tbl.add_column("Topic",    width=12)
        tbl.add_column("Dur",      width=6)
        tbl.add_column("Progress", width=26)
        tbl.add_column("Schedule", width=12)
        for t in rows:
            c = STATUS_COLORS[t["status"]]
            tbl.add_row(
                short_id(t["id"]),
                f"[{c}]{t['title']}[/{c}]",
                t["topic"],
                fmt_mins(t.get("duration_mins", 0)),
                fmt_bar(t.get("progress", 0)),
                t.get("scheduled") or "[dim]—[/dim]",
            )
        console.print(tbl)

    _section([t for t in tuts if t["status"] != "done"], "📚 Queue")
    _section([t for t in tuts if t["status"] == "done"],  "✅ Done")
    if not tuts:
        rprint("[dim]Queue is empty. Run [bold]tq add[/bold] to start![/dim]")

    # Footer summary
    st         = data["settings"].get("streak", {})
    goal       = data["settings"].get("daily_goal_mins", 60)
    done_today = sum(t.get("duration_mins", 0) for t in data["tutorials"] if t.get("completed_date") == today_str())
    q          = sum(1 for t in data["tutorials"] if t["status"] != "done")
    rprint(
        f"\n🔥 Streak [bold]{st.get('count', 0)}d[/bold]  "
        f"⚡ Today [bold]{fmt_mins(done_today)}/{fmt_mins(goal)}[/bold]  "
        f"📚 Queue [bold]{q}[/bold]"
    )

@cli.command()
def pick():
    """🎯 Smart-pick the next best tutorial to watch."""
    data = load_data()
    t    = smart_pick(data["tutorials"])
    if not t:
        rprint("[green]🎉 Queue is empty — nothing to pick![/green]")
        return
    rprint(Panel(
        f"[bold cyan]{t['title']}[/bold cyan]\n"
        f"[dim]Topic:[/dim]    {t['topic']}  "
        f"[dim]Duration:[/dim] {fmt_mins(t.get('duration_mins', 0))}\n"
        f"[dim]Progress:[/dim] {fmt_bar(t.get('progress', 0))}"
        + (f"\n[dim]URL:[/dim]     {t['url']}" if t.get("url") else ""),
        title="🎯 Pick for Me",
        border_style="cyan",
    ))
    rprint(f"[dim]→ tq progress {short_id(t['id'])} <pct>    tq done {short_id(t['id'])}[/dim]")

@cli.command()
def done(tutorial_id: str = typer.Argument(..., help="Tutorial ID (first 6 chars)")):
    """✅ Mark a tutorial as done."""
    data = load_data()
    for t in data["tutorials"]:
        if t["id"].startswith(tutorial_id):
            t.update({"status": "done", "progress": 100, "completed_date": today_str()})
            update_streak(data)
            save_data(data)
            streak = data["settings"]["streak"]["count"]
            rprint(f"[green]✓[/green] [bold]{t['title']}[/bold] — complete! 🎉  🔥 Streak: {streak}d")
            return
    rprint(f"[red]Not found:[/red] no tutorial with id starting with '{tutorial_id}'")

@cli.command()
def progress(
    tutorial_id: str = typer.Argument(...,             help="Tutorial ID"),
    pct:         int = typer.Argument(..., min=0, max=100, help="Progress 0–100"),
):
    """📊 Update progress on a tutorial."""
    data = load_data()
    for t in data["tutorials"]:
        if t["id"].startswith(tutorial_id):
            t["progress"] = pct
            if pct >= 100: t["status"] = "done";        t["completed_date"] = today_str(); update_streak(data)
            elif pct > 0:  t["status"] = "in_progress"
            else:          t["status"] = "todo"
            save_data(data)
            rprint(f"[cyan]◈[/cyan] [bold]{t['title']}[/bold]: {fmt_bar(pct)}")
            return
    rprint(f"[red]Not found:[/red] '{tutorial_id}'")

@cli.command()
def schedule(
    tutorial_id: str = typer.Argument(...),
    when:        str = typer.Argument(..., help="today / tomorrow / YYYY-MM-DD"),
):
    """📅 Schedule a tutorial for a specific day."""
    data = load_data()
    d    = parse_date(when)
    for t in data["tutorials"]:
        if t["id"].startswith(tutorial_id):
            t["scheduled"] = d
            save_data(data)
            rprint(f"[cyan]📅[/cyan] [bold]{t['title']}[/bold] → {d}")
            return
    rprint(f"[red]Not found:[/red] '{tutorial_id}'")

@cli.command()
def stats():
    """📈 Show your learning stats and streak."""
    data       = load_data()
    tuts       = data["tutorials"]
    st         = data["settings"].get("streak", {})
    goal       = data["settings"].get("daily_goal_mins", 60)
    done_today = sum(t.get("duration_mins", 0) for t in tuts if t.get("completed_date") == today_str())
    pct        = min(100, int(done_today / goal * 100)) if goal else 0
    total_mins = sum(t.get("duration_mins", 0) for t in tuts if t["status"] == "done")
    rprint(Panel(
        f"[bold]🔥 Streak[/bold]         {st.get('count', 0)} days\n"
        f"[bold]⚡ Daily Goal[/bold]     {fmt_bar(pct, 12)}  {fmt_mins(done_today)} / {fmt_mins(goal)}\n\n"
        f"[bold]📚 Total[/bold]          {len(tuts)}\n"
        f"[bold]✅ Done[/bold]           [green]{sum(1 for t in tuts if t['status']=='done')}[/green]\n"
        f"[bold]▶  In Progress[/bold]   [yellow]{sum(1 for t in tuts if t['status']=='in_progress')}[/yellow]\n"
        f"[bold]⏳ To Watch[/bold]       {sum(1 for t in tuts if t['status']=='todo')}\n\n"
        f"[bold]⏱  Time Learned[/bold]  {fmt_mins(total_mins)}",
        title="📈 Your Stats",
        border_style="cyan",
    ))

@cli.command()
def goal(mins: int = typer.Argument(..., help="Daily learning goal in minutes")):
    """🎯 Set your daily learning goal."""
    data = load_data()
    data["settings"]["daily_goal_mins"] = mins
    save_data(data)
    rprint(f"[green]✓[/green] Daily goal → [bold]{fmt_mins(mins)}[/bold]")

# ── TUI ───────────────────────────────────────────────────────────────────────

def _launch_tui() -> None:
    try:
        from textual.app import App, ComposeResult
        from textual.binding import Binding
        from textual.containers import Container, Horizontal
        from textual.screen import ModalScreen
        from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Static
    except ImportError:
        rprint("[red]Textual not installed.[/red] Run: [bold]pip install textual[/bold]")
        sys.exit(1)

    from rich.text import Text

    # ── Add Tutorial Modal ────────────────────────────────────────────────────

    class AddModal(ModalScreen):
        BINDINGS = [Binding("escape", "dismiss", "Cancel")]
        DEFAULT_CSS = """
        AddModal { align: center middle; }
        #modal-box {
            background: $surface; border: tall $primary;
            padding: 1 2; width: 58; height: auto;
        }
        #modal-title { text-style: bold; margin-bottom: 1; }
        .field-label { color: $text-muted; margin-top: 1; }
        #modal-btns { margin-top: 1; height: 3; }
        #modal-btns Button { min-width: 12; margin-right: 1; height: 3; }
        """
        def compose(self) -> ComposeResult:
            with Container(id="modal-box"):
                yield Label("Add Tutorial", id="modal-title")
                yield Label("Title *",                               classes="field-label")
                yield Input(placeholder="React Hooks Deep Dive",    id="i-title")
                yield Label("URL",                                   classes="field-label")
                yield Input(placeholder="https://youtube.com/...",  id="i-url")
                yield Label("Topic",                                 classes="field-label")
                yield Input(placeholder="React / Python / CSS",     id="i-topic", value="Other")
                yield Label("Duration (minutes)",                    classes="field-label")
                yield Input(placeholder="45",                        id="i-dur")
                yield Label("Schedule (today / tomorrow / YYYY-MM-DD)", classes="field-label")
                yield Input(placeholder="today",                     id="i-sched")
                with Horizontal(id="modal-btns"):
                    yield Button("Save",   variant="primary", id="btn-ok")
                    yield Button("Cancel", variant="default", id="btn-cancel")

        def on_button_pressed(self, e: Button.Pressed) -> None:
            if e.button.id == "btn-cancel":
                self.dismiss(None)
                return
            title = self.query_one("#i-title", Input).value.strip()
            if not title:
                return
            try:    dur = int(self.query_one("#i-dur", Input).value.strip() or "0")
            except: dur = 0
            sched_raw = self.query_one("#i-sched", Input).value.strip()
            try:    sched = parse_date(sched_raw) if sched_raw else ""
            except: sched = ""
            self.dismiss({
                "title":         title,
                "url":           self.query_one("#i-url",   Input).value.strip(),
                "topic":         self.query_one("#i-topic", Input).value.strip() or "Other",
                "duration_mins": dur,
                "scheduled":     sched,
            })

    # ── Progress Modal ────────────────────────────────────────────────────────

    class ProgModal(ModalScreen):
        BINDINGS = [Binding("escape", "dismiss", "Cancel")]
        DEFAULT_CSS = """
        ProgModal { align: center middle; }
        #pm-box {
            background: $surface; border: tall $primary;
            padding: 1 2; width: 46; height: auto;
        }
        #pm-title { text-style: bold; margin-bottom: 1; }
        #pm-btns  { margin-top: 1; }
        #pm-btns Button { min-width: 12; margin-right: 1; }
        """
        def __init__(self, tutorial_title: str):
            super().__init__()
            self._tut_title = tutorial_title

        def compose(self) -> ComposeResult:
            with Container(id="pm-box"):
                yield Label(f"Set progress for: {self._tut_title[:36]}", id="pm-title")
                yield Input(placeholder="0 - 100", id="pm-inp")
                with Horizontal(id="pm-btns"):
                    yield Button("Save",   variant="primary", id="pm-ok")
                    yield Button("Cancel", variant="default", id="pm-cancel")

        def on_button_pressed(self, e: Button.Pressed) -> None:
            if e.button.id == "pm-cancel":
                self.dismiss(None)
                return
            try:    self.dismiss(int(self.query_one("#pm-inp", Input).value))
            except: self.dismiss(None)

    # ── Main TUI App ──────────────────────────────────────────────────────────

    class TQApp(App):
        TITLE = "tq - Tutorial Queue"
        CSS = """
        Screen { background: $background; }
        #stats-bar {
            height: 1;
            background: $surface;
            padding: 0 2;
            color: $text-muted;
        }
        DataTable { height: 1fr; }
        #empty-state {
            width: 1fr; height: 1fr;
            align: center middle;
        }
        #empty-state Static {
            content-align: center middle;
            width: auto;
            margin-bottom: 1;
        }
        #empty-state Button { min-width: 20; }
        """
        BINDINGS = [
            Binding("a", "add",       "Add",          show=True),
            Binding("o", "open_url",  "Open URL",     show=True),
            Binding("p", "pick",      "Pick for Me",  show=True),
            Binding("d", "mark_done", "Done",         show=True),
            Binding("e", "set_prog",  "Set Progress", show=True),
            Binding("x", "delete",    "Delete",       show=True),
            Binding("q", "quit",      "Quit",         show=True),
        ]

        def __init__(self):
            super().__init__()
            self._data = load_data()

        # ── Helpers ───────────────────────────────────────────────────────────

        def _ordered(self) -> list:
            tuts = self._data["tutorials"]
            return [t for t in tuts if t["status"] != "done"] + \
                   [t for t in tuts if t["status"] == "done"]

        def _selected(self) -> Optional[dict]:
            ordered = self._ordered()
            if not ordered:
                return None
            idx = self.query_one("#tbl", DataTable).cursor_row
            return ordered[idx] if 0 <= idx < len(ordered) else None

        # ── Layout ────────────────────────────────────────────────────────────

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Static("", id="stats-bar")
            with Container(id="empty-state"):
                yield Static("No tutorials yet")
                yield Button("Add Tutorial", variant="primary", id="btn-empty-add")
            yield DataTable(id="tbl", cursor_type="row")
            yield Footer()

        def on_mount(self) -> None:
            tbl = self.query_one("#tbl", DataTable)
            tbl.add_columns(" ", "Title", "Topic", "Duration", "Progress", "URL")
            self._refresh()

        # ── Render ────────────────────────────────────────────────────────────

        def _refresh(self) -> None:
            self._data = load_data()
            has_tuts = len(self._data["tutorials"]) > 0
            self.query_one("#empty-state").display = not has_tuts
            self.query_one("#tbl").display = has_tuts
            self._render_stats()
            self._render_table()

        def _render_stats(self) -> None:
            st         = self._data["settings"].get("streak", {})
            goal       = self._data["settings"].get("daily_goal_mins", 60)
            done_today = sum(
                t.get("duration_mins", 0) for t in self._data["tutorials"]
                if t.get("completed_date") == today_str()
            )
            pct = min(100, int(done_today / goal * 100)) if goal else 0
            q   = sum(1 for t in self._data["tutorials"] if t["status"] != "done")
            self.query_one("#stats-bar", Static).update(
                f"Streak: {st.get('count', 0)}d  |  "
                f"Goal: {fmt_mins(done_today)}/{fmt_mins(goal)} ({pct}%)  |  "
                f"Queue: {q}"
            )

        def _render_table(self) -> None:
            tbl = self.query_one("#tbl", DataTable)
            tbl.clear()
            for t in self._ordered():
                icon  = STATUS_ICONS[t["status"]]
                title = t["title"][:40]
                topic = t.get("topic", "")
                dur   = fmt_mins(t.get("duration_mins", 0))
                pct   = t.get("progress", 0)
                bar   = "█" * (pct // 10) + "░" * (10 - pct // 10) + f" {pct}%"
                url = Text(t.get("url", "") or "")
                tbl.add_row(icon, title, topic, dur, bar, url)

        # ── Events ────────────────────────────────────────────────────────────

        def on_data_table_row_selected(self, e: DataTable.RowSelected) -> None:
            t = self._selected()
            if t and t.get("url"):
                import webbrowser
                webbrowser.open(t["url"])
                self.notify("Opened in browser", title=t["url"])
            else:
                self.notify("No URL for this tutorial", title="Open URL")

        def on_button_pressed(self, e: Button.Pressed) -> None:
            if e.button.id == "btn-empty-add":
                self.action_add()

        # ── Actions ───────────────────────────────────────────────────────────

        def action_add(self) -> None:
            def on_result(result) -> None:
                if not result:
                    return
                tid = str(uuid.uuid4())
                result.update({
                    "id":             tid,
                    "status":         "todo",
                    "progress":       0,
                    "added":          today_str(),
                    "completed_date": None,
                })
                self._data["tutorials"].append(result)
                save_data(self._data)
                self._refresh()
                self.notify(f"Added: {result['title']}", title="Tutorial Added")
            self.push_screen(AddModal(), on_result)

        def action_pick(self) -> None:
            t = smart_pick(self._data["tutorials"])
            if not t:
                self.notify("All done - queue is empty!", title="Pick")
                return
            ordered = self._ordered()
            try:
                idx = next(i for i, x in enumerate(ordered) if x["id"] == t["id"])
                self.query_one("#tbl", DataTable).move_cursor(row=idx)
            except StopIteration:
                pass
            self.notify(
                f"{t['title']}  ({fmt_mins(t.get('duration_mins', 0))} - {t['topic']})",
                title="Pick for Me",
            )

        def action_open_url(self) -> None:
            import webbrowser
            t = self._selected()
            if not t or not t.get("url"):
                self.notify("No URL for this tutorial", title="Open URL")
                return
            webbrowser.open(t["url"])
            self.notify(t["url"], title="Opened in browser")

        def action_mark_done(self) -> None:
            t = self._selected()
            if not t:
                return
            for x in self._data["tutorials"]:
                if x["id"] == t["id"]:
                    x.update({"status": "done", "progress": 100, "completed_date": today_str()})
                    update_streak(self._data)
                    save_data(self._data)
                    self._refresh()
                    self.notify(t["title"], title="Marked Done!")
                    return

        def action_delete(self) -> None:
            t = self._selected()
            if not t:
                return
            self._data["tutorials"] = [
                x for x in self._data["tutorials"] if x["id"] != t["id"]
            ]
            save_data(self._data)
            self._refresh()
            self.notify(t["title"], title="Deleted")

        def action_set_prog(self) -> None:
            t = self._selected()
            if not t:
                return
            def on_result(pct) -> None:
                if pct is None:
                    return
                pct = max(0, min(100, pct))
                for x in self._data["tutorials"]:
                    if x["id"] == t["id"]:
                        x["progress"] = pct
                        if pct >= 100: x["status"] = "done";        x["completed_date"] = today_str(); update_streak(self._data)
                        elif pct > 0:  x["status"] = "in_progress"
                        else:          x["status"] = "todo"
                        save_data(self._data)
                        self._refresh()
                        self.notify(f"{pct}%", title="Progress Updated")
                        return
            self.push_screen(ProgModal(t["title"]), on_result)

    TQApp().run()

# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()