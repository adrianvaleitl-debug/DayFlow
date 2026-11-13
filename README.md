# DayFlow 2.0 — clean rebuild

A calm personal planning workspace by Adrian Vale, rebuilt with React, TypeScript and Tauri 2. The previous application UI and Python application code are not carried forward.

## Core workspace
- Tasks with due dates, priority and completion tracking
- Calendar-style upcoming task view
- Notes with tags
- Habit list with daily check-ins
- Goals with target dates and next steps
- Focus timer with 15, 25, 45 and 60 minute sessions
- Weekly review with saved reflection
- Classy blue and Royal gold appearance modes

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

## Data and privacy
Your tasks, notes, habits and goals are saved in local app storage on this device. No hosted account is required and no data is uploaded. Export or back up your device data separately if you need to retain it.

## Stack
React 18 · TypeScript · Vite · Tauri 2 · Rust

Website: https://adrianvaleitl-debug.github.io/
