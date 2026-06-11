import customtkinter as ctk
import threading
import os
from ui.file_upload_widget import FileUploadWidget

# Load system prompt from the original instructions file at runtime
_INSTRUCTIONS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..",
    ".github", "instructions",
    "scrum-master-metrics.instructions.md"
)


def _load_instructions() -> str:
    """Load the scrum master instructions file, stripping YAML front-matter."""
    try:
        path = os.path.abspath(_INSTRUCTIONS_PATH)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                content = content[end + 3:].strip()
        return content
    except Exception:
        return (
            "You analyse sprint delivery data to help the PM or Scrum Master "
            "understand velocity trends and plan capacity realistically."
        )


class MetricsPanel(ctk.CTkFrame):
    def __init__(self, parent, settings: dict):
        super().__init__(parent, fg_color="transparent")
        self.settings = settings
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(8, weight=1)
        self._build()

    def _build(self):
        title = ctk.CTkLabel(self, text="\U0001f4ca Scrum Master \u2013 Metrics & Capacity",
                             font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, sticky="w", pady=(0, 16))

        # Mode selector
        mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        mode_frame.grid(row=1, column=0, sticky="w", pady=(0, 8))

        ctk.CTkLabel(mode_frame, text="Analysis type:",
                     font=ctk.CTkFont(size=13)).grid(row=0, column=0, padx=(0, 8))

        self.mode_var = ctk.StringVar(value="Velocity Review")
        ctk.CTkOptionMenu(
            mode_frame,
            values=["Velocity Review", "Capacity Planning"],
            variable=self.mode_var,
            width=200, height=32,
            font=ctk.CTkFont(size=13)
        ).grid(row=0, column=1)

        # Input
        ctk.CTkLabel(
            self,
            text="Paste sprint data or notes (optional if uploading files):",
            font=ctk.CTkFont(size=13)
        ).grid(row=2, column=0, sticky="w", pady=(8, 4))

        self.input_box = ctk.CTkTextbox(self, height=120,
                                        font=ctk.CTkFont(size=13), wrap="word")
        self.input_box.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        # File upload
        self.file_upload = FileUploadWidget(self)
        self.file_upload.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        # Generate
        self.generate_btn = ctk.CTkButton(
            self, text="\u26a1 Generate Metrics Report", height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._generate
        )
        self.generate_btn.grid(row=5, column=0, sticky="w", pady=(0, 8))

        self.status_label = ctk.CTkLabel(self, text="",
                                         font=ctk.CTkFont(size=13), text_color="gray")
        self.status_label.grid(row=6, column=0, sticky="w", pady=(0, 4))

        ctk.CTkLabel(self, text="Report Output",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=7, column=0, sticky="w", pady=(8, 4))

        self.output_box = ctk.CTkTextbox(self, font=ctk.CTkFont(size=13), wrap="word")
        self.output_box.grid(row=8, column=0, sticky="nsew")
        self.output_box.configure(state="disabled")

        ctk.CTkButton(
            self, text="\U0001f4cb Copy", width=80, height=28,
            font=ctk.CTkFont(size=12), fg_color="transparent",
            border_width=1, command=self._copy_output
        ).grid(row=9, column=0, sticky="e", pady=(4, 0))

    def _set_output(self, text: str):
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", text)
        self.output_box.configure(state="disabled")

    def _copy_output(self):
        text = self.output_box.get("1.0", "end").strip()
        self.clipboard_clear()
        self.clipboard_append(text)

    def _generate(self):
        token = self.settings.get("github_token", "")
        if not token:
            self.status_label.configure(
                text="\u26a0\ufe0f Please sign in to GitHub Copilot first.",
                text_color="orange")
            return

        text_input = self.input_box.get("1.0", "end").strip()
        files = self.file_upload.get_files()
        mode = self.mode_var.get()

        if not text_input and not files:
            self.status_label.configure(
                text="\u26a0\ufe0f Please enter data or attach files.",
                text_color="orange")
            return

        self.generate_btn.configure(state="disabled", text="Generating...")
        self.status_label.configure(text="\u23f3 Analysing sprint data...",
                                    text_color="gray")

        def run():
            try:
                from core.copilot_client import CopilotClient
                from core.file_processor import FileProcessor

                client = CopilotClient(
                    token=token,
                    model=self.settings.get("model", "gpt-4o")
                )
                processor = FileProcessor()

                # Load instructions live from file
                system_prompt = _load_instructions()

                user_content = [
                    {"type": "text", "text": f"Analysis type: {mode}"}
                ]

                if text_input:
                    user_content.append(
                        {"type": "text", "text": f"Input data:\n{text_input}"}
                    )

                for file_path in files:
                    content = processor.process(file_path)
                    if content.get("type") == "image":
                        user_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{content['mime']};base64,{content['data']}"
                            }
                        })
                    else:
                        user_content.append(
                            {"type": "text",
                             "text": f"File: {file_path}\n{content['data']}"}
                        )

                result = client.complete_multimodal(
                    system=system_prompt, content=user_content)
                self.after(0, lambda: self._set_output(result))
                self.after(0, lambda: self.status_label.configure(
                    text="\u2705 Report generated.", text_color="#2ecc71"))
                self.after(0, lambda: self.generate_btn.configure(
                    state="normal", text="\u26a1 Generate Metrics Report"))
            except Exception as e:
                self.after(0, lambda: self.status_label.configure(
                    text=f"\u274c Error: {e}", text_color="red"))
                self.after(0, lambda: self.generate_btn.configure(
                    state="normal", text="\u26a1 Generate Metrics Report"))

        threading.Thread(target=run, daemon=True).start()
