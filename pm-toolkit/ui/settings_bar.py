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
    Call the GitHub Models catalogue endpoint and return all model IDs.
    Falls back to _FALLBACK_MODELS on any error.
    """
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


class _MSClientIDDialog(ctk.CTkToplevel):
    """Dialog to enter the Azure App Client ID for Microsoft 365 sign-in."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Microsoft 365 \u2013 Sign In")
        self.geometry("520x300")
        self.resizable(False, False)
        self.grab_set()
        self.result: str = ""
        self._build()

    def _build(self):
        pad = {"padx": 24, "pady": 8}
        ctk.CTkLabel(
            self,
            text="Enter your Azure App (Client) ID",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(**pad, anchor="w")
        ctk.CTkLabel(
            self,
            text=(
                "Register a public-client app at portal.azure.com\n"
                "  \u2022 Redirect URI: http://localhost  (Mobile/Desktop)\n"
                "  \u2022 Delegated scopes: Mail.Send, Files.ReadWrite.AppFolder, User.Read\n"
                "Paste the Application (client) ID below:"
            ),
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="left"
        ).pack(padx=24, pady=(0, 8), anchor="w")
        self.entry = ctk.CTkEntry(
            self, width=460, height=36,
            font=ctk.CTkFont(size=13),
            placeholder_text="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        )
        self.entry.pack(padx=24, pady=(0, 4))
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=24, fill="x", pady=(12, 0))
        ctk.CTkButton(
            btn_frame, text="Sign In", width=110, height=34,
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
        cid = self.entry.get().strip()
        if cid:
            self.result = cid
        self.destroy()


class SettingsBar(ctk.CTkFrame):
    def __init__(self, parent, settings: dict, save_settings_fn, on_theme_change):
        super().__init__(parent, height=48, corner_radius=0)
        self.settings = settings
        self.save_settings_fn = save_settings_fn
        self.on_theme_change = on_theme_change
        # 8 columns: Gmail label/btn, M365 label/btn, Copilot label/btn, Model label/menu
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
            fg_color=("\u2705 Connected" and ("#2ecc71", "#27ae60")
                      if gmail_connected else ("gray80", "gray30")),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray40"),
            command=self._gmail_signin
        )
        # Correct the fg_color expression
        self.gmail_btn.configure(
            fg_color=("#2ecc71", "#27ae60") if gmail_connected else ("gray80", "gray30"),
            hover_color=("\u2705 Connected" and ("#27ae60", "#219a52")
                         if gmail_connected else ("gray70", "gray40"))
        )
        self.gmail_btn.configure(
            hover_color=("#27ae60", "#219a52") if gmail_connected else ("gray70", "gray40")
        )
        self.gmail_btn.grid(row=0, column=1, padx=(0, 24), pady=8)

        # ---- Microsoft 365 ------------------------------------------- #
        ms_connected = bool(self.settings.get("ms_client_id"))
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
        dialog = _MSClientIDDialog(self)
        self.wait_window(dialog)
        client_id = dialog.result
        if not client_id:
            return

        def do_auth():
            try:
                import os
                os.environ["MS_CLIENT_ID"] = client_id
                from core.microsoft_auth import MicrosoftAuth
                auth = MicrosoftAuth(client_id=client_id)
                auth.authenticate()          # opens browser once; caches token
                self.settings["ms_client_id"] = client_id
                self.save_settings_fn(self.settings)
                self.after(0, lambda: self.ms_btn.configure(
                    text="\u2705 Connected",
                    fg_color=("#2ecc71", "#27ae60"),
                    hover_color=("#27ae60", "#219a52"),
                    text_color=("gray10", "gray90"),
                ))
            except Exception as e:
                self.after(0, lambda: self.ms_btn.configure(
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
            self._refresh_model_list(token)

    def _on_model_change(self, value: str):
        self.settings["model"] = value
        self.save_settings_fn(self.settings)
