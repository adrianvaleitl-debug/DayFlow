import json
import os
import sys
import time
import threading
import tkinter as tk
from tkinter import messagebox
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    import customtkinter as ctk
except ImportError:
    raise SystemExit("DayFlow needs CustomTkinter. Run: pip install -r requirements.txt")

APP_NAME = "DayFlow"
APP_VERSION = "0.1.0"
DATA_DIR = Path(os.getenv("APPDATA", str(Path.home()))) / "DayFlow"
DATA_FILE = DATA_DIR / "dayflow_data.json"

DEFAULT_DATA = {
    "tasks": [], "notes": [], "habits": [], "goals": [],
    "settings": {"appearance": "dark", "accent": "blue", "focus_minutes": 25}
}

def load_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DATA_FILE.exists():
        try:
            loaded = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            data = DEFAULT_DATA.copy()
            data.update(loaded)
            for key in ("tasks", "notes", "habits", "goals"):
                if not isinstance(data.get(key), list):
                    data[key] = []
            if not isinstance(data.get("settings"), dict):
                data["settings"] = DEFAULT_DATA["settings"].copy()
            return data
        except (OSError, json.JSONDecodeError):
            pass
    return json.loads(json.dumps(DEFAULT_DATA))

class DayFlow(ctk.CTk):
    def __init__(self):
        self.data = load_data()
        ctk.set_appearance_mode(self.data["settings"].get("appearance", "dark"))
        ctk.set_default_color_theme("blue")
        super().__init__()
        self.title(f"{APP_NAME}  •  Your day, under control")
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
        self.after(15000, self.check_reminders)

    def save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")

    def build_shell(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=("#E9EDF3", "#171D28"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(26, 30))
        ctk.CTkLabel(brand, text="◈  DAYFLOW", font=ctk.CTkFont(size=22, weight="bold"), text_color=("#172235", "#F4F7FC")).pack(anchor="w")
        ctk.CTkLabel(brand, text="YOUR DAY, UNDER CONTROL", font=ctk.CTkFont(size=9, weight="bold"), text_color=("#718096", "#8492A6")).pack(anchor="w", pady=(5, 0))
        self.nav_buttons = {}
        for name, glyph in [("Overview","⌂"),("Tasks","✓"),("Calendar","▦"),("Notes","▤"),("Habits","↗"),("Goals","◎"),("Focus","◷"),("Settings","⚙")]:
            b = ctk.CTkButton(self.sidebar, text=f"  {glyph}    {name}", anchor="w", height=42, corner_radius=10,
                fg_color="transparent", hover_color=("#DCE4EF", "#252F40"), text_color=("#344054", "#C7D0DE"),
                font=ctk.CTkFont(size=13, weight="bold"), command=lambda n=name: self.show_page(n))
            b.pack(fill="x", padx=12, pady=3)
            self.nav_buttons[name] = b
        ctk.CTkLabel(self.sidebar, text=f"DAYFLOW  v{APP_VERSION}", text_color=("#98A2B3", "#667085"), font=ctk.CTkFont(size=10)).pack(side="bottom", pady=18)
        self.main = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew", padx=28, pady=24)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

    def clear_main(self):
        for child in self.main.winfo_children():
            child.destroy()

    def header(self, title, subtitle):
        top = ctk.CTkFrame(self.main, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        ctk.CTkLabel(top, text=title, font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(top, text=subtitle, font=ctk.CTkFont(size=12), text_color=("gray55", "gray65")).pack(anchor="w", pady=(4, 0))
        return top

    def body(self):
        body = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        return body

    def panel(self, parent, title=None):
        frame = ctk.CTkFrame(parent, corner_radius=16, fg_color=("white", "#1A2230"), border_width=1, border_color=("#E4E9F0", "#263244"))
        if title:
            ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=18, pady=(16, 10))
        return frame

    def show_page(self, name):
        self.active_page = name
        for n, b in self.nav_buttons.items():
            b.configure(fg_color=("#D7E5F7", "#263B58") if n == name else "transparent",
                        text_color=("#1456A0", "#8FC0FF") if n == name else ("#344054", "#C7D0DE"))
        self.clear_main()
        getattr(self, f"page_{name.lower()}")()

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
            ctk.CTkLabel(card, text=str(value), font=ctk.CTkFont(size=30, weight="bold")).pack(anchor="w", padx=18)
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
                t["done"]=v.get(); self.save(); self.show_page("Tasks")
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
            card=self.panel(body,habit["name"]); card.pack(fill="x",pady=6)
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
        self.timer_label=ctk.CTkLabel(card,text=f"{minutes:02d}:00",font=ctk.CTkFont(size=64,weight="bold"))
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
        info=self.panel(body,"Your data"); info.pack(fill="x",pady=12)
        ctk.CTkLabel(info,text=f"Your information is stored locally on this device:\n{DATA_FILE}",justify="left",text_color=("gray55","gray65")).pack(anchor="w",padx=18,pady=16)

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
            self.data["tasks"][0]["reminded"]=today if self.data["tasks"] else today
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
