import json
import os
import sys
import ctypes
import time
import threading
import urllib.request
import ssl
import certifi
import webbrowser
import subprocess
import tempfile
import winreg
import tkinter as tk
from tkinter import messagebox
from datetime import date, datetime, timedelta
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageTk

GLASS_KEY = "#010101"

def apply_windows_glass_backdrop(window, transparency=8, light=False):
    """Expose a Windows acrylic backdrop through transparent Tk root pixels."""
    if sys.platform != "win32":
        return False
    key = GLASS_KEY
    try:
        # Tk's colour-key transparency lets DWM draw acrylic behind the client
        # area without fading child text, icons or controls.
        window.wm_attributes("-transparentcolor", key)
        window.configure(fg_color=key)
    except Exception:
        # Keep the app usable if colour-key transparency is unavailable.
        try:
            window.configure(fg_color="#EDEDED" if light else "#101012")
        except Exception:
            pass
    try:
        window.update_idletasks()
        user32 = ctypes.windll.user32
        hwnd = ctypes.c_void_p(window.winfo_id())
        try:
            user32.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
            user32.GetAncestor.restype = ctypes.c_void_p
            hwnd = ctypes.c_void_p(user32.GetAncestor(hwnd, 2) or hwnd.value)
        except Exception:
            pass

        # Windows 11 system backdrop (transient acrylic).
        backdrop_ok = False
        try:
            backdrop = ctypes.c_int(3)
            dwm_set = ctypes.windll.dwmapi.DwmSetWindowAttribute
            dwm_set.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint]
            dwm_set.restype = ctypes.c_long
            result = dwm_set(hwnd, 38, ctypes.byref(backdrop), ctypes.sizeof(backdrop))
            backdrop_ok = (result == 0)
        except Exception:
            pass

        # Acrylic fallback also supplies a user-adjustable tint on Windows 10.
        class ACCENT_POLICY(ctypes.Structure):
            _fields_ = [("AccentState", ctypes.c_int), ("AccentFlags", ctypes.c_int),
                        ("GradientColor", ctypes.c_int), ("AnimationId", ctypes.c_int)]
        class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
            _fields_ = [("Attribute", ctypes.c_int), ("Data", ctypes.c_void_p),
                        ("SizeOfData", ctypes.c_size_t)]
        amount = max(0, min(35, int(transparency)))
        alpha = 0xE8 - round((0xE8 - 0x70) * amount / 35)
        colour = 0x00F0F0F0 if light else 0x0017171B
        policy = ACCENT_POLICY(4, 2, (alpha << 24) | colour, 0)
        data = WINDOWCOMPOSITIONATTRIBDATA(19, ctypes.addressof(policy), ctypes.sizeof(policy))
        apply_attribute = user32.SetWindowCompositionAttribute
        apply_attribute.argtypes = [ctypes.c_void_p, ctypes.POINTER(WINDOWCOMPOSITIONATTRIBDATA)]
        apply_attribute.restype = ctypes.c_bool
        accent_ok = bool(apply_attribute(hwnd, ctypes.byref(data)))
        try:
            user32.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                            ctypes.c_int, ctypes.c_int, ctypes.c_uint]
            user32.SetWindowPos.restype = ctypes.c_bool
            user32.SetWindowPos(hwnd, None, 0, 0, 0, 0,
                                0x0001 | 0x0002 | 0x0004 | 0x0020)
        except Exception:
            pass
        return backdrop_ok or accent_ok
    except Exception:
        return False



def install_accent_spotlight(window, accent, background="#101012"):
    """Render a soft multi-layer nebula glow behind the app's glass surfaces."""
    try:
        if not isinstance(accent, str) or len(accent) != 7 or not accent.startswith("#"):
            return
        window.update_idletasks()
        width = max(900, int(window.winfo_width()))
        height = max(620, int(window.winfo_height()))
        rgb = tuple(int(accent[index:index + 2], 16) for index in (1, 3, 5))
        glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(glow)
        # Broad atmospheric haze plus several softer nebula cores. Keep the
        # edges diffuse so the colour never looks like a hard spotlight.
        blobs = [
            (0.76, 0.10, 0.48, 0.48, 68),
            (0.92, 0.42, 0.34, 0.38, 46),
            (0.18, 0.88, 0.42, 0.38, 32),
            (0.46, 0.52, 0.34, 0.30, 22),
        ]
        for cx, cy, rx, ry, alpha in blobs:
            bounds = (int((cx-rx)*width), int((cy-ry)*height),
                      int((cx+rx)*width), int((cy+ry)*height))
            draw.ellipse(bounds, fill=(*rgb, alpha))
        glow = glow.filter(ImageFilter.GaussianBlur(max(90, int(min(width, height) * 0.19))))
        photo = ImageTk.PhotoImage(glow)
        previous = getattr(window, "_accent_spotlight_canvas", None)
        if previous is not None and previous.winfo_exists():
            previous.destroy()
        canvas = tk.Canvas(window, width=width, height=height, highlightthickness=0,
                           borderwidth=0, bg=background)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        canvas.create_image(0, 0, anchor="nw", image=photo)
        canvas.lower()
        window._accent_spotlight_canvas = canvas
        window._accent_spotlight_photo = photo
        # Keep the pre-rendered glow stable during interactive resizing.
        # Re-blurring a full-window image on every Configure event caused lag.
        window._active_spotlight_colour = accent
    except Exception:
        # A decorative layer must never interrupt app startup or navigation.
        pass

