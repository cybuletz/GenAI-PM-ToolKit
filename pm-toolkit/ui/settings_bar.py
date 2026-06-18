import customtkinter as ctk
import threading
import requests as _requests
from core.gmail_auth import GmailAuth

_MODELS_LIST_URL = "https://models.inference.ai.azure.com/models"
_FALLBACK_MODELS = ["gpt-4o", "gpt-4.1", "gpt-4o-mini",
                    "claude-3-5-sonnet", "claude-3-7-sonnet"]


def fetch_available_models(token: str) -> list[str]:
    try:
        resp = _requests.get(
            _MODELS_LIST_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        items = data if isinstance(data, list) else data.get("data", [])
        models = [
            item.get("id") or item.get("name", "")
            for item in items
            if item.get("id") or item.get("name")
        ]
        return models if models else _FALLBACK_MODELS
    except Exception:
        return _FALLBACK_MODELS


class _PATDialog(ctk.CTkToplevel):
    """Simple dialog to paste a GitHub Personal Access Token."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("GitHub Copilot \u2013 Sign In")
        self.geometry("500x260")
        self.resizable(False, False)
        self.grab_set()
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
            fg_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray40"),
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
        # columns: Gmail lbl/btn | M365 lbl/btn | Copilot lbl/btn | Model lbl/menu(expands)
        self.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=0)
        self.grid_columnconfigure(7, weight=1)
        self._build()

    def _build(self):
        # ---- Gmail --------------------------------------------------- #
        gmail_connected = bool(self.settings.get("gmail_token_path"))
        ctk.CTkLabel(self, text="Gmail:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, padx=(16, 4), pady=8)
        self.gmail_btn = ctk.CTkButton(
            self,
            text="\u2705 Connected" if gmail_connected else "Sign In",
            width=110, height=28, font=ctk.CTkFont(size=12),
            fg_color=("#2ecc71", "#27ae60") if gmail_connected else ("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("#27ae60", "#219a52") if gmail_connected else ("gray70", "gray40"),
            command=self._gmail_signin
        )
        self.gmail_btn.grid(row=0, column=1, padx=(0, 24), pady=8)

        # ---- Microsoft 365 — same pattern as Gmail ------------------- #
        # ms_token_cache.json presence = previously signed in
        ms_token_path = self._ms_token_path()
        ms_connected = ms_token_path is not None
        ctk.CTkLabel(self, text="M365:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=2, padx=(0, 4), pady=8)
        self.ms_btn = ctk.CTkButton(
            self,
            text="\u2705 Connected" if ms_connected else "Sign In",
            width=110, height=28, font=ctk.CTkFont(size=12),
            fg_color=("#2ecc71", "#27ae60") if ms_connected else ("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("#27ae60", "#219a52") if ms_connected else ("gray70", "gray40"),
            command=self._ms365_signin
        )
        self.ms_btn.grid(row=0, column=3, padx=(0, 24), pady=8)

        # ---- GitHub Copilot ------------------------------------------ #
        gh_connected = bool(self.settings.get("github_token"))
        ctk.CTkLabel(self, text="Copilot:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=4, padx=(0, 4), pady=8)
        self.gh_btn = ctk.CTkButton(
            self,
            text="\u2705 Connected" if gh_connected else "Sign In",
            width=110, height=28, font=ctk.CTkFont(size=12),
            fg_color=("#2ecc71", "#27ae60") if gh_connected else ("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("#27ae60", "#219a52") if gh_connected else ("gray70", "gray40"),
            command=self._github_signin
        )
        self.gh_btn.grid(row=0, column=5, padx=(0, 24), pady=8)

        # ---- Model selector ------------------------------------------ #
        ctk.CTkLabel(self, text="Model:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=6, padx=(0, 4), pady=8)
        current_model = self.settings.get("model", "gpt-4o")
        self.model_var = ctk.StringVar(value=current_model)
        self.model_menu = ctk.CTkOptionMenu(
            self,
            values=_FALLBACK_MODELS,
            variable=self.model_var,
            width=200, height=28,
            font=ctk.CTkFont(size=12),
            button_color=("gray75", "gray35"),
            button_hover_color=("gray65", "gray45"),
            fg_color=("gray85", "gray25"),
            text_color=("gray10", "gray90"),
            command=self._on_model_change
        )
        self.model_menu.grid(row=0, column=7, padx=(0, 16), pady=8, sticky="w")

        if self.settings.get("github_token"):
            self._refresh_model_list(self.settings["github_token"])

    @staticmethod
    def _ms_token_path():
        """Return the ms_token_cache.json path if it exists, else None."""
        import os
        survey_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "tools", "survey")
        )
        p = os.path.join(survey_dir, "ms_token_cache.json")
        return p if os.path.exists(p) else None

    def _refresh_model_list(self, token: str):
        def run():
            models = fetch_available_models(token)
            current = self.model_var.get()
            if current not in models:
                models = [current] + models
            self.after(0, lambda: self.model_menu.configure(values=models))
        threading.Thread(target=run, daemon=True).start()

    def _gmail_signin(self):
        def do_auth():
            try:
                auth = GmailAuth()
                token_path = auth.authenticate()
                self.settings["gmail_token_path"] = token_path
                self.save_settings_fn(self.settings)
                self.after(0, lambda: self.gmail_btn.configure(
                    text="\u2705 Connected",
                    fg_color=("#2ecc71", "#27ae60"),
                    hover_color=("#27ae60", "#219a52"),
                    text_color=("gray10", "gray90"),
                ))
            except Exception:
                self.after(0, lambda: self.gmail_btn.configure(
                    text="\u274c Failed",
                    fg_color=("#e74c3c", "#c0392b"),
                ))
        threading.Thread(target=do_auth, daemon=True).start()

    def _ms365_signin(self):
        """
        Authenticate with Microsoft 365.
        Reads tools/survey/ms_credentials.json (same pattern as Gmail credentials.json).
        Opens the real Microsoft login page in the browser — no dialog, no manual URL.
        Subsequent sign-ins are silent (token cached in ms_token_cache.json).
        """
        def do_auth():
            try:
                from core.microsoft_auth import MicrosoftAuth
                auth = MicrosoftAuth()
                auth.authenticate()   # browser opens on first call; silent thereafter
                self.after(0, lambda: self.ms_btn.configure(
                    text="\u2705 Connected",
                    fg_color=("#2ecc71", "#27ae60"),
                    hover_color=("#27ae60", "#219a52"),
                    text_color=("gray10", "gray90"),
                ))
            except FileNotFoundError as e:
                # ms_credentials.json missing — show a clear one-time message
                self.after(0, lambda: self.ms_btn.configure(
                    text="\u26a0\ufe0f Setup needed",
                    fg_color=("#e67e22", "#d35400"),
                    hover_color=("#d35400", "#b94600"),
                    text_color=("white", "white"),
                ))
                self.after(0, lambda: self._show_ms_setup_hint(str(e)))
            except Exception as e:
                self.after(0, lambda: self.ms_btn.configure(
                    text="\u274c Failed",
                    fg_color=("#e74c3c", "#c0392b"),
                ))
        threading.Thread(target=do_auth, daemon=True).start()

    def _show_ms_setup_hint(self, message: str):
        """Show a small non-blocking popup with setup instructions."""
        win = ctk.CTkToplevel(self)
        win.title("Microsoft 365 — One-time Setup")
        win.geometry("520x220")
        win.resizable(False, False)
        win.grab_set()
        ctk.CTkLabel(
            win,
            text=message,
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="left",
            wraplength=480,
        ).pack(padx=20, pady=(20, 12), anchor="w")
        ctk.CTkButton(win, text="OK", width=80, command=win.destroy).pack(pady=(0, 16))

    def _github_signin(self):
        dialog = _PATDialog(self)
        self.wait_window(dialog)
        token = dialog.result
        if token:
            self.settings["github_token"] = token
            self.save_settings_fn(self.settings)
            self.gh_btn.configure(
                text="\u2705 Connected",
                fg_color=("#2ecc71", "#27ae60"),
                hover_color=("#27ae60", "#219a52"),
                text_color=("gray10", "gray90"),
            )
            self._refresh_model_list(token)

    def _on_model_change(self, value: str):
        self.settings["model"] = value
        self.save_settings_fn(self.settings)
