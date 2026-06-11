import customtkinter as ctk
import threading
from core.gmail_auth import GmailAuth


class _PATDialog(ctk.CTkToplevel):
    """Simple dialog to paste a GitHub Personal Access Token."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("GitHub Copilot – Sign In")
        self.geometry("500x260")
        self.resizable(False, False)
        self.grab_set()  # modal
        self.result: str = ""
        self._build()

    def _build(self):
        pad = {"padx": 24, "pady": 8}

        ctk.CTkLabel(
            self,
            text="Paste your GitHub Personal Access Token (PAT)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(**pad, anchor="w")

        ctk.CTkLabel(
            self,
            text=(
                "Generate one at: github.com/settings/tokens\n"
                "Required scope: models:read  (or use a Copilot-enabled token)"
            ),
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="left"
        ).pack(padx=24, pady=(0, 8), anchor="w")

        self.entry = ctk.CTkEntry(
            self, width=450, height=36,
            font=ctk.CTkFont(size=13),
            placeholder_text="ghp_xxxxxxxxxxxxxxxxxxxx",
            show="*"
        )
        self.entry.pack(padx=24, pady=(0, 4))

        show_var = ctk.BooleanVar(value=False)
        def toggle_show():
            self.entry.configure(show="" if show_var.get() else "*")
        ctk.CTkCheckBox(
            self, text="Show token", variable=show_var, command=toggle_show,
            font=ctk.CTkFont(size=12)
        ).pack(padx=24, pady=(0, 12), anchor="w")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=24, fill="x")

        ctk.CTkButton(
            btn_frame, text="Save", width=100, height=34,
            command=self._save
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_frame, text="Cancel", width=100, height=34,
            fg_color="transparent", border_width=1,
            command=self.destroy
        ).pack(side="right")

    def _save(self):
        token = self.entry.get().strip()
        if token:
            self.result = token
        self.destroy()


class SettingsBar(ctk.CTkFrame):
    def __init__(self, parent, settings: dict, save_settings_fn, on_theme_change):
        super().__init__(parent, height=48, corner_radius=0)
        self.settings = settings
        self.save_settings_fn = save_settings_fn
        self.on_theme_change = on_theme_change
        self.grid_columnconfigure((0, 1, 2, 3, 4), weight=0)
        self.grid_columnconfigure(5, weight=1)
        self._build()

    def _build(self):
        # Gmail status
        gmail_connected = bool(self.settings.get("gmail_token_path"))
        self.gmail_label = ctk.CTkLabel(self, text="Gmail:", font=ctk.CTkFont(size=12))
        self.gmail_label.grid(row=0, column=0, padx=(16, 4), pady=8)

        self.gmail_btn = ctk.CTkButton(
            self, text="✅ Connected" if gmail_connected else "Sign In",
            width=110, height=28, font=ctk.CTkFont(size=12),
            fg_color=("#2ecc71", "#27ae60") if gmail_connected else None,
            command=self._gmail_signin
        )
        self.gmail_btn.grid(row=0, column=1, padx=(0, 24), pady=8)

        # GitHub Copilot status
        gh_connected = bool(self.settings.get("github_token"))
        self.gh_label = ctk.CTkLabel(self, text="Copilot:", font=ctk.CTkFont(size=12))
        self.gh_label.grid(row=0, column=2, padx=(0, 4), pady=8)

        self.gh_btn = ctk.CTkButton(
            self,
            text="✅ Connected" if gh_connected else "Sign In",
            width=110, height=28, font=ctk.CTkFont(size=12),
            fg_color=("#2ecc71", "#27ae60") if gh_connected else None,
            command=self._github_signin
        )
        self.gh_btn.grid(row=0, column=3, padx=(0, 24), pady=8)

        # Model selector
        self.model_label = ctk.CTkLabel(self, text="Model:", font=ctk.CTkFont(size=12))
        self.model_label.grid(row=0, column=4, padx=(0, 4), pady=8)

        self.model_var = ctk.StringVar(value=self.settings.get("model", "gpt-4o"))
        self.model_menu = ctk.CTkOptionMenu(
            self,
            values=["gpt-4o", "gpt-4.1", "gpt-4o-mini", "claude-3-5-sonnet", "claude-3-7-sonnet"],
            variable=self.model_var,
            width=180, height=28,
            font=ctk.CTkFont(size=12),
            command=self._on_model_change
        )
        self.model_menu.grid(row=0, column=5, padx=(0, 16), pady=8, sticky="w")

    def _gmail_signin(self):
        def do_auth():
            try:
                auth = GmailAuth()
                token_path = auth.authenticate()
                self.settings["gmail_token_path"] = token_path
                self.save_settings_fn(self.settings)
                self.after(0, lambda: self.gmail_btn.configure(
                    text="✅ Connected",
                    fg_color=("#2ecc71", "#27ae60")
                ))
            except Exception:
                self.after(0, lambda: self.gmail_btn.configure(text="❌ Failed"))
        threading.Thread(target=do_auth, daemon=True).start()

    def _github_signin(self):
        """Open PAT dialog on the main thread, then save the token."""
        dialog = _PATDialog(self)
        self.wait_window(dialog)
        token = dialog.result
        if token:
            self.settings["github_token"] = token
            self.save_settings_fn(self.settings)
            self.gh_btn.configure(
                text="✅ Connected",
                fg_color=("#2ecc71", "#27ae60")
            )

    def _on_model_change(self, value: str):
        self.settings["model"] = value
        self.save_settings_fn(self.settings)
