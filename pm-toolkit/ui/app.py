import customtkinter as ctk
from ui.survey_panel import SurveyPanel
from ui.metrics_panel import MetricsPanel
from ui.stakeholder_panel import StakeholderPanel
from ui.profile_panel import ProfilePanel
from ui.settings_bar import SettingsBar


class PMToolkitApp(ctk.CTk):
    def __init__(self, settings: dict, save_settings_fn):
        super().__init__()
        self.settings = settings
        self.save_settings_fn = save_settings_fn

        self.title("PM Toolkit")
        self.geometry("1100x720")
        self.minsize(900, 600)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)
        self._build_sidebar()

        # Main content area
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Settings bar at bottom
        self.settings_bar = SettingsBar(
            self,
            settings=self.settings,
            save_settings_fn=self.save_settings_fn,
            on_theme_change=self._on_theme_change
        )
        self.settings_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        # Panels
        self.panels = {}
        self.panels["survey"] = SurveyPanel(self.content_frame, settings=self.settings)
        self.panels["metrics"] = MetricsPanel(self.content_frame, settings=self.settings)
        self.panels["stakeholder"] = StakeholderPanel(self.content_frame, settings=self.settings)
        self.panels["profile"] = ProfilePanel(self.content_frame, settings=self.settings)

        self._show_panel("survey")

    def _build_sidebar(self):
        logo_label = ctk.CTkLabel(
            self.sidebar, text="🧰 PM Toolkit",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        logo_label.grid(row=0, column=0, padx=16, pady=(24, 32))

        nav_items = [
            ("📋  Survey", "survey"),
            ("📊  Metrics", "metrics"),
            ("📢  Stakeholder", "stakeholder"),
            ("👤  Profile", "profile"),
        ]
        self.nav_buttons = {}
        for i, (label, key) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25"),
                font=ctk.CTkFont(size=14),
                command=lambda k=key: self._show_panel(k)
            )
            btn.grid(row=i, column=0, padx=8, pady=4, sticky="ew")
            self.nav_buttons[key] = btn

        # Theme toggle
        self.theme_var = ctk.StringVar(value=self.settings.get("theme", "System"))
        theme_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["System", "Light", "Dark"],
            variable=self.theme_var,
            command=self._on_theme_change,
            width=140
        )
        theme_menu.grid(row=11, column=0, padx=16, pady=(0, 16), sticky="s")

    def _show_panel(self, key: str):
        for k, panel in self.panels.items():
            panel.grid_remove()
        self.panels[key].grid(row=0, column=0, sticky="nsew")
        # Highlight active nav button
        for k, btn in self.nav_buttons.items():
            btn.configure(fg_color=("gray75", "gray35") if k == key else "transparent")
        self.active_panel = key

    def _on_theme_change(self, value: str):
        ctk.set_appearance_mode(value)
        self.settings["theme"] = value
        self.save_settings_fn(self.settings)
