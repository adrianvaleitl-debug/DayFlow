import json
import os
import sys
import ctypes
import time
import threading
import urllib.request
import webbrowser
import subprocess
import tempfile
import winreg
import tkinter as tk
from tkinter import messagebox
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    import customtkinter as ctk
except ImportError:
    raise SystemExit("DayFlow needs CustomTkinter. Run: pip install -r requirements.txt")

APP_NAME = "DayFlow"
APP_VERSION = "1.3.0"
GITHUB_RELEASES_API = "https://api.github.com/repos/adrianvaleitl-debug/DayFlow/releases/latest"
DATA_DIR = Path(os.getenv("APPDATA", str(Path.home()))) / "DayFlow"
DATA_FILE = DATA_DIR / "dayflow_data.json"

DEFAULT_DATA = {
    "tasks": [], "notes": [], "habits": [], "goals": [], "focus_sessions": [],
    "settings": {"appearance": "dark", "accent": "blue", "focus_minutes": 25, "font": "Segoe UI", "bold": True, "tutorial_seen": False, "auto_updates": True}
}

def load_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DATA_FILE.exists():
        try:
            loaded = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            data = DEFAULT_DATA.copy()
            data.update(loaded)
            for key in ("tasks", "notes", "habits", "goals", "focus_sessions"):
                if not isinstance(data.get(key), list):
                    data[key] = []
            if not isinstance(data.get("settings"), dict):
                data["settings"] = DEFAULT_DATA["settings"].copy()
            else:
                settings = DEFAULT_DATA["settings"].copy()
                settings.update(data["settings"])
                if "tutorial_seen" not in data["settings"]:
                    settings["tutorial_seen"] = True
                data["settings"] = settings
            return data
        except (OSError, json.JSONDecodeError):
            pass
    return json.loads(json.dumps(DEFAULT_DATA))

