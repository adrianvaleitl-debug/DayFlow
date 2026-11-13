# DayFlow

**Version 1.7 — Your day, under control.**

## What's new in 1.7
- Added a confirmed Settings action to delete the local DayFlow data file.
- Added a browser-storage choice banner to the website, with an option not to save appearance preferences.

## What's new in 1.6
- Added a required first-launch legal and liability acknowledgement before app access.
- Added a Legal & Important Information section to Settings so the notice can be reopened.
- Clarified reminder limitations, critical appointment safeguards, local data storage and backups.
- Existing tasks, notes, habits, goals, focus sessions and settings are preserved.

## Legal and data notice

DayFlow is a personal productivity and planning tool, not a professional scheduling, emergency alert, medical, mental-health, legal, financial or other advisory service. In-app reminders are not guaranteed and depend on the app and device being available; do not rely on DayFlow as the sole reminder for critical commitments. Personal planning data is stored locally, and users are responsible for keeping separate backups. DayFlow does not guarantee productivity or other outcomes. To the fullest extent permitted by law, Adrian Vale and the people involved in creating or maintaining DayFlow exclude liability for losses arising from use of or reliance on the app, including data loss and missed reminders. This does not exclude liability or consumer rights that cannot legally be excluded.

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
