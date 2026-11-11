# DayFlow

**Version 1.5 — Your day, under control.**

## What's new in 1.5
- Fixed accent-theme refresh so the sidebar, navigation, footer and page content all update together.
- Moved the navigation rail to the right to create a wider, uninterrupted working canvas.
- Removed expensive spotlight image regeneration during window resizing for smoother window movement.
- Preserved tasks, notes, habits, goals, focus sessions and settings.
- Existing tasks, notes, habits, goals, focus sessions and settings are preserved.

## Previous release highlights
- **1.4.8:** Added the accent-colour spotlight and persistent Adrian Vale / Ko-fi shortcuts.
- **1.4.7:** Added persistent creator shortcuts to the desktop sidebar.
- **1.4.6:** Restored six accent choices and refined panel spacing and Windows icon handling.


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