try:
    import customtkinter as ctk
except ImportError:
    raise SystemExit("DayFlow needs CustomTkinter. Run: pip install -r requirements.txt")

APP_NAME = "DayFlow"
APP_VERSION = "1.6"
GITHUB_RELEASES_API = "https://api.github.com/repos/adrianvaleitl-debug/DayFlow/releases/latest"
PERSONAL_SITE = "https://adrianvaleitl-debug.github.io/"
KOFI = "https://ko-fi.com/marketinsight"
GITHUB_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
DATA_DIR = Path(os.getenv("APPDATA", str(Path.home()))) / "DayFlow"
DATA_FILE = DATA_DIR / "dayflow_data.json"

DEFAULT_DATA = {
    "tasks": [], "notes": [], "habits": [], "goals": [], "focus_sessions": [],
    "settings": {"appearance": "dark", "accent": "black", "transparency": 8, "focus_minutes": 25, "font": "Segoe UI", "bold": True, "tutorial_seen": False, "auto_updates": True}
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
        if not self.data["settings"].get("forest_glass_migrated"):
            self.data["settings"]["accent"] = "black"
            self.data["settings"]["forest_glass_migrated"] = True
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            DATA_FILE.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        if self.data["settings"].get("accent") in ("dollar", "euro", "pound", "yen", "franc"):
            self.data["settings"]["accent"] = "black"
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            DATA_FILE.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AdrianVale.DayFlow")
        except Exception:
            pass
        ctk.set_appearance_mode(self.data["settings"].get("appearance", "dark"))
        ctk.set_default_color_theme("blue")
        self.apply_accent_theme()
        super().__init__()
        self.title(f"{APP_NAME}  •  Your day, under control")
        try:
            icon = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "dayflow.ico"
            if icon.exists():
                # Use the dedicated ICO for the window and taskbar identity.
                self.iconbitmap(str(icon))
        except Exception:
            pass
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"{min(1380, max(1080, screen_w - 80))}x{min(900, max(720, screen_h - 100))}")
        self.minsize(1020, 680)
        self.configure(fg_color=GLASS_KEY if sys.platform=="win32" else ("#101012", "#101012"))
        self.apply_glass_effect()
        self.timer_running = False
        self.timer_end = None
        self.timer_job = None
        self.active_page = "Overview"
        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self.build_shell()
        self.show_page("Overview")
        self.after(350, self.apply_glass_effect)
        self.after(1200, self.apply_native_icon)
        self.after(2600, self.apply_native_icon)
        self.after(500, self.show_legal_notice)

    def show_legal_notice(self, force=False):
        version = "2026-11-12"
        if not force and self.data["settings"].get("legal_notice_version") == version:
            self.continue_after_legal_notice()
            return
        dialog = ctk.CTkToplevel(self)
        dialog.title("DayFlow · Important information")
        dialog.geometry("720x650")
        dialog.minsize(600, 520)
        dialog.transient(self)
        dialog.grab_set()
        def dismiss_notice():
            if force:
                dialog.grab_release()
                dialog.destroy()
            else:
                self.close_app()
        dialog.protocol("WM_DELETE_WINDOW", dismiss_notice)
        dialog.configure(fg_color=("#F2F3F2", "#171A18"))
        ctk.CTkLabel(dialog, text="Before you use DayFlow", font=self.ui_font(24, True), anchor="w").pack(fill="x", padx=26, pady=(22, 5))
        ctk.CTkLabel(dialog, text="Please read and acknowledge this personal planning software notice.", font=self.ui_font(12), text_color=("gray35", "gray70"), anchor="w").pack(fill="x", padx=26, pady=(0, 12))
        body = ctk.CTkScrollableFrame(dialog, fg_color=("#FFFFFF", "#202622"))
        body.pack(fill="both", expand=True, padx=20, pady=(0, 14))
        notice = (
            "PERSONAL ORGANISATION TOOL ONLY\n\n"
            "DayFlow is a personal productivity and planning tool. It helps you organise tasks, notes, habits, goals and focus sessions. It is not a professional scheduling, emergency alert, medical, mental-health, legal, financial or other advisory service. It does not assess your health, wellbeing, performance or suitability for any activity.\n\n"
            "TASKS, DATES AND REMINDERS\n\n"
            "You are responsible for checking task details, due dates, priorities and plans. DayFlow reminders are in-app prompts and are not guaranteed to appear at a particular time or at all. They can be affected by whether the app is running, device settings, sleep or shutdown, software errors and other interruptions. Do not rely on DayFlow as the sole reminder for medical appointments, safety matters, legal deadlines, payments, travel or other critical commitments. Use an additional dependable reminder where missing an event could have serious consequences.\n\n"
            "YOUR DATA AND BACKUPS\n\n"
            "Your tasks, notes, habits, goals and progress are stored locally on this device. Device failure, accidental deletion, corrupted files, operating-system problems or user actions may cause data loss. You are responsible for keeping separate backups of information you need.\n\n"
            "NO GUARANTEE OF RESULTS OR AVAILABILITY\n\n"
            "DayFlow does not guarantee increased productivity, completion of goals, improved habits or any particular outcome. Features may change, become unavailable or contain defects. Update checks and downloads rely on third-party services, including GitHub, outside the developer's control.\n\n"
            "LIMITATION OF LIABILITY\n\n"
            "To the fullest extent permitted by applicable law, Adrian Vale and the people involved in creating or maintaining DayFlow exclude responsibility for losses, damage or costs arising from use of, inability to use, or reliance on the app, including lost or corrupted data, missed reminders, missed deadlines, interrupted work or decisions made using its contents. This does not exclude or limit any liability or consumer right that cannot lawfully be excluded or limited.\n\n"
            "Using DayFlow does not create a professional relationship with Adrian Vale. If you do not agree with this notice, do not continue using the app."
        )
        ctk.CTkLabel(body, text=notice, font=self.ui_font(12), justify="left", anchor="nw", wraplength=630).pack(fill="both", expand=True, padx=16, pady=16)
        actions = ctk.CTkFrame(dialog, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=(0, 18))
        ctk.CTkButton(actions, text="Exit DayFlow", command=dismiss_notice, width=160).pack(side="left")
        def accept_notice():
            self.data["settings"]["legal_notice_version"] = version
            self.save()
            dialog.grab_release()
            dialog.destroy()
            if not force:
                self.continue_after_legal_notice()
        ctk.CTkButton(actions, text="I understand — continue", command=accept_notice, width=205, height=40).pack(side="right")

    def continue_after_legal_notice(self):
        if not self.data["settings"].get("tutorial_seen", False):
            self.data["settings"]["tutorial_seen"] = True
            self.save()
            self.after(250, self.show_tutorial)
        self.after(15000, self.check_reminders)
        if self.data["settings"].get("auto_updates", True):
            self.after(2500, lambda: self.check_updates(silent=True))

    def show_legal_from_settings(self):
        self.show_legal_notice(force=True)

    def accent_colors(self):
        return {"black":("#B9B9B9","#A0A0A0"),"amber":("#D7B77F","#BFA16A"),"azure":("#91AFE0","#7897C8"),"lavender":("#B5A0D8","#9B86BE"),"rose":("#D99EAD","#C48495"),"teal":("#91BEC3","#76A6AB"),"dollar":("#D7B77F","#BFA16A"),"euro":("#91AFE0","#7897C8"),"pound":("#B5A0D8","#9B86BE"),"yen":("#D99EAD","#C48495"),"franc":("#91BEC3","#76A6AB")}

    def tint_surface(self, base, amount=0.06):
        """Keep glass surfaces charcoal; the selected colour is used only for accents."""
        return base

    def apply_accent_theme(self):
        accent=str(self.data.get("settings",{}).get("accent","black")).lower()
        if accent not in self.accent_colors(): accent="black"
        self.data["settings"]["accent"]=accent
        primary,hover=self.accent_colors()[accent]
        theme=ctk.ThemeManager.theme
        if "CTkFrame" in theme: theme["CTkFrame"]["corner_radius"]=22
        if "CTkButton" in theme: theme["CTkButton"]["corner_radius"]=15
        if "CTkEntry" in theme: theme["CTkEntry"]["corner_radius"]=15
        updates={
            "CTkButton":{"fg_color":[primary,primary],"hover_color":[hover,hover],"text_color":["#202020","#202020"],"corner_radius":13},
            "CTkCheckBox":{"fg_color":[primary,primary],"hover_color":[hover,hover],"border_color":["#7F7F7F","#7F7F7F"],"checkmark_color":["#202020","#202020"]},
            "CTkSwitch":{"progress_color":[primary,primary]},
            "CTkSlider":{"progress_color":[primary,primary],"button_color":[primary,primary],"button_hover_color":[hover,hover]},
            "CTkProgressBar":{"progress_color":[primary,primary]},
            "CTkRadioButton":{"fg_color":[primary,primary],"hover_color":[hover,hover]},
            "CTkOptionMenu":{"fg_color":["#282828","#282828"],"button_color":[primary,primary],"button_hover_color":[hover,hover],"dropdown_fg_color":["#1F1F1F","#1F1F1F"],"dropdown_hover_color":["#363636","#363636"],"dropdown_text_color":["#F2F2F2","#F2F2F2"],"text_color":["#F2F2F2","#F2F2F2"],"corner_radius":14},
            "CTkComboBox":{"fg_color":["#1A1A1A","#1A1A1A"],"border_color":["#404040","#404040"],"button_color":[primary,primary],"button_hover_color":[hover,hover],"dropdown_fg_color":["#1F1F1F","#1F1F1F"],"dropdown_hover_color":["#363636","#363636"],"dropdown_text_color":["#F2F2F2","#F2F2F2"],"text_color":["#F2F2F2","#F2F2F2"],"corner_radius":14},
            "CTkEntry":{"fg_color":["#1A1A1A","#1A1A1A"],"border_color":["#404040","#404040"],"text_color":["#F2F2F2","#F2F2F2"],"corner_radius":14}
        }
        for widget,values in updates.items():
            if widget in theme: theme[widget].update(values)

    def apply_glass_effect(self):
        try:
            if not sys.platform.startswith("win"):
                return
            apply_windows_glass_backdrop(
                self, int(self.data["settings"].get("transparency", 8)),
                ctk.get_appearance_mode() == "Light")
        except Exception:
            pass

    def apply_native_icon(self):
        """Set Windows large and small window icons explicitly for the taskbar."""
        if sys.platform != "win32":
            return
        try:
            base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
            icon = base / "dayflow.ico"
            if not icon.exists():
                icon = base / "assets" / "dayflow.ico"
            if not icon.exists():
                return
            user32 = ctypes.windll.user32
            self.update_idletasks()
            self.iconbitmap(default=str(icon))
            png = icon.with_suffix('.png')
            if png.exists():
                self._dayflow_icon_photo = tk.PhotoImage(file=str(png))
                self.iconphoto(True, self._dayflow_icon_photo)
            user32.LoadImageW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
            user32.LoadImageW.restype = ctypes.c_void_p
            handle = user32.LoadImageW(None, str(icon), 1, 0, 0, 0x0010)
            if handle:
                user32.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
                user32.GetAncestor.restype = ctypes.c_void_p
                user32.SendMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_void_p]
                user32.SendMessageW.restype = ctypes.c_ssize_t
                hwnd = ctypes.c_void_p(self.winfo_id())
                root_hwnd = user32.GetAncestor(hwnd, 2) or hwnd
                user32.SendMessageW(root_hwnd, 0x0080, 1, handle)
                user32.SendMessageW(root_hwnd, 0x0080, 0, handle)
                self._dayflow_icon_handle = handle
        except Exception:
            pass

    def ui_font(self, size=12, force_bold=False):
        settings = self.data.get("settings", {})
        return ctk.CTkFont(family=settings.get("font", "Segoe UI"), size=size,
                           weight="bold" if force_bold or settings.get("bold", True) else "normal")

    def save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")

    def build_shell(self):
        install_accent_spotlight(self, self.accent_colors()[str(self.data["settings"].get("accent", "black")).lower()][0], GLASS_KEY if sys.platform=="win32" else ("#EDEDED" if ctk.get_appearance_mode()=="Light" else "#101012"))
        # Right-side navigation rail keeps the working canvas broad and uncluttered.
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=224, corner_radius=27, fg_color=("#202024", "#202024"), border_width=1, border_color=("#38383E", "#38383E"))
        self.sidebar.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(8, 14), pady=14)
        self.sidebar.grid_propagate(False)
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(25, 28))
        ctk.CTkLabel(brand, text="◈", font=self.ui_font(30, True), text_color=self.accent_colors()[self.data["settings"].get("accent","euro")][0]).pack(side="left", padx=(0,10))
        brand_text = ctk.CTkFrame(brand, fg_color="transparent")
        brand_text.pack(side="left")
        ctk.CTkLabel(brand_text, text="DayFlow", font=self.ui_font(20, True)).pack(anchor="w")
        ctk.CTkLabel(brand_text, text="PERSONAL WORKSPACE", font=ctk.CTkFont(size=8, weight="bold"), text_color=("gray55","gray65")).pack(anchor="w")
        self.nav_buttons = {}
        nav_area = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent", corner_radius=18)
        nav_area.pack(fill="both", expand=True, padx=12, pady=(0,8))
        groups = [
            ("YOUR DAY", [("Overview","⌂"),("Inbox","↳"),("Tasks","✓"),("Calendar","▦")]),
            ("PERSONAL SPACE", [("Notes","▤"),("Habits","↗"),("Goals","◎")]),
            ("PRODUCTIVITY", [("Focus","◷"),("Insights","◌"),("Weekly Review","▥")]),
            ("PREFERENCES", [("Updates","✦"),("Settings","⚙")])]
        for group, items in groups:
            ctk.CTkLabel(nav_area, text=group, font=ctk.CTkFont(size=9, weight="bold"), text_color=("gray55","gray65")).pack(anchor="w", padx=12, pady=(15,7))
            for name, glyph in items:
                button = ctk.CTkButton(nav_area, text=f"{glyph}   {name}", height=42, corner_radius=12, anchor="w", fg_color="transparent", hover_color=("#E9E9E9","#363636"), text_color=("#696969","#C3C3C3"), font=self.ui_font(12), command=lambda n=name: self.show_page(n))
                button.pack(fill="x", padx=2, pady=2)
                self.nav_buttons[name] = button
        side_footer = ctk.CTkFrame(self.sidebar, fg_color=("#29292E", "#29292E"), corner_radius=22, border_width=0)
        side_footer.pack(fill="x", padx=14, pady=15)
        ctk.CTkLabel(side_footer, text="MAKE ROOM FOR WHAT MATTERS", font=ctk.CTkFont(size=8, weight="bold"), text_color=("gray55","gray65")).pack(anchor="w", padx=12, pady=(11,3))
        ctk.CTkLabel(side_footer, text="A little progress, every day.", font=self.ui_font(10)).pack(anchor="w", padx=12, pady=(0,7))
        ctk.CTkButton(side_footer, text="My website ↗", height=30, corner_radius=10, fg_color="transparent", hover_color=("#E9E9E9","#383838"), text_color=self.accent_colors()[str(self.data["settings"].get("accent","black")).lower()][0], command=lambda:webbrowser.open(PERSONAL_SITE)).pack(fill="x", padx=9, pady=2)
        ctk.CTkButton(side_footer, text="Donate · Ko-fi ↗", height=30, corner_radius=10, fg_color=self.accent_colors()[str(self.data["settings"].get("accent","black")).lower()][0], hover_color=self.accent_colors()[str(self.data["settings"].get("accent","black")).lower()][1], text_color="#202020", command=lambda:webbrowser.open(KOFI)).pack(fill="x", padx=9, pady=(2,10))
        self.topbar = ctk.CTkFrame(self, height=68, corner_radius=25, fg_color=("#202024", "#202024"), border_width=1, border_color=("#38383E", "#38383E"))
        self.topbar.grid(row=0, column=0, sticky="ew", padx=(14, 8), pady=(14, 8))
        self.topbar.grid_propagate(False)
        self.page_title = ctk.CTkLabel(self.topbar, text="Overview", font=self.ui_font(16, True))
        self.page_title.pack(side="left", padx=27)
        self.date_label = ctk.CTkLabel(self.topbar, text=date.today().strftime("%A  ·  %d %B %Y"), font=ctk.CTkFont(size=11), text_color=("gray55","gray65"))
        self.date_label.pack(side="right", padx=28)
        self.main = ctk.CTkFrame(self, fg_color="transparent", corner_radius=18)
        self.main.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=(10, 14))
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

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
        frame = ctk.CTkFrame(parent, corner_radius=24, fg_color=("#202024", "#202024"), border_width=0)
        if title:
            ctk.CTkLabel(frame, text=title, font=self.ui_font(15, True)).pack(anchor="w", padx=24, pady=(20, 12))
        return frame

    def show_page(self, name):
        self.active_page = name
        accent_color = self.accent_colors().get(self.data.get("settings", {}).get("accent", "black"), self.accent_colors()["euro"])[0]
        self.page_title.configure(text=name)
        for nav_name, button in self.nav_buttons.items():
            active = nav_name == name
            button.configure(fg_color=(accent_color, accent_color) if active else "transparent", hover_color=(accent_color, accent_color) if active else ("#E9E9E9","#363636"), text_color=("#202020","#202020") if active else ("#696969","#C3C3C3"), font=self.ui_font(12, active))
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

    def page_inbox(self):
        self.header("Inbox", "A landing place for loose thoughts and things to do.")
        body = self.body()
        capture = self.panel(body, "Quick capture")
        capture.pack(fill="x", pady=(0, 14))
        entry = ctk.CTkEntry(capture, height=42, placeholder_text="Drop something here to remember it…")
        entry.pack(fill="x", padx=18, pady=(0, 9))
        def capture_item():
            value = entry.get().strip()
            if value:
                self.data["tasks"].insert(0, {"id":str(time.time_ns()),"title":value,"due":"","priority":"Normal","done":False,"remind":"","inbox":True})
                self.save()
                self.show_page("Inbox")
        ctk.CTkButton(capture, text="Add to inbox", command=capture_item).pack(anchor="e", padx=18, pady=(0, 16))
        loose = [t for t in self.data["tasks"] if not t.get("done") and (t.get("inbox") or not t.get("due"))]
        listing = self.panel(body, f"Unsorted · {len(loose)}")
        listing.pack(fill="x")
        if not loose:
            ctk.CTkLabel(listing, text="All clear. Your inbox is empty.", text_color=("gray55","gray65")).pack(anchor="w", padx=18, pady=18)
        for task in loose:
            line = ctk.CTkFrame(listing, fg_color="transparent")
            line.pack(fill="x", padx=14, pady=5)
            ctk.CTkLabel(line, text=task.get("title",""), anchor="w").pack(side="left", fill="x", expand=True, padx=5)
            ctk.CTkButton(line, text="Move to tasks", width=105, command=lambda t=task:self._promote_inbox_task(t)).pack(side="right", padx=4)
            ctk.CTkButton(line, text="×", width=30, fg_color="transparent", command=lambda t=task:self.delete_item("tasks",t,"Inbox")).pack(side="right")

    def _promote_inbox_task(self, task):
        task["inbox"] = False
        if not task.get("due"):
            task["due"] = date.today().isoformat()
        self.save()
        self.show_page("Tasks")

    def page_insights(self):
        self.header("Insights", "A quick look at the habits and momentum behind your week.")
        body = self.body()
        cards = ctk.CTkFrame(body, fg_color="transparent")
        cards.pack(fill="x")
        done = [t for t in self.data["tasks"] if t.get("done")]
        open_tasks = [t for t in self.data["tasks"] if not t.get("done")]
        sessions = self.data.get("focus_sessions", [])
        habits = self.data.get("habits", [])
        for title, value, hint in [("TASKS COMPLETED",len(done),"All-time completed"),("STILL IN MOTION",len(open_tasks),"Open tasks"),("FOCUS SESSIONS",len(sessions),"Recorded sessions"),("HABITS IN PLAY",len(habits),"Routines you're tracking")]:
            card = self.panel(cards)
            card.pack(side="left", fill="both", expand=True, padx=(0,10), pady=4)
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=9,weight="bold"), text_color=("gray55","gray65")).pack(anchor="w", padx=15, pady=(14,3))
            ctk.CTkLabel(card, text=str(value), font=self.ui_font(27,True)).pack(anchor="w", padx=15)
            ctk.CTkLabel(card, text=hint, font=ctk.CTkFont(size=10), text_color=("gray55","gray65")).pack(anchor="w", padx=15, pady=(0,13))
        focus_minutes = sum(int(item.get("minutes",0)) for item in sessions)
        summary = self.panel(body, "Your momentum")
        summary.pack(fill="x", pady=(15,0))
        ctk.CTkLabel(summary, text=f"{focus_minutes // 60}h {focus_minutes % 60}m of recorded focus time", font=self.ui_font(19,True)).pack(anchor="w", padx=18, pady=(17,5))
        ctk.CTkLabel(summary, text="Progress isn't only about doing more. It's about making the important things easier to return to.", wraplength=760, justify="left", text_color=("gray55","gray65")).pack(anchor="w", padx=18, pady=(0,18))

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
            ctk.CTkCheckBox(line,text=task["title"],variable=done,command=toggle,font=ctk.CTkFont(size=12),text_color=("gray55","gray65") if task.get("done") else ("#282828","#F4F4F4")).pack(side="left",fill="x",expand=True)
            ctk.CTkLabel(line,text=f'{task.get("due","No date")}  ·  {task.get("priority","Normal")}',font=ctk.CTkFont(size=10),text_color=("gray55","gray65")).pack(side="left",padx=10)
            ctk.CTkButton(line,text="×",width=30,fg_color="transparent",hover_color=("#E9E9E9","#343434"),text_color=("#414141","#B5B5B5"),command=lambda t=task:self.delete_item("tasks",t,"Tasks")).pack(side="right")

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
                fg_color="#6B6B6B" if completed else None).pack(side="left",padx=18,pady=(0,14))
            ctk.CTkLabel(card,text=f'{len(habit.get("history",[]))} total check-ins',text_color=("gray55","gray65")).pack(side="left",padx=12,pady=(0,14))
            ctk.CTkButton(card,text="Remove",width=70,fg_color="transparent",text_color=("#414141","#B5B5B5"),command=lambda h=habit:self.delete_item("habits",h,"Habits")).pack(side="right",padx=14,pady=(0,14))

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
            row = ctk.CTkFrame(dialog, fg_color=("gray92", "#292929"), corner_radius=12)
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
                with urllib.request.urlopen(request, timeout=20, context=GITHUB_SSL_CONTEXT) as response:
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
                fd, temp_path = tempfile.mkstemp(prefix="DayFlow-Setup-", suffix="-update.exe", dir=str(update_dir))
                os.close(fd)
                path = Path(temp_path)
                request = urllib.request.Request(url, headers={"User-Agent": "DayFlow-Updater"})
                with urllib.request.urlopen(request, timeout=120, context=GITHUB_SSL_CONTEXT) as response:
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

    def page_updates(self):
        self.header("Updates", "A release history for DayFlow, with the latest changes up front.")
        body = self.body()
        latest = self.panel(body)
        latest.pack(fill="x", pady=(0, 14))
        top = ctk.CTkFrame(latest, fg_color="transparent")
        top.pack(fill="x", padx=22, pady=(20, 8))
        ctk.CTkLabel(top, text="1.6", font=self.ui_font(25, True),
                     text_color=self.accent_colors()[self.data["settings"].get("accent", "black")][0]).pack(side="left")
        ctk.CTkLabel(top, text="LATEST RELEASE", font=self.ui_font(10, True),
                     text_color=("gray55", "gray65")).pack(side="right")
        ctk.CTkLabel(latest, text="Legal safeguards and reminder limitations",
                     font=self.ui_font(19, True)).pack(anchor="w", padx=22, pady=(0, 5))
        ctk.CTkLabel(latest, text="12 November 2026  ·  Windows desktop",
                     font=self.ui_font(10), text_color=("gray55", "gray65")).pack(anchor="w", padx=22)
        ctk.CTkLabel(latest,
            text="This release adds a first-launch legal and liability notice, plus a Legal & Important Information section in Settings. It explains reminder limitations, critical commitments and local data backups.",
            font=self.ui_font(11), justify="left", anchor="w", wraplength=900,
            text_color=("gray40", "gray75")).pack(fill="x", padx=22, pady=(12, 15))
        for item in [
            "A risk and liability notice appears before first use and must be acknowledged.",
            "The full notice can be reopened from Settings at any time.",
            "In-app reminders are not guaranteed and should not be the only alert for critical commitments.",
            "Your tasks, notes, habits, goals and settings remain stored locally; keep separate backups."]:
            ctk.CTkLabel(latest, text="✓   " + item, font=self.ui_font(11),
                         anchor="w", justify="left", wraplength=900).pack(fill="x", padx=24, pady=3)
        history = self.panel(body, "Previous release")
        history.pack(fill="x", pady=5)
        ctk.CTkLabel(history, text="1.4.8  ·  Accent and creator shortcuts",
                     font=self.ui_font(13, True)).pack(anchor="w", padx=18, pady=(0, 4))
        ctk.CTkLabel(history,
                     text="Added the accent-colour spotlight and persistent Adrian Vale / Ko-fi shortcuts. The Windows backdrop and transparency implementation is refined in 1.4.9.",
                     font=self.ui_font(11), text_color=("gray45", "gray70"),
                     justify="left", anchor="w", wraplength=900).pack(fill="x", padx=18, pady=(0, 12))
        earlier = self.panel(body, "Earlier versions")
        earlier.pack(fill="x", pady=5)
        for version, title, detail in [
            ("1.4.7", "Creator shortcuts", "Added persistent website and Ko-fi links to the desktop sidebar."),
            ("1.4.6", "Accent and spacing refinements", "Restored six accent choices, refined panel spacing and improved Windows icon handling.")
        ]:
            row = ctk.CTkFrame(earlier, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=(8, 2))
            ctk.CTkLabel(row, text=version, font=self.ui_font(12, True),
                         text_color=self.accent_colors()[self.data["settings"].get("accent", "black")][0]).pack(side="left")
            ctk.CTkLabel(row, text=title, font=self.ui_font(12, True)).pack(side="left", padx=12)
            ctk.CTkLabel(earlier, text=detail, font=self.ui_font(10),
                         text_color=("gray45", "gray70"), anchor="w", justify="left",
                         wraplength=900).pack(fill="x", padx=18, pady=(0, 7))

    def page_settings(self):
        self.header("Settings", "Make DayFlow feel like your workspace.")
        body=self.body()
        card=self.panel(body,"Appearance"); card.pack(fill="x",pady=(0,12))
        ctk.CTkLabel(card,text="Appearance").pack(anchor="w",padx=18,pady=(0,5))
        appearance=ctk.CTkOptionMenu(card,values=["dark","light","system"],command=self.set_appearance)
        appearance.set(self.data["settings"].get("appearance","dark")); appearance.pack(anchor="w",padx=22,pady=(0,12))
        ctk.CTkLabel(card,text="Accent colour").pack(anchor="w",padx=22,pady=(0,5))
        colour=ctk.CTkOptionMenu(card,values=["Black","Amber","Azure","Lavender","Rose","Teal"],command=self.set_accent)
        colour.set({"black":"Black","amber":"Amber","azure":"Azure","lavender":"Lavender","rose":"Rose","teal":"Teal","dollar":"Amber","euro":"Azure","pound":"Lavender","yen":"Rose","franc":"Teal"}.get(self.data["settings"].get("accent","black"),"Black")); colour.pack(anchor="w",padx=22,pady=(0,12))
        ctk.CTkLabel(card,text="Window transparency").pack(anchor="w",padx=18,pady=(0,5))
        transparency_value=ctk.CTkLabel(card,text=f'{int(self.data["settings"].get("transparency",8))}%',text_color=("gray55","gray75"))
        transparency_value.pack(anchor="w",padx=18,pady=(0,4))
        transparency=ctk.CTkSlider(card,from_=0,to=35,number_of_steps=35,command=lambda v:self.set_transparency(v,transparency_value))
        transparency.set(int(self.data["settings"].get("transparency",8))); transparency.pack(fill="x",padx=18,pady=(0,16))
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

        legal = ctk.CTkFrame(scroll, fg_color=("#FFFFFF", "#202622"), corner_radius=18)
        legal.pack(fill="x", padx=12, pady=8)
        ctk.CTkLabel(legal, text="Legal & important information", font=self.ui_font(16, True), anchor="w").pack(fill="x", padx=18, pady=(14, 5))
        ctk.CTkLabel(legal, text="Reminders are not guaranteed. Keep separate backups of important personal planning information.", font=self.ui_font(11), text_color=("gray35", "gray70"), wraplength=700, justify="left", anchor="w").pack(fill="x", padx=18, pady=(0, 8))
        ctk.CTkButton(legal, text="Read legal & liability notice", command=self.show_legal_from_settings, width=220).pack(anchor="w", padx=18, pady=(0, 14))

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
            icon = (Path(sys.executable).resolve().parent / "dayflow.ico") if getattr(sys, "frozen", False) else (Path(__file__).resolve().parent / "assets" / "dayflow.ico")
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

    def set_transparency(self,value,label=None):
        value=round(max(0,min(35,float(value))))
        self.data["settings"]["transparency"]=value
        if label: label.configure(text=f"{value}%")
        self.after_idle(self.apply_glass_effect)
        self.save()

    def set_accent(self, value):
        aliases={"Black":"black","Amber":"amber","Azure":"azure","Lavender":"lavender","Rose":"rose","Teal":"teal","Focus":"amber","Flow":"azure","Growth":"lavender","Energy":"rose","Balance":"teal"}
        value=aliases.get(value,str(value).lower())
        if value not in self.accent_colors():
            value="black"
        self.data["settings"]["accent"]=value
        self.apply_accent_theme()
        self.save()
        # Recreate the shell as well as the page so the sidebar, footer,
        # navigation highlights and content all receive the selected palette.
        current_page=getattr(self,"active_page","Overview")
        for child in self.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass
        self.build_shell()
        self.show_page(current_page)
        self.apply_glass_effect()
        install_accent_spotlight(self, self.accent_colors()[value][0],
            GLASS_KEY if sys.platform=="win32" else ("#EDEDED" if ctk.get_appearance_mode()=="Light" else "#101012"))

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

_DAYFLOW_MUTEX = None

def acquire_single_instance():
    """Keep one DayFlow window; clicking its shortcut activates the existing window."""
    global _DAYFLOW_MUTEX
    if sys.platform != "win32":
        return True
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        handle = kernel32.CreateMutexW(None, False, "Local\\AdrianVale.DayFlow.Singleton")
        if not handle:
            return True
        if kernel32.GetLastError() == 183:
            kernel32.CloseHandle(handle)
            user32 = ctypes.windll.user32
            hwnd = user32.FindWindowW(None, "DayFlow  •  Your day, under control")
            if hwnd:
                user32.ShowWindow(hwnd, 9)
                user32.SetForegroundWindow(hwnd)
            return False
        _DAYFLOW_MUTEX = handle
        return True
    except Exception:
        return True

if __name__ == "__main__" and acquire_single_instance():
    app = DayFlow()
    app.mainloop()
