import customtkinter as ctk
import threading
from ui.file_upload_widget import FileUploadWidget


class MetricsPanel(ctk.CTkFrame):
    def __init__(self, parent, settings: dict):
        super().__init__(parent, fg_color="transparent")
        self.settings = settings
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self._build()

    def _build(self):
        title = ctk.CTkLabel(self, text="📊 Scrum Master – Metrics & Capacity",
                             font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, sticky="w", pady=(0, 16))

        # Mode selector
        mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        mode_frame.grid(row=1, column=0, sticky="w", pady=(0, 8))

        mode_label = ctk.CTkLabel(mode_frame, text="Analysis type:", font=ctk.CTkFont(size=13))
        mode_label.grid(row=0, column=0, padx=(0, 8))

        self.mode_var = ctk.StringVar(value="Velocity Review")
        mode_menu = ctk.CTkOptionMenu(
            mode_frame,
            values=["Velocity Review", "Capacity Planning"],
            variable=self.mode_var,
            width=200, height=32,
            font=ctk.CTkFont(size=13)
        )
        mode_menu.grid(row=0, column=1)

        # Input area
        input_label = ctk.CTkLabel(self, text="Paste sprint data or notes (optional if uploading files):",
                                   font=ctk.CTkFont(size=13))
        input_label.grid(row=2, column=0, sticky="w", pady=(8, 4))

        self.input_box = ctk.CTkTextbox(self, height=120, font=ctk.CTkFont(size=13), wrap="word")
        self.input_box.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        self.input_box.insert("1.0", "")

        # File upload
        self.file_upload = FileUploadWidget(self)
        self.file_upload.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        # Generate button
        self.generate_btn = ctk.CTkButton(
            self, text="⚡ Generate Metrics Report", height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._generate
        )
        self.generate_btn.grid(row=5, column=0, sticky="w", pady=(0, 8))

        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=13), text_color="gray")
        self.status_label.grid(row=6, column=0, sticky="w", pady=(0, 4))

        # Output
        output_label = ctk.CTkLabel(self, text="Report Output", font=ctk.CTkFont(size=13, weight="bold"))
        output_label.grid(row=7, column=0, sticky="w", pady=(8, 4))

        self.output_box = ctk.CTkTextbox(self, font=ctk.CTkFont(size=13), wrap="word")
        self.output_box.grid(row=8, column=0, sticky="nsew")
        self.output_box.configure(state="disabled")
        self.grid_rowconfigure(8, weight=1)

        copy_btn = ctk.CTkButton(
            self, text="📋 Copy", width=80, height=28,
            font=ctk.CTkFont(size=12), fg_color="transparent",
            border_width=1, command=self._copy_output
        )
        copy_btn.grid(row=9, column=0, sticky="e", pady=(4, 0))

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
            self.status_label.configure(text="⚠️ Please sign in to GitHub Copilot first.", text_color="orange")
            return

        text_input = self.input_box.get("1.0", "end").strip()
        files = self.file_upload.get_files()
        mode = self.mode_var.get()

        if not text_input and not files:
            self.status_label.configure(text="⚠️ Please enter data or attach files.", text_color="orange")
            return

        self.generate_btn.configure(state="disabled", text="Generating...")
        self.status_label.configure(text="⏳ Analysing sprint data...", text_color="gray")

        def run():
            try:
                from core.copilot_client import CopilotClient
                from core.file_processor import FileProcessor

                client = CopilotClient(token=token, model=self.settings.get("model", "gpt-4o"))
                processor = FileProcessor()

                system_prompt = self._get_system_prompt()
                user_content = []

                if text_input:
                    user_content.append({"type": "text", "text": f"Input data:\n{text_input}"})

                for file_path in files:
                    content = processor.process(file_path)
                    if content.get("type") == "image":
                        user_content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:{content['mime']};base64,{content['data']}"}
                        })
                    else:
                        user_content.append({"type": "text", "text": f"File: {file_path}\n{content['data']}"})

                if not user_content:
                    user_content.append({"type": "text", "text": "No data provided."})

                user_content.insert(0, {"type": "text", "text": f"Analysis type: {mode}"})

                result = client.complete_multimodal(system=system_prompt, content=user_content)
                self.after(0, lambda: self._set_output(result))
                self.after(0, lambda: self.status_label.configure(text="✅ Report generated.", text_color="#2ecc71"))
                self.after(0, lambda: self.generate_btn.configure(state="normal", text="⚡ Generate Metrics Report"))
            except Exception as e:
                self.after(0, lambda: self.status_label.configure(text=f"❌ Error: {e}", text_color="red"))
                self.after(0, lambda: self.generate_btn.configure(state="normal", text="⚡ Generate Metrics Report"))

        threading.Thread(target=run, daemon=True).start()

    def _get_system_prompt(self) -> str:
        return """You're looking at sprint delivery data with a focus on usable trend analysis and practical sprint planning.
Your job is to help the PM or Scrum Master understand what the recent numbers support, what the next sprint can realistically absorb, and where planning assumptions may be too optimistic.

Tone & Style:
- Be direct, practical, and data-led.
- Use plain language for the summary; numbers can go in the table.
- Be honest about uncertainty when the input is incomplete.
- Avoid alarm language unless the data clearly shows sustained delivery risk.

Output Rules:
- Velocity outputs must include: sprints analyzed, committed vs. completed values, rolling average, trend direction (improving/stable/declining), and a recommended commitment range for the next sprint.
- Capacity planning outputs must show who is available, who has reduced availability, total available person-days, a planning buffer, and the estimated usable story point range.
- Always include at least one concrete recommendation tied to the numbers.
- Velocity = story points completed, not started or in progress.
- Rolling average should use the last 3-5 sprints when available."""
