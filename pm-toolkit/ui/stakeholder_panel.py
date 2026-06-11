import customtkinter as ctk
import threading
import os
from ui.file_upload_widget import FileUploadWidget

# Path to the instructions file — loaded at runtime so it stays in sync
_INSTRUCTIONS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..",
    ".github", "instructions",
    "stakeholder-communicator-reporter.instructions.md"
)


def _load_instructions() -> str:
    """Load the stakeholder instructions file, stripping the YAML front-matter."""
    try:
        path = os.path.abspath(_INSTRUCTIONS_PATH)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        # Strip YAML front-matter (--- ... ---)
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                content = content[end + 3:].strip()
        return content
    except Exception:
        # Fallback if file not found
        return (
            "You help a project manager communicate project status to stakeholders. "
            "Be professional, concise, and lead with the key message."
        )


class StakeholderPanel(ctk.CTkFrame):
    def __init__(self, parent, settings: dict):
        super().__init__(parent, fg_color="transparent")
        self.settings = settings
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(8, weight=1)
        self._build()

    def _build(self):
        title = ctk.CTkLabel(self, text="\U0001f4e2 Stakeholder Communicator",
                             font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, sticky="w", pady=(0, 16))

        # Report type — two options only
        type_frame = ctk.CTkFrame(self, fg_color="transparent")
        type_frame.grid(row=1, column=0, sticky="w", pady=(0, 8))

        ctk.CTkLabel(type_frame, text="Report type:",
                     font=ctk.CTkFont(size=13)).grid(row=0, column=0, padx=(0, 8))

        self.type_var = ctk.StringVar(value="Executive Status Report")
        ctk.CTkOptionMenu(
            type_frame,
            values=["Executive Status Report", "Executive Summary"],
            variable=self.type_var,
            width=220, height=32,
            font=ctk.CTkFont(size=13)
        ).grid(row=0, column=1)

        # Input
        ctk.CTkLabel(
            self,
            text="Paste context, sprint notes, email threads, or bullet points:",
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
            self, text="\u270d\ufe0f Generate Update", height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._generate
        )
        self.generate_btn.grid(row=5, column=0, sticky="w", pady=(0, 8))

        self.status_label = ctk.CTkLabel(self, text="",
                                         font=ctk.CTkFont(size=13), text_color="gray")
        self.status_label.grid(row=6, column=0, sticky="w", pady=(0, 4))

        ctk.CTkLabel(self, text="Generated Update",
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
        report_type = self.type_var.get()

        if not text_input and not files:
            self.status_label.configure(
                text="\u26a0\ufe0f Please enter context or attach files.",
                text_color="orange")
            return

        self.generate_btn.configure(state="disabled", text="Generating...")
        self.status_label.configure(text="\u23f3 Drafting stakeholder update...",
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
                    {"type": "text",
                     "text": f"Produce a: {report_type}"}
                ]

                if text_input:
                    user_content.append(
                        {"type": "text", "text": f"Input:\n{text_input}"}
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
                    text="\u2705 Update generated.", text_color="#2ecc71"))
                self.after(0, lambda: self.generate_btn.configure(
                    state="normal", text="\u270d\ufe0f Generate Update"))
            except Exception as e:
                self.after(0, lambda: self.status_label.configure(
                    text=f"\u274c Error: {e}", text_color="red"))
                self.after(0, lambda: self.generate_btn.configure(
                    state="normal", text="\u270d\ufe0f Generate Update"))

        threading.Thread(target=run, daemon=True).start()
