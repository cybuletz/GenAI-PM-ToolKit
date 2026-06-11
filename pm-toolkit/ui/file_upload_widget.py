import customtkinter as ctk
from tkinter import filedialog
import os

ACCEPTED_EXTENSIONS = (
    ".pdf", ".docx", ".txt", ".md", ".csv", ".xlsx",
    ".py", ".ts", ".js", ".json", ".yaml", ".yml", ".xml",
    ".png", ".jpg", ".jpeg", ".gif", ".webp"
)

ACCEPT_FILETYPES = [
    ("All supported", "*.pdf *.docx *.txt *.md *.csv *.xlsx *.py *.ts *.js *.json *.yaml *.yml *.xml *.png *.jpg *.jpeg *.gif *.webp"),
    ("Documents", "*.pdf *.docx *.txt *.md"),
    ("Spreadsheets", "*.csv *.xlsx"),
    ("Images", "*.png *.jpg *.jpeg *.gif *.webp"),
    ("Code", "*.py *.ts *.js *.json *.yaml *.yml *.xml"),
]

MAX_VISIBLE_CHIPS = 6  # chips per row before wrapping


class FileUploadWidget(ctk.CTkFrame):
    """Attach-files bar with wrapping chips. Always visible; no stretch."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.files: list[str] = []
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew")
        top.grid_columnconfigure(1, weight=1)

        attach_btn = ctk.CTkButton(
            top, text="📎 Attach Files", width=130, height=32,
            font=ctk.CTkFont(size=13),
            fg_color="transparent", border_width=1,
            command=self._browse_files
        )
        attach_btn.grid(row=0, column=0, padx=(0, 8))

        self.hint_label = ctk.CTkLabel(
            top,
            text="Supported: PDF, DOCX, TXT, MD, CSV, XLSX, images, code files",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.hint_label.grid(row=0, column=1, sticky="w")

        # Chip container — uses pack layout inside so chips wrap naturally
        self.chip_outer = ctk.CTkFrame(self, fg_color="transparent")
        self.chip_outer.grid(row=1, column=0, sticky="ew", pady=(6, 0))

    def _browse_files(self):
        paths = filedialog.askopenfilenames(filetypes=ACCEPT_FILETYPES)
        for path in paths:
            if path not in self.files:
                ext = os.path.splitext(path)[1].lower()
                if ext in ACCEPTED_EXTENSIONS:
                    self.files.append(path)
        self._refresh_chips()

    def _refresh_chips(self):
        for widget in self.chip_outer.winfo_children():
            widget.destroy()

        for path in self.files:
            filename = os.path.basename(path)
            chip = ctk.CTkFrame(self.chip_outer, corner_radius=6)
            # Use pack so chips flow left-to-right and wrap to next line
            chip.pack(side="left", padx=(0, 6), pady=2)

            name_label = ctk.CTkLabel(chip, text=filename, font=ctk.CTkFont(size=12), padx=6)
            name_label.pack(side="left")

            remove_btn = ctk.CTkButton(
                chip, text="✕", width=20, height=20,
                font=ctk.CTkFont(size=11),
                fg_color="transparent",
                hover_color="gray30",
                command=lambda p=path: self._remove_file(p)
            )
            remove_btn.pack(side="left", padx=(0, 4))

    def _remove_file(self, path: str):
        if path in self.files:
            self.files.remove(path)
        self._refresh_chips()

    def get_files(self) -> list[str]:
        return list(self.files)
