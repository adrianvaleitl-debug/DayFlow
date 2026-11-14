# Daymark 2.2 2.0 — Adrian Vale

A calm personal planning workspace, rebuilt with React, TypeScript and Tauri 2. The previous Python UI and application implementation are not included.

## Core features
- Tasks with due dates, priorities, completion and search
- Monthly calendar view for upcoming tasks
- Notes with tags and longer-form content
- Habit list with daily check-ins and consecutive-day streaks
- Goals with target dates, categories and progress
- Focus timer with 15, 25, 45 and 60 minute sessions
- Completed focus-session history
- Weekly review for tasks completed, focus minutes and habit check-ins, plus a saved reflection
- Classy blue and Royal gold appearance themes
- Full JSON backup export, CSV export and a confirmed local-data deletion option

## Run locally
```bash
npm install
npm run tauri dev
```

## Test and build
```bash
npm test
npm run build
npm run tauri build
```

## Data and limitations
Tasks, notes, habits, goals and focus history are saved in local app storage on this device. No hosted account or cloud sync is required. Export a backup regularly. Daymark reminders are not guaranteed; use a separate dependable reminder for critical commitments.

## Technology
React 18 · TypeScript · Vite · Tauri 2 · Rust

Website: https://adrianvaleitl-debug.github.io/Adrian-Vales-Projects/

## Daymark 2.2.0

- Added a first-launch reminder reliability and data-loss acknowledgement.
- Renamed the product Daymark and introduced a matching royal-gold D app icon.
