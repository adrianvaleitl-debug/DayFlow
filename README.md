# DayFlow

**Your day, under control.**

DayFlow is a modern Windows desktop productivity app for planning your day, building routines, capturing ideas, and making steady progress on your goals.

## Current features

- **Overview dashboard** with open-task and due-today summaries
- **Task manager** with due dates, priorities, completion tracking, and deletion
- **Upcoming calendar list** for dated tasks
- **Notes** for quick capture and longer thoughts
- **Habit tracker** with daily check-ins and a running total
- **Goals** with adjustable progress tracking
- **Focus timer** with configurable session length
- **Appearance settings** for dark, light, or system theme
- **Local data storage** in your Windows AppData folder

## Run from source

1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Run:

   ```powershell
   py -m pip install -r requirements.txt
   py dayflow.py
   ```

## Build a Windows executable

```powershell
py -m pip install -r requirements.txt
py -m PyInstaller --noconfirm --clean --windowed --name DayFlow dayflow.py
```

The executable will be in `dist/DayFlow/DayFlow.exe`.

## Data and privacy

DayFlow stores its data locally in `%APPDATA%\DayFlow\dayflow_data.json`. It does not require an account or send your personal tasks and notes to a server.

## Project

Created by [Adrian Vale](https://github.com/adrianvaleitl-debug).

- GitHub: https://github.com/adrianvaleitl-debug/DayFlow
- Portfolio: https://adrianvaleitl-debug.github.io/