class DayFlow(ctk.CTk):
    def __init__(self):
        self.data = load_data()
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AdrianVale.DayFlow")
        except Exception:
            pass
        ctk.set_appearance_mode(self.data["settings"].get("appearance", "dark"))
        ctk.set_default_color_theme("blue")
        super().__init__()
        self.title(f"{APP_NAME}  •  Your day, under control")
        try:
            icon = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "dayflow.ico"
            if icon.exists():
                self.iconbitmap(default=str(icon))
                png_icon = icon.with_suffix(".png")
                if png_icon.exists():
                    self._window_icon_photo = tk.PhotoImage(file=str(png_icon))
                    self.iconphoto(True, self._window_icon_photo)
        except Exception:
            pass
        self.geometry("1240x820")
        self.minsize(980, 680)
        self.configure(fg_color=("#F3F5F8", "#11151D"))
        self.timer_running = False
        self.timer_end = None
        self.timer_job = None
        self.active_page = "Overview"
        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self.build_shell()
        self.show_page("Overview")
        if not self.data["settings"].get("tutorial_seen", False):
            self.after(500, self.show_tutorial)
        self.after(15000, self.check_reminders)
        if self.data["settings"].get("auto_updates", True):
            self.after(2500, lambda: self.check_updates(silent=True))

    def ui_font(self, size=12, force_bold=False):
        settings = self.data.get("settings", {})
        return ctk.CTkFont(family=settings.get("font", "Segoe UI"), size=size,
                           weight="bold" if force_bold or settings.get("bold", True) else "normal")

    def save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")

    def build_shell(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        topbar = ctk.CTkFrame(self, height=66, corner_radius=0, fg_color=("#FFFFFF", "#171D28"))
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_propagate(False)
        ctk.CTkLabel(topbar, text="◈  DAYFLOW", font=self.ui_font(21, True), text_color=("#172235", "#F4F7FC")).pack(side="left", padx=28)
        ctk.CTkLabel(topbar, text="YOUR PERSONAL SPACE  /  TODAY", font=ctk.CTkFont(size=10, weight="bold"), text_color=("#718096", "#8492A6")).pack(side="left", padx=18)
        ctk.CTkLabel(topbar, text=date.today().strftime("%A  ·  %d %B %Y"), font=ctk.CTkFont(size=11, weight="bold"), text_color=("#718096", "#A2AFC2")).pack(side="right", padx=28)
        self.main = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main.grid(row=1, column=0, sticky="nsew", padx=34, pady=(24, 10))
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)
        self.nav_dock = ctk.CTkFrame(self, height=72, corner_radius=22, fg_color=("#E8EDF5", "#1A2433"), border_width=1, border_color=("#DCE4EF", "#2B3A50"))
        self.nav_dock.grid(row=2, column=0, sticky="ew", padx=50, pady=(0, 16))
        self.nav_dock.grid_propagate(False)
        self.nav_buttons = {}
        for name, glyph in [("Overview","⌂"),("Tasks","✓"),("Calendar","▦"),("Notes","▤"),("Habits","↗"),("Goals","◎"),("Focus","◷"),("Weekly Review","▥"),("Settings","⚙")]:
            b = ctk.CTkButton(self.nav_dock, text=f"{glyph}  {name}", height=43, corner_radius=14,
                fg_color="transparent", hover_color=("#D7E5F7", "#263B58"), text_color=("#344054", "#C7D0DE"),
                font=self.ui_font(12, True), command=lambda n=name: self.show_page(n))
            b.pack(side="left", expand=True, fill="both", padx=4, pady=6)
            self.nav_buttons[name] = b

    def clear_main(self):
        for child in self.main.winfo_children():
            child.destroy()

    def header(self, title, subtitle):
        top = ctk.CTkFrame(self.main, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        ctk.CTkLabel(top, text=title, font=self.ui_font(28, True)).pack(anchor="w")
        ctk.CTkLabel(top, text=subtitle, font=ctk.CTkFont(size=12), text_color=("gray55", "gray65")).pack(anchor="w", pady=(4, 0))
        return top

    def body(self):
        body = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        return body

    def panel(self, parent, title=None):
        frame = ctk.CTkFrame(parent, corner_radius=16, fg_color=("white", "#1A2230"), border_width=1, border_color=("#E4E9F0", "#263244"))
        if title:
            ctk.CTkLabel(frame, text=title, font=self.ui_font(15, True)).pack(anchor="w", padx=18, pady=(16, 10))
        return frame

    def show_page(self, name):
        self.active_page = name
        for n, b in self.nav_buttons.items():
            b.configure(fg_color=("#D7E5F7", "#263B58") if n == name else "transparent",
                        text_color=("#1456A0", "#8FC0FF") if n == name else ("#344054", "#C7D0DE"))
        self.clear_main()
        getattr(self, f"page_{name.lower().replace(chr(32), chr(95))}")()
        if name == "Focus" and self.timer_running:
            self.tick_timer()

    def page_overview(self):
        self.header("Good " + ("morning" if datetime.now().hour < 12 else "afternoon" if datetime.now().hour < 18 else "evening") + ".", date.today().strftime("%A, %d %B %Y"))
        body = self.body()
        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")
        pending = [t for t in self.data["tasks"] if not t.get("done")]
        today = [t for t in pending if t.get("due") == date.today().isoformat()]
        for title, value, hint in [("OPEN TASKS", len(pending), "Things still to do"), ("DUE TODAY", len(today), "Keep today on track"), ("HABITS", len(self.data["habits"]), "Routines you're building")]:
            card = self.panel(top)
            card.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=4)
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=10, weight="bold"), text_color=("gray55","gray65")).pack(anchor="w", padx=18, pady=(16, 3))
            ctk.CTkLabel(card, text=str(value), font=self.ui_font(30, True)).pack(anchor="w", padx=18)
            ctk.CTkLabel(card, text=hint, font=ctk.CTkFont(size=11), text_color=("gray55","gray65")).pack(anchor="w", padx=18, pady=(0, 16))
        lower = ctk.CTkFrame(body, fg_color="transparent")
        lower.pack(fill="both", expand=True, pady=(16, 0))
        left = self.panel(lower, "Today's priorities")
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))
        for task in today[:7]:
            ctk.CTkLabel(left, text="•  " + task["title"], anchor="w", font=ctk.CTkFont(size=12)).pack(fill="x", padx=18, pady=7)
        if not today:
            ctk.CTkLabel(left, text="Nothing due today. A good chance to get ahead.", text_color=("gray55","gray65")).pack(anchor="w", padx=18, pady=(0, 18))
        right = self.panel(lower, "Quick capture")
        right.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(right, text="Get it out of your head and into DayFlow.", text_color=("gray55","gray65"), wraplength=280).pack(anchor="w", padx=18, pady=(0, 12))
        self.quick_entry = ctk.CTkEntry(right, placeholder_text="Add a task...")
        self.quick_entry.pack(fill="x", padx=18, pady=5)
        ctk.CTkButton(right, text="Add task", command=self.quick_add).pack(anchor="w", padx=18, pady=(6, 18))

    def quick_add(self):
        title = self.quick_entry.get().strip()
        if title:
            self.data["tasks"].append({"id": str(time.time_ns()), "title": title, "due": date.today().isoformat(), "priority": "Normal", "done": False, "remind": ""})
            self.save()
            self.show_page("Overview")

    def page_tasks(self):
        self.header("Tasks", "Capture it, prioritise it, and move it forward.")
        body = self.body()
        form = self.panel(body, "Add a task"); form.pack(fill="x", pady=(0, 14))
        row = ctk.CTkFrame(form, fg_color="transparent"); row.pack(fill="x", padx=16, pady=(0, 16))
        title = ctk.CTkEntry(row, placeholder_text="What needs doing?", height=38); title.pack(side="left", fill="x", expand=True, padx=(0, 8))
        due = ctk.CTkEntry(row, width=125, placeholder_text="YYYY-MM-DD"); due.insert(0, date.today().isoformat()); due.pack(side="left", padx=5)
        priority = ctk.CTkOptionMenu(row, values=["Low","Normal","High"]); priority.pack(side="left", padx=5)
        def add():
            if title.get().strip():
                due_value = due.get().strip()
                try: datetime.strptime(due_value, "%Y-%m-%d")
                except ValueError: messagebox.showerror("Invalid date", "Use YYYY-MM-DD for the due date."); return
                self.data["tasks"].append({"id":str(time.time_ns()),"title":title.get().strip(),"due":due_value,"priority":priority.get(),"done":False,"remind":""})
                self.save(); self.show_page("Tasks")
        ctk.CTkButton(row, text="Add task", command=add, width=100).pack(side="left", padx=(5,0))
        listing = self.panel(body, "Your task list"); listing.pack(fill="x")
        tasks = sorted(self.data["tasks"], key=lambda x:(x.get("done",False), x.get("due","9999"), x.get("priority")!="High"))
        if not tasks: ctk.CTkLabel(listing,text="No tasks yet. Add your first one above.",text_color=("gray55","gray65")).pack(anchor="w",padx=18,pady=(0,18))
        for task in tasks:
            line = ctk.CTkFrame(listing, fg_color="transparent"); line.pack(fill="x", padx=14, pady=5)
            done = ctk.BooleanVar(value=task.get("done",False))
            def toggle(t=task,v=done):
                t["done"]=v.get(); t["completed_at"]=date.today().isoformat() if v.get() else ""; self.save(); self.show_page("Tasks")
            ctk.CTkCheckBox(line,text=task["title"],variable=done,command=toggle,font=ctk.CTkFont(size=12),text_color=("gray55","gray65") if task.get("done") else ("#202939","#F2F4F7")).pack(side="left",fill="x",expand=True)
            ctk.CTkLabel(line,text=f'{task.get("due","No date")}  ·  {task.get("priority","Normal")}',font=ctk.CTkFont(size=10),text_color=("gray55","gray65")).pack(side="left",padx=10)
            ctk.CTkButton(line,text="×",width=30,fg_color="transparent",hover_color=("#FEE4E2","#542B2B"),text_color=("#B42318","#FDA29B"),command=lambda t=task:self.delete_item("tasks",t,"Tasks")).pack(side="right")

    def page_calendar(self):
        self.header("Calendar", "A simple view of what's coming up.")
        body=self.body()
        month=date.today().strftime("%B %Y")
        card=self.panel(body,month); card.pack(fill="x")
        ctk.CTkLabel(card,text="Upcoming tasks",font=ctk.CTkFont(size=13,weight="bold")).pack(anchor="w",padx=18,pady=(0,8))
        upcoming=sorted([t for t in self.data["tasks"] if not t.get("done") and t.get("due")],key=lambda x:x["due"])
        for t in upcoming[:30]:
            ctk.CTkLabel(card,text=f'{t["due"]}     {t["title"]}',anchor="w").pack(fill="x",padx=18,pady=5)
        if not upcoming: ctk.CTkLabel(card,text="No upcoming tasks. Add a due date to a task to see it here.",text_color=("gray55","gray65")).pack(anchor="w",padx=18,pady=(0,18))

    def page_notes(self):
        self.header("Notes", "Ideas, thoughts, and everything you don't want to forget.")
        body=self.body()
        form=self.panel(body,"New note"); form.pack(fill="x",pady=(0,14))
        title=ctk.CTkEntry(form,placeholder_text="Note title"); title.pack(fill="x",padx=16,pady=(0,8))
        content=ctk.CTkTextbox(form,height=110); content.pack(fill="x",padx=16,pady=(0,8))
        def add():
            if title.get().strip() or content.get("1.0","end").strip():
                self.data["notes"].insert(0,{"id":str(time.time_ns()),"title":title.get().strip() or "Untitled note","content":content.get("1.0","end").strip(),"updated":datetime.now().strftime("%d %b %Y, %H:%M")})
                self.save(); self.show_page("Notes")
        ctk.CTkButton(form,text="Save note",command=add).pack(anchor="e",padx=16,pady=(0,14))
        for note in self.data["notes"]:
            card=self.panel(body,note.get("title","Untitled")); card.pack(fill="x",pady=6)
            ctk.CTkLabel(card,text=note.get("content",""),justify="left",anchor="w",wraplength=850).pack(fill="x",padx=18,pady=(0,8))
            ctk.CTkLabel(card,text=note.get("updated",""),text_color=("gray55","gray65"),font=ctk.CTkFont(size=10)).pack(anchor="w",padx=18,pady=(0,12))

    def page_habits(self):
        self.header("Habits", "Small actions, repeated consistently, make a difference.")
        body=self.body()
        form=self.panel(body,"Build a habit"); form.pack(fill="x",pady=(0,14))
        entry=ctk.CTkEntry(form,placeholder_text="e.g. Read for 10 minutes"); entry.pack(side="left",fill="x",expand=True,padx=16,pady=16)
        def add():
            if entry.get().strip():
                self.data["habits"].append({"id":str(time.time_ns()),"name":entry.get().strip(),"history":[]}); self.save(); self.show_page("Habits")
        ctk.CTkButton(form,text="Add habit",command=add).pack(side="left",padx=(0,16))
        for habit in self.data["habits"]:
            dates=set(habit.get("history",[])); streak=0; cursor=date.today()
            while cursor.isoformat() in dates:
                streak+=1; cursor-=timedelta(days=1)
            card=self.panel(body,habit["name"]); card.pack(fill="x",pady=6)
            ctk.CTkLabel(card,text=f"{streak}-day current streak  ·  {len(dates)} total check-ins",text_color=("gray55","gray65")).pack(anchor="w",padx=18,pady=(0,8))
            completed=date.today().isoformat() in habit.get("history",[])
            def mark(h=habit):
                h.setdefault("history",[])
                today=date.today().isoformat()
                if today in h["history"]: h["history"].remove(today)
                else: h["history"].append(today)
                self.save(); self.show_page("Habits")
            ctk.CTkButton(card,text="✓ Completed today" if completed else "Mark complete today",command=mark,
                fg_color="#16865A" if completed else None).pack(side="left",padx=18,pady=(0,14))
            ctk.CTkLabel(card,text=f'{len(habit.get("history",[]))} total check-ins',text_color=("gray55","gray65")).pack(side="left",padx=12,pady=(0,14))
            ctk.CTkButton(card,text="Remove",width=70,fg_color="transparent",text_color=("#B42318","#FDA29B"),command=lambda h=habit:self.delete_item("habits",h,"Habits")).pack(side="right",padx=14,pady=(0,14))

    def page_goals(self):
        self.header("Goals", "Turn bigger ambitions into visible progress.")
        body=self.body()
        form=self.panel(body,"Create a goal"); form.pack(fill="x",pady=(0,14))
        entry=ctk.CTkEntry(form,placeholder_text="What do you want to achieve?"); entry.pack(side="left",fill="x",expand=True,padx=16,pady=16)
        def add():
            if entry.get().strip():
                self.data["goals"].append({"id":str(time.time_ns()),"name":entry.get().strip(),"progress":0}); self.save(); self.show_page("Goals")
        ctk.CTkButton(form,text="Add goal",command=add).pack(side="left",padx=(0,16))
        for goal in self.data["goals"]:
            card=self.panel(body,goal["name"]); card.pack(fill="x",pady=6)
            value=goal.get("progress",0)
            ctk.CTkProgressBar(card).pack(fill="x",padx=18,pady=(0,5))
            bar=card.winfo_children()[-1]; bar.set(max(0,min(100,value))/100)
            controls=ctk.CTkFrame(card,fg_color="transparent"); controls.pack(fill="x",padx=18,pady=(0,14))
            ctk.CTkLabel(controls,text=f"{value}% complete").pack(side="left")
            def change(delta,g=goal):
                g["progress"]=max(0,min(100,g.get("progress",0)+delta)); self.save(); self.show_page("Goals")
            ctk.CTkButton(controls,text="+10%",width=65,command=lambda g=goal:change(10,g)).pack(side="right",padx=4)
            ctk.CTkButton(controls,text="-10%",width=65,fg_color="transparent",command=lambda g=goal:change(-10,g)).pack(side="right",padx=4)

    def page_focus(self):
        self.header("Focus", "Give one thing your full attention.")
        body=self.body()
        card=self.panel(body,"Focus session"); card.pack(fill="x")
        minutes=int(self.data["settings"].get("focus_minutes",25))
        self.timer_label=ctk.CTkLabel(card,text=f"{minutes:02d}:00",font=self.ui_font(64, True))
        self.timer_label.pack(pady=(18,8))
        ctk.CTkLabel(card,text="Work in one focused block. Take a break when the timer ends.",text_color=("gray55","gray65")).pack(pady=(0,16))
        controls=ctk.CTkFrame(card,fg_color="transparent"); controls.pack(pady=(0,20))
        ctk.CTkButton(controls,text="Start",command=self.start_timer).pack(side="left",padx=5)
        ctk.CTkButton(controls,text="Reset",fg_color="transparent",command=self.reset_timer).pack(side="left",padx=5)
        ctk.CTkLabel(card,text="Session length can be changed in Settings.",text_color=("gray55","gray65"),font=ctk.CTkFont(size=10)).pack(pady=(0,16))

    def start_timer(self):
        if self.timer_running: return
        self.timer_running=True
        if not self.timer_end: self.timer_end=time.time()+int(self.data["settings"].get("focus_minutes",25))*60
        self.tick_timer()

    def tick_timer(self):
        if not self.timer_running or self.active_page!="Focus": return
        remaining=max(0,int(self.timer_end-time.time()))
        self.timer_label.configure(text=f"{remaining//60:02d}:{remaining%60:02d}")
        if remaining<=0:
            self.timer_running=False; self.timer_end=None
            self.data.setdefault("focus_sessions", []).append({"date":date.today().isoformat(),"minutes":int(self.data["settings"].get("focus_minutes",25))})
            self.save()
            messagebox.showinfo("Focus complete","Nice work. Your focus session is complete.")
            return
        self.timer_job=self.after(500,self.tick_timer)

    def reset_timer(self):
        self.timer_running=False; self.timer_end=None
        if self.timer_job:
            try: self.after_cancel(self.timer_job)
            except tk.TclError: pass
        if self.active_page=="Focus":
            self.timer_label.configure(text=f'{int(self.data["settings"].get("focus_minutes",25)):02d}:00')

    def show_tutorial(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Welcome to DayFlow")
        dialog.geometry("560x440")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        ctk.CTkLabel(dialog, text="Welcome to DayFlow", font=self.ui_font(26, True)).pack(anchor="w", padx=28, pady=(28, 6))
        ctk.CTkLabel(dialog, text="A calmer way to get your day under control.", font=self.ui_font(13)).pack(anchor="w", padx=28, pady=(0, 20))
        for heading, detail in [
            ("1. Plan your day", "Add tasks, choose a priority and set a due date."),
            ("2. Build your routines", "Track habits and keep your goals moving."),
            ("3. Make space to focus", "Use the focus timer to work in distraction-free blocks."),
            ("4. Keep everything together", "Save notes and see upcoming work in your calendar.")
        ]:
            row = ctk.CTkFrame(dialog, fg_color=("gray92", "#202A39"), corner_radius=12)
            row.pack(fill="x", padx=24, pady=5)
            ctk.CTkLabel(row, text=heading, font=self.ui_font(13, True)).pack(anchor="w", padx=14, pady=(10, 2))
            ctk.CTkLabel(row, text=detail, font=self.ui_font(11), text_color=("gray40", "gray70")).pack(anchor="w", padx=14, pady=(0, 10))
        def finish():
            self.data["settings"]["tutorial_seen"] = True
            self.save()
            dialog.destroy()
        dialog.protocol("WM_DELETE_WINDOW", finish)
        ctk.CTkButton(dialog, text="Let's get started", command=finish, height=40).pack(anchor="e", padx=24, pady=18)

    def check_updates(self, silent=False):
        def worker():
            try:
                request = urllib.request.Request(GITHUB_RELEASES_API, headers={"User-Agent": "DayFlow-Updater"})
                with urllib.request.urlopen(request, timeout=8) as response:
                    release = json.loads(response.read().decode("utf-8"))
                latest = str(release.get("tag_name", "")).lstrip("v")
                current = APP_VERSION.lstrip("v")
                def version_tuple(value):
                    return tuple(int(part) for part in value.split(".") if part.isdigit())
                if latest and version_tuple(latest) > version_tuple(current):
                    assets = release.get("assets", [])
                    expected_installer = f"dayflow-setup-{latest}.exe".lower()
                    installer = next((a for a in assets if a.get("name", "").lower() == expected_installer), None)
                    def prompt():
                        if messagebox.askyesno("DayFlow update", f"Version {latest} is available. Install it now?"):
                            if installer:
                                self.install_update(installer["browser_download_url"])
                            else:
                                webbrowser.open(release.get("html_url", "https://github.com/adrianvaleitl-debug/DayFlow/releases"))
                    self.after(0, prompt)
                elif not silent:
                    self.after(0, lambda: messagebox.showinfo("DayFlow", "You're already using the latest version."))
            except Exception as exc:
                if not silent:
                    self.after(0, lambda: messagebox.showwarning("Update check", f"Couldn't check for updates.\\n{exc}"))
        threading.Thread(target=worker, daemon=True).start()

    def install_update(self, url):
        def worker():
            try:
                update_dir = Path(tempfile.gettempdir()) / "AdrianVale" / "DayFlow"
                update_dir.mkdir(parents=True, exist_ok=True)
                path = update_dir / f"DayFlow-Setup-{APP_VERSION}-update.exe"
                request = urllib.request.Request(url, headers={"User-Agent": "DayFlow-Updater"})
                with urllib.request.urlopen(request, timeout=90) as response:
                    payload = response.read()
                if len(payload) < 100_000 or not payload.startswith(b"MZ"):
                    raise RuntimeError("The downloaded installer did not pass its Windows executable check. Download it from the GitHub releases page instead.")
                path.write_bytes(payload)
                subprocess.Popen(
                    [str(path), "/SILENT", "/CLOSEAPPLICATIONS", "/NORESTART", "/SUPPRESSMSGBOXES", "/SP-"],
                    shell=False, close_fds=True
                )
                self.after(1200, self.close_app)
            except Exception as exc:
                message = str(exc)
                self.after(0, lambda message=message: messagebox.showerror(
                    "DayFlow update failed",
                    f"The update could not be started. Your existing app and data have been left untouched.\n\n{message}"
                ))
        threading.Thread(target=worker, daemon=True).start()

    def page_weekly_review(self):
        self.header("Weekly review", "A useful snapshot of the last seven days.")
        body=self.body()
        since=(date.today()-timedelta(days=6)).isoformat()
        completed=[t for t in self.data["tasks"] if t.get("done") and t.get("completed_at","")>=since]
        sessions=[s for s in self.data.get("focus_sessions",[]) if s.get("date","")>=since]
        focus_minutes=sum(int(s.get("minutes",0)) for s in sessions)
        habit_checks=sum(1 for h in self.data["habits"] for day in h.get("history",[]) if day>=since)
        row=ctk.CTkFrame(body,fg_color="transparent");row.pack(fill="x")
        for title,value,hint in [("TASKS COMPLETED",len(completed),"Finished in the last 7 days"),("FOCUS SESSIONS",len(sessions),"Completed focus blocks"),("FOCUS TIME",f"{focus_minutes//60}h {focus_minutes%60}m","Time invested"),("HABIT CHECK-INS",habit_checks,"Routine progress")]:
            card=self.panel(row);card.pack(side="left",fill="x",expand=True,padx=5,pady=5)
            ctk.CTkLabel(card,text=title,font=self.ui_font(10,True),text_color=("gray55","gray65")).pack(anchor="w",padx=14,pady=(14,3))
            ctk.CTkLabel(card,text=str(value),font=self.ui_font(25,True)).pack(anchor="w",padx=14)
            ctk.CTkLabel(card,text=hint,font=self.ui_font(10),text_color=("gray55","gray65")).pack(anchor="w",padx=14,pady=(0,14))
        finished=self.panel(body,"Completed tasks");finished.pack(fill="x",pady=12)
        if completed:
            for task in sorted(completed,key=lambda t:t.get("completed_at",""),reverse=True)[:20]:
                ctk.CTkLabel(finished,text=f"✓  {task.get('title','Task')}   ·   {task.get('completed_at','')}",anchor="w").pack(fill="x",padx=18,pady=5)
        else:
            ctk.CTkLabel(finished,text="Completed tasks will appear here as you work through your week.",text_color=("gray55","gray65")).pack(anchor="w",padx=18,pady=(0,16))
        habits=self.panel(body,"Habit consistency");habits.pack(fill="x",pady=(0,12))
        for habit in self.data["habits"]:
            dates=set(habit.get("history",[])); streak=0; cursor=date.today()
            while cursor.isoformat() in dates:
                streak+=1; cursor-=timedelta(days=1)
            ctk.CTkLabel(habits,text=f"{habit.get('name','Habit')}   ·   {streak}-day current streak   ·   {sum(1 for x in dates if x>=since)} this week",anchor="w").pack(fill="x",padx=18,pady=6)

    def page_settings(self):
        self.header("Settings", "Make DayFlow feel like your workspace.")
        body=self.body()
        card=self.panel(body,"Appearance"); card.pack(fill="x",pady=(0,12))
        ctk.CTkLabel(card,text="Theme").pack(anchor="w",padx=18,pady=(0,5))
        appearance=ctk.CTkOptionMenu(card,values=["dark","light","system"],command=self.set_appearance)
        appearance.set(self.data["settings"].get("appearance","dark")); appearance.pack(anchor="w",padx=18,pady=(0,16))
        focus=self.panel(body,"Focus timer"); focus.pack(fill="x")
        ctk.CTkLabel(focus,text="Default focus session (minutes)").pack(anchor="w",padx=18,pady=(0,5))
        value=ctk.CTkEntry(focus,width=100); value.insert(0,str(self.data["settings"].get("focus_minutes",25))); value.pack(anchor="w",padx=18,pady=(0,8))
        def save_settings():
            try: n=max(1,min(180,int(value.get())))
            except ValueError: messagebox.showerror("Invalid value","Enter a number from 1 to 180."); return
            self.data["settings"]["focus_minutes"]=n; self.save(); messagebox.showinfo("Saved","Your settings have been saved.")
        ctk.CTkButton(focus,text="Save settings",command=save_settings).pack(anchor="w",padx=18,pady=(0,16))
        appearance_card=self.panel(body,"Personalisation"); appearance_card.pack(fill="x",pady=12)
        ctk.CTkLabel(appearance_card,text="Font").pack(anchor="w",padx=18,pady=(0,5))
        font_choice=ctk.CTkOptionMenu(appearance_card,values=["Segoe UI","Arial","Calibri","Georgia","Consolas"],
            command=lambda v:self.update_setting("font",v))
        font_choice.set(self.data["settings"].get("font","Segoe UI")); font_choice.pack(anchor="w",padx=18,pady=(0,10))
        bold_var=ctk.BooleanVar(value=self.data["settings"].get("bold",True))
        ctk.CTkSwitch(appearance_card,text="Bold text",variable=bold_var,
            command=lambda:self.update_setting("bold",bold_var.get())).pack(anchor="w",padx=18,pady=(0,14))
        updates_card=self.panel(body,"Updates & onboarding"); updates_card.pack(fill="x",pady=(0,12))
        auto_var=ctk.BooleanVar(value=self.data["settings"].get("auto_updates",True))
        ctk.CTkSwitch(updates_card,text="Automatically check for updates",variable=auto_var,
            command=lambda:self.update_setting("auto_updates",auto_var.get())).pack(anchor="w",padx=18,pady=(0,10))
        ctk.CTkButton(updates_card,text="Check for updates",command=lambda:self.check_updates(silent=False)).pack(anchor="w",padx=18,pady=(0,8))
        ctk.CTkButton(updates_card,text="Replay welcome tutorial",fg_color="transparent",
            command=self.show_tutorial).pack(anchor="w",padx=18,pady=(0,14))
        shortcuts=self.panel(body,"Windows shortcuts"); shortcuts.pack(fill="x",pady=12)
        ctk.CTkButton(shortcuts,text="Create desktop shortcut",command=lambda:self.create_shortcut(False)).pack(anchor="w",padx=18,pady=(12,6))
        ctk.CTkButton(shortcuts,text="Remove desktop shortcut",fg_color="transparent",command=lambda:self.create_shortcut(True)).pack(anchor="w",padx=18,pady=(0,8))
        startup_var=ctk.BooleanVar(value=self.data["settings"].get("launch_at_startup",False))
        ctk.CTkSwitch(shortcuts,text="Launch DayFlow when Windows starts",variable=startup_var,command=lambda:self.set_startup(startup_var.get())).pack(anchor="w",padx=18,pady=(0,14))
        info=self.panel(body,"Your data"); info.pack(fill="x",pady=12)
        ctk.CTkLabel(info,text=f"Your information is stored locally on this device:\n{DATA_FILE}",justify="left",text_color=("gray55","gray65")).pack(anchor="w",padx=18,pady=16)

    def update_setting(self, key, value):
        self.data["settings"][key] = value
        self.save()

    def desktop_folder(self):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
                value, _ = winreg.QueryValueEx(key, "Desktop")
            return Path(os.path.expandvars(value))
        except Exception:
            return Path.home() / "Desktop"

    def create_shortcut(self, remove=False):
        if sys.platform != "win32":
            messagebox.showinfo("Windows shortcut", "Desktop shortcuts are available in the Windows app.")
            return
        shortcut = self.desktop_folder() / "DayFlow.lnk"
        try:
            if remove:
                if shortcut.exists(): shortcut.unlink()
                messagebox.showinfo("Shortcut", "DayFlow desktop shortcut removed.")
                return
            target = Path(sys.executable)
            args = "" if getattr(sys, "frozen", False) else '"' + str(Path(__file__).resolve()) + '"'
            icon = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "dayflow.ico"
            shortcut.parent.mkdir(parents=True, exist_ok=True)
            ps = "$w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut(" + repr(str(shortcut)) + "); $s.TargetPath=" + repr(str(target)) + "; $s.Arguments=" + repr(args) + "; $s.WorkingDirectory=" + repr(str(target.parent)) + "; $s.Description='DayFlow personal planner'; $s.IconLocation=" + repr(str(icon) + ",0") + "; $s.Save()"
            encoded = __import__("base64").b64encode(ps.encode("utf-16le")).decode("ascii")
            subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded], check=True, capture_output=True)
            messagebox.showinfo("Shortcut", "DayFlow desktop shortcut created.")
        except Exception as exc:
            messagebox.showerror("Shortcut error", str(exc))

    def set_startup(self, enabled):
        if sys.platform != "win32":
            messagebox.showinfo("Windows startup", "This option is available in the Windows app.")
            return
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as key:
                if enabled:
                    command = '"' + sys.executable + '"' if getattr(sys, "frozen", False) else '"' + sys.executable + '" "' + str(Path(__file__).resolve()) + '"'
                    winreg.SetValueEx(key, "DayFlow", 0, winreg.REG_SZ, command)
                else:
                    try: winreg.DeleteValue(key, "DayFlow")
                    except FileNotFoundError: pass
            self.data["settings"]["launch_at_startup"] = bool(enabled)
            self.save()
        except Exception as exc:
            messagebox.showerror("Startup setting", str(exc))

    def set_appearance(self, value):
        self.data["settings"]["appearance"]=value; self.save(); ctk.set_appearance_mode(value)

    def delete_item(self, key, item, page):
        if messagebox.askyesno("Delete item","Are you sure you want to delete this?"):
            self.data[key]=[x for x in self.data[key] if x.get("id")!=item.get("id")]
            self.save(); self.show_page(page)

    def check_reminders(self):
        today=date.today().isoformat()
        due=[t for t in self.data["tasks"] if not t.get("done") and t.get("due")==today and t.get("reminded")!=today]
        if due and self.state() == "normal":
            for task in due: task["reminded"]=today
            self.save()
            messagebox.showinfo("DayFlow reminder",f"You have {len(due)} task(s) due today.")
        self.after(60000,self.check_reminders)

    def close_app(self):
        self.reset_timer()
        self.save()
        self.destroy()

if __name__ == "__main__":
    app = DayFlow()
    app.mainloop()
