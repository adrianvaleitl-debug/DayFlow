# DayFlow

**Version 1.3.0 — Your day, under control.**

## What's new in 1.3.0
- **Weekly Review:** see completed tasks, focus sessions, focus time and habit check-ins over the last seven days.
- **Habit streaks:** current daily streaks and lifetime check-in totals are visible on each habit card.
- **Focus history:** completed focus sessions are saved locally and included in the weekly review.
- Existing task, note, habit and goal data remains compatible; the new history starts accumulating from this version.


**Your day, under control.**

DayFlow is a Windows desktop productivity workspace for planning your day, building routines, capturing ideas and making steady progress on your goals. Version 1.3.0 adds a Weekly Review, habit streaks and focus-session history to the redesigned personal planning workspace.

## Features

- **Overview dashboard** — open tasks, today's priorities and quick capture
- **Task manager** — due dates, priorities, completion and delete controls
- **Upcoming calendar** — a date-sorted view of future tasks
- **Notes** — save and revisit ideas and longer notes
- **Habit tracker** — daily check-ins, current streaks and lifetime history
- **Weekly Review** — completed tasks, focus sessions, focus time and habit check-ins from the last seven days
- **Focus history** — completed sessions are stored locally and included in weekly progress
- **Goals** — track progress in 10% increments
- **Focus timer** — configurable focus sessions
- **First-run tutorial** — guided introduction when DayFlow opens for the first time
- **Personalisation** — dark, light or system appearance, five font choices and bold-text setting
- **Automatic update checks** — checks GitHub Releases and offers the latest Windows installer
- **Local-first storage** — your tasks, notes and routines stay on your computer

## Download

Visit the [DayFlow website](https://adrianvaleitl-debug.github.io/DayFlow/) or the [latest GitHub release](https://github.com/adrianvaleitl-debug/DayFlow/releases/latest).

## Run from source

1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Run:

   ```powershell
   py -m pip install -r requirements.txt
   py dayflow.py
   ```

## Build locally

```powershell
py -m pip install -r requirements.txt
py -m PyInstaller --noconfirm --clean --onefile --windowed --name DayFlow dayflow.py
```

The executable is created at `dist/DayFlow.exe`.

## Release process

Updating the `VERSION` file and pushing to `main` runs the Windows release workflow. It builds the executable, packages it with Inno Setup and publishes a versioned installer to GitHub Releases. The app checks that release feed for updates.

## Data and privacy

DayFlow stores its data locally in `%APPDATA%\DayFlow\dayflow_data.json`. It does not require an account or upload personal tasks and notes to a server. Update checks contact the public GitHub Releases API.

## Project links

- **Adrian Vale — personal website:** https://adrianvaleitl-debug.github.io/

- Website: https://adrianvaleitl-debug.github.io/DayFlow/
- GitHub: https://github.com/adrianvaleitl-debug/DayFlow
- Creator: [Adrian Vale](https://github.com/adrianvaleitl-debug)
- Portfolio: https://adrianvaleitl-debug.github.io/
