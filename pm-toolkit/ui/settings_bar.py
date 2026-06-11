import customtkinter as ctk
import threading
from core.github_auth import GitHubAuth
from core.gmail_auth import GmailAuth


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
            self, text="✅ Connected" if gh_connected else "Sign In",
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
                self.gmail_btn.configure(
                    text="✅ Connected",
                    fg_color=("#2ecc71", "#27ae60")
                )
            except Exception as e:
                self.gmail_btn.configure(text="❌ Failed")
        threading.Thread(target=do_auth, daemon=True).start()

    def _github_signin(self):
        def do_auth():
            try:
                auth = GitHubAuth()
                token = auth.authenticate_device_flow()
                self.settings["github_token"] = token
                self.save_settings_fn(self.settings)
                self.gh_btn.configure(
                    text="✅ Connected",
                    fg_color=("#2ecc71", "#27ae60")
                )
            except Exception as e:
                self.gh_btn.configure(text="❌ Failed")
        threading.Thread(target=do_auth, daemon=True).start()

    def _on_model_change(self, value: str):
        self.settings["model"] = value
        self.save_settings_fn(self.settings)
