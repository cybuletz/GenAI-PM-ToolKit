import customtkinter as ctk
import threading
import requests as _requests
from core.gmail_auth import GmailAuth

# GitHub Models API — used to fetch available chat models
_MODELS_LIST_URL = "https://models.inference.ai.azure.com/models"
# Sane fallback if the API call fails or returns nothing useful
_FALLBACK_MODELS = ["gpt-4o", "gpt-4.1", "gpt-4o-mini",
                    "claude-3-5-sonnet", "claude-3-7-sonnet"]


def fetch_available_models(token: str) -> list[str]:
    """
    Call the GitHub Models catalogue endpoint and return model IDs that
    support chat completion.  Falls back to _FALLBACK_MODELS on any error.
    """
    try:
        resp = _requests.get(
            _MODELS_LIST_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        # The API returns a list of model objects; each has an "id" and
        # a "capabilities" dict.  Keep only chat-capable models.
        models = []
        items = data if isinstance(data, list) else data.get("data", [])
        for item in items:
            caps = item.get("capabilities", {})
            if caps.get("supports_completion") or caps.get("type") == "chat":
                models.append(item["id"])
        if not models:
            # If capabilities aren't exposed, just take all returned ids
            models = [item["id"] for item in items if item.get("id")]
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
        self.grid_columnconfigure((0, 1, 2, 3, 4), weight=0)
        self.grid_columnconfigure(5, weight=1)
        self._build()

    def _build(self):
        # Gmail
        gmail_connected = bool(self.settings.get("gmail_token_path"))
        ctk.CTkLabel(self, text="Gmail:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, padx=(16, 4), pady=8)
        self.gmail_btn = ctk.CTkButton(
            self,
            text="\u2705 Connected" if gmail_connected else "Sign In",
            width=110, height=28, font=ctk.CTkFont(size=12),
            fg_color=("#2ecc71", "#27ae60") if gmail_connected
            else ("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("#27ae60", "#219a52") if gmail_connected
            else ("gray70", "gray40"),
            command=self._gmail_signin
        )
        self.gmail_btn.grid(row=0, column=1, padx=(0, 24), pady=8)

        # GitHub Copilot
        gh_connected = bool(self.settings.get("github_token"))
        ctk.CTkLabel(self, text="Copilot:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=2, padx=(0, 4), pady=8)
        self.gh_btn = ctk.CTkButton(
            self,
            text="\u2705 Connected" if gh_connected else "Sign In",
            width=110, height=28, font=ctk.CTkFont(size=12),
            fg_color=("#2ecc71", "#27ae60") if gh_connected
            else ("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("#27ae60", "#219a52") if gh_connected
            else ("gray70", "gray40"),
            command=self._github_signin
        )
        self.gh_btn.grid(row=0, column=3, padx=(0, 24), pady=8)

        # Model selector
        ctk.CTkLabel(self, text="Model:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=4, padx=(0, 4), pady=8)
        current_model = self.settings.get("model", "gpt-4o")
        self.model_var = ctk.StringVar(value=current_model)
        self.model_menu = ctk.CTkOptionMenu(
            self,
            values=_FALLBACK_MODELS,   # populated with live data after sign-in
            variable=self.model_var,
            width=200, height=28,
            font=ctk.CTkFont(size=12),
            button_color=("gray75", "gray35"),
            button_hover_color=("gray65", "gray45"),
            fg_color=("gray85", "gray25"),
            text_color=("gray10", "gray90"),
            command=self._on_model_change
        )
        self.model_menu.grid(row=0, column=5, padx=(0, 16), pady=8, sticky="w")

        # If we already have a token, fetch models in the background
        if self.settings.get("github_token"):
            self._refresh_model_list(self.settings["github_token"])

    def _refresh_model_list(self, token: str):
        """Fetch live model list from GitHub Models API in a background thread."""
        def run():
            models = fetch_available_models(token)
            current = self.model_var.get()
            if current not in models:
                # Keep the current selection even if not in the new list
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
            # Now that we have a token, populate the model list
            self._refresh_model_list(token)

    def _on_model_change(self, value: str):
        self.settings["model"] = value
        self.save_settings_fn(self.settings)
