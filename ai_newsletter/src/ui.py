import sys
import os
import re
import threading
 
import tkinter as tk
from tkinter import font as tkfont
from dotenv import load_dotenv
from config import ENV_PATH

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv(ENV_PATH)
 
import data_manager

BLUE        = "#1A56DB"
BLUE_HOVER  = "#1648C0"
BLUE_LIGHT  = "#EFF6FF"
WHITE       = "#FFFFFF"
BG          = "#F0F4F8"
CARD_BG     = "#FFFFFF"
TEXT_DARK   = "#0F172A"
TEXT_MID    = "#475569"
TEXT_LIGHT  = "#94A3B8"
BORDER      = "#E2E8F0"
SUCCESS_BG  = "#DCFCE7"
SUCCESS_FG  = "#15803D"
ERROR_BG    = "#FEE2E2"
ERROR_FG    = "#B91C1C"
WARN_BG     = "#FFF7ED"
WARN_FG     = "#C2410C"

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
 
def _is_valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email.strip()))
 
class NewsletterApp(tk.Tk):

    def __init__(self):
        super().__init__()
 
        self.title("AI Newsletter")
        self.resizable(False, False)
        self.configure(bg=BG)
        w, h = 460, 480
        self.geometry(f"{w}x{h}+{(self.winfo_screenwidth()-w)//2}+{(self.winfo_screenheight()-h)//2}")
 
        self._build_ui()

    def _build_ui(self):
        outer = tk.Frame(self, bg=BG, padx=28, pady=28)
        outer.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(outer, bg=BLUE, padx=22, pady=20)
        header.pack(fill=tk.X, pady=(0, 20))
 
        tk.Label(
            header, text="AI Newsletter",
            bg=BLUE, fg=WHITE,
            font=("Arial", 18, "bold"),
            anchor="w"
        ).pack(fill=tk.X)
 
        tk.Label(
            header, text="Daily AI news — delivered to your inbox",
            bg=BLUE, fg="#BFDBFE",
            font=("Arial", 11),
            anchor="w"
        ).pack(fill=tk.X, pady=(4, 0))

        card = tk.Frame(outer, bg=CARD_BG, padx=22, pady=22,
                        relief=tk.FLAT, highlightbackground=BORDER,
                        highlightthickness=1)
        card.pack(fill=tk.X, pady=(0, 14))
 
        tk.Label(card, text="Subscribe", bg=CARD_BG, fg=TEXT_DARK,
                 font=("Arial", 13, "bold")).pack(anchor="w", pady=(0, 4))
 
        tk.Label(card, text="Enter your email address to receive the daily digest.",
                 bg=CARD_BG, fg=TEXT_MID, font=("Arial", 11),
                 wraplength=380, justify="left").pack(anchor="w", pady=(0, 14))
        


        entry_frame = tk.Frame(card, bg=CARD_BG)
        entry_frame.pack(fill=tk.X, pady=(0, 12))
 
        self.email_var = tk.StringVar()
        self.email_entry = tk.Entry(
            entry_frame, textvariable=self.email_var,
            font=("Arial", 12), relief=tk.FLAT,
            bg="#F8FAFC", fg=TEXT_DARK,
            insertbackground=BLUE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.email_entry.pack(fill=tk.X, ipady=8)
        self.email_entry.bind("<Return>", lambda e: self.add_email_address())


        self.subscribe_btn = _Button(
            card, text="Subscribe", command=self.add_email_address,
            bg=BLUE, fg=WHITE, hover_bg=BLUE_HOVER
        )
        self.subscribe_btn.pack(fill=tk.X)

        self.subscribe_status = tk.Label(
            card, text="", bg=CARD_BG,
            font=("Arial", 11), wraplength=380, justify="left"
        )
        self.subscribe_status.pack(anchor="w", pady=(10, 0))

        admin_card = tk.Frame(outer, bg=CARD_BG, padx=22, pady=22,
                              relief=tk.FLAT, highlightbackground=BORDER,
                              highlightthickness=1)
        admin_card.pack(fill=tk.X)
 
        tk.Label(admin_card, text="Manual send", bg=CARD_BG, fg=TEXT_DARK,
                 font=("Arial", 13, "bold")).pack(anchor="w", pady=(0, 4))
 
        tk.Label(admin_card,
                 text="Scrape, summarize, and send today's digest to all active subscribers.",
                 bg=CARD_BG, fg=TEXT_MID, font=("Arial", 11),
                 wraplength=380, justify="left").pack(anchor="w", pady=(0, 14))
 
        self.send_btn = _Button(
            admin_card, text="Send today's newsletter",
            command=self.send_todays_email,
            bg="#1E293B", fg=WHITE, hover_bg="#0F172A"
        )
        self.send_btn.pack(fill=tk.X)

        self.send_status = tk.Label(
            admin_card, text="", bg=CARD_BG,
            font=("Arial", 11), wraplength=380, justify="left"
        )
        self.send_status.pack(anchor="w", pady=(10, 0))
 


    def add_email_address(self):
        email = self.email_var.get().strip()
        if not email:
            self._set_status(self.subscribe_status, "Please enter an email address.", kind="warn")
            return
        if not _is_valid_email(email):
            self._set_status(self.subscribe_status, "That email address doesn't look valid.", kind="error")
            return

        self.subscribe_btn.set_state("disabled")
        self._set_status(self.subscribe_status, "Subscribing…", kind="info")

        def _do():
            try:
                data_manager.add_user(email)
            except ValueError as e:
                self.after(0, lambda: self._set_status(self.subscribe_status, str(e), kind="warn"))
            except Exception as e:
                self.after(0, lambda: self._set_status(self.subscribe_status, f"Subscribe failed: {e}", kind="error"))
            else:
                self.after(0, lambda: self._on_subscribe_success(email))
            finally:
                self.after(0, lambda: self.subscribe_btn.set_state("normal"))

        threading.Thread(target=_do, daemon=True).start()

    def _on_subscribe_success(self, email: str):
        self.email_var.set("")
        self.email_entry.focus_set()
        self._set_status(self.subscribe_status, f"Subscribed: {email}", kind="success")

    def send_todays_email(self):
        def _do():
            try:
                import main
                main.run()
            except Exception as e:
                self.after(0, lambda: self._set_status(self.send_status, f"Send failed: {e}", kind="error"))
            else:
                self.after(0, lambda: self._set_status(self.send_status, "Newsletter sent.", kind="success"))
            finally:
                self.after(0, lambda: self.send_btn.set_state("normal"))

        self.send_btn.set_state("disabled")
        self._set_status(self.send_status, "Sending… (this may take a minute)", kind="info")
        threading.Thread(target=_do, daemon=True).start()

    def _set_status(self, label: tk.Label, message: str, kind: str = "info"):
        kind = (kind or "info").lower()
        if kind == "success":
            fg, bg = SUCCESS_FG, SUCCESS_BG
        elif kind == "error":
            fg, bg = ERROR_FG, ERROR_BG
        elif kind == "warn":
            fg, bg = WARN_FG, WARN_BG
        else:
            fg, bg = TEXT_MID, BLUE_LIGHT

        label.config(text=message, fg=fg, bg=bg)


class _Button(tk.Label):
    def __init__(self, parent, text, command, bg, fg, hover_bg, **kwargs):
        self._bg = bg
        self._hover_bg = hover_bg
        self._fg = fg
        self._command = command
        self._disabled = False

        super().__init__(
            parent,
            text=text,
            bg=bg,
            fg=fg,
            padx=14,
            pady=10,
            cursor="hand2",
            font=tkfont.Font(family="Arial", size=12, weight="bold"),
            **kwargs,
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _on_enter(self, _):
        if not self._disabled:
            self.config(bg=self._hover_bg)
 
    def _on_leave(self, _):
        if not self._disabled:
            self.config(bg=self._bg)
 
    def _on_click(self, _):
        if not self._disabled and self._command:
            self._command()

    def set_state(self, state: str):
        state = (state or "normal").lower()
        self._disabled = state in {"disabled", "disable", "off"}
        if self._disabled:
            self.config(bg="#CBD5E1", fg="#475569", cursor="")
        else:
            self.config(bg=self._bg, fg=self._fg, cursor="hand2")


def launch():
    app = NewsletterApp()
    app.mainloop()

if __name__ == "__main__": 
    launch()
