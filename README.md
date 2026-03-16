# 📚 tq — Tutorial Queue

> Never lose a tutorial in a forgotten browser tab again.

`tq` is a smart CLI + TUI app that helps you track, schedule, and actually finish the tutorials you save. It lives in your terminal, works on every platform, and takes seconds to install.

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

- **📥 Queue management** — add tutorials with title, URL, topic, and duration
- **🎯 Smart Pick** — `tq pick` chooses your next best tutorial automatically
- **📊 Progress tracking** — track % completion per tutorial
- **📅 Scheduling** — assign tutorials to specific days
- **🔥 Streaks & daily goals** — build a learning habit with streaks and a daily minute goal
- **🖥️ Full TUI dashboard** — a clean interactive terminal UI
- **⚡ Fast CLI** — one-liners for everything when you don't need the TUI

---

## 🚀 Installation

### Quick install (recommended)

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/yohamza/tq/main/install.sh | bash
```

> After install, restart your terminal or run `source ~/.zshrc` (or `source ~/.bashrc`) for the `tq` command to be available.

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/yohamza/tq/main/install.ps1 | iex
```

> After install, open a new terminal window for the `tq` command to be available.

### Manual install

```bash
pip install typer rich textual
git clone https://github.com/yohamza/tq.git
cd tq
python tq.py
```

---

## 🖥️ TUI Mode

Launch the full interactive dashboard:

```bash
tq
```

```
┌─ tq - Tutorial Queue ───────────────────────────────────────────┐
│ Streak: 3d  |  Goal: 30m/60m (50%)  |  Queue: 4               │
│                                                                 │
│   Title              Topic    Duration  Progress     URL        │
│ ▶ React Hooks        React    45m       ████░░ 40%   Open       │
│ ○ CSS Grid           CSS      30m       ░░░░░░  0%   Open       │
│ ○ Python Basics      Python   2h        ░░░░░░  0%              │
│ ○ Node.js APIs       Node     1h 15m    ░░░░░░  0%   Open       │
│ ✅ TypeScript 101    TS       1h        ██████ 100%  Open       │
│                                                                 │
│ A Add  O Open URL  P Pick  D Done  E Progress  X Delete  Q Quit │
└─────────────────────────────────────────────────────────────────┘
```

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate the list |
| `A` | Add a new tutorial |
| `O` | Open selected tutorial's URL in browser |
| `D` | Mark selected as Done |
| `E` | Set progress % |
| `P` | Smart pick — best next tutorial |
| `X` | Delete selected tutorial |
| `Q` | Quit |

Double-clicking a row also opens its URL in your default browser.

---

## ⌨️ CLI Commands

### Add a tutorial
```bash
tq add "React Hooks Deep Dive"
tq add "CSS Grid Guide" --url https://youtube.com/... --duration 30 --topic CSS
tq add "Python Basics" -d 120 -t Python --schedule today
```

### View your queue
```bash
tq list                        # full queue
tq list --topic React          # filter by topic
tq list --status in_progress   # filter by status
```

### Smart pick
```bash
tq pick
# Resumes in-progress → picks scheduled for today → picks shortest
```

### Track progress
```bash
tq progress abc123 60          # set to 60%
tq done abc123                 # mark as 100% complete
```

### Schedule
```bash
tq schedule abc123 today
tq schedule abc123 tomorrow
tq schedule abc123 2026-04-01
```

### Goals & stats
```bash
tq goal 45                     # set daily goal to 45 minutes
tq stats                       # view streak, totals, and daily progress
```

---

## 🧠 Smart Pick Logic

`tq pick` selects your next tutorial using this priority:

1. **Resume** — the in-progress tutorial with the highest completion %
2. **Scheduled** — tutorials due today, shortest first (quick wins)
3. **Queue** — the shortest unstarted tutorial

---

## 💾 Data Storage

All data is stored locally as plain JSON:

| Platform | Path |
|----------|------|
| macOS / Linux | `~/.config/tq/data.json` |
| Windows | `~/.config/tq/data.json` |

You can back it up, sync it with Dropbox / iCloud, or edit it manually.

---

## 🗂️ Project Structure

```
tq/
├── tq.py                        # main app (CLI + TUI)
├── install.sh                   # macOS/Linux installer
├── install.ps1                  # Windows installer
├── README.md
└── .github/
    └── workflows/
        └── build.yml            # auto-builds binaries on release
```

---

## 🔨 Development

```bash
# Clone
git clone https://github.com/yohamza/tq.git
cd tq

# Install dependencies
pip install typer rich textual

# Run locally
python tq.py
```

---

## 📦 Releasing a new version

```bash
git add .
git commit -m "feat: my new feature"
git tag v1.1.0
git push && git push --tags
```

GitHub Actions will automatically build binaries for all 3 platforms and attach them to the release.

---

## 🛣️ Roadmap

- [ ] `tq update` — self-update from GitHub Releases
- [ ] `tq import <url>` — auto-fetch title & duration from YouTube
- [ ] Weekly review mode
- [ ] Export learning log to Markdown
- [ ] Browser extension to send tabs directly to queue

---

## 📄 License

MIT — do whatever you want with it.
