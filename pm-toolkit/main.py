import customtkinter as ctk
from ui.app import PMToolkitApp
import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")


def load_settings():
    defaults = {"theme": "System", "model": "gpt-4o", "github_token": "", "gmail_token_path": ""}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            saved = json.load(f)
        defaults.update(saved)
    return defaults


def save_settings(settings: dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


if __name__ == "__main__":
    settings = load_settings()
    ctk.set_appearance_mode(settings.get("theme", "System"))
    ctk.set_default_color_theme("blue")
    app = PMToolkitApp(settings=settings, save_settings_fn=save_settings)
    app.mainloop()
