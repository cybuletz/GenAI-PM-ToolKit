import customtkinter as ctk
import threading
from ui.file_upload_widget import FileUploadWidget


class StakeholderPanel(ctk.CTkFrame):
    def __init__(self, parent, settings: dict):
        super().__init__(parent, fg_color="transparent")
        self.settings = settings
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self._build()

    def _build(self):
        title = ctk.CTkLabel(self, text="📢 Stakeholder Communicator",
                             font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, sticky="w", pady=(0, 16))

        # Report type selector
        type_frame = ctk.CTkFrame(self, fg_color="transparent")
        type_frame.grid(row=1, column=0, sticky="w", pady=(0, 8))

        type_label = ctk.CTkLabel(type_frame, text="Report type:", font=ctk.CTkFont(size=13))
        type_label.grid(row=0, column=0, padx=(0, 8))

        self.type_var = ctk.StringVar(value="Executive Status Report")
        type_menu = ctk.CTkOptionMenu(
            type_frame,
            values=[
                "Executive Status Report",
                "Sprint Summary",
                "Meeting Follow-Up",
                "Milestone Announcement",
                "Executive Summary",
            ],
            variable=self.type_var,
            width=220, height=32,
            font=ctk.CTkFont(size=13)
        )
        type_menu.grid(row=0, column=1, padx=(0, 16))

        audience_label = ctk.CTkLabel(type_frame, text="Audience:", font=ctk.CTkFont(size=13))
        audience_label.grid(row=0, column=2, padx=(0, 8))

        self.audience_var = ctk.StringVar(value="Executive / C-level")
        audience_menu = ctk.CTkOptionMenu(
            type_frame,
            values=["Executive / C-level", "Client / External", "Sponsor", "Technical Lead", "Board"],
            variable=self.audience_var,
            width=180, height=32,
            font=ctk.CTkFont(size=13)
        )
        audience_menu.grid(row=0, column=3)

        # Input area
        input_label = ctk.CTkLabel(self, text="Paste context, sprint notes, email threads, or bullet points:",
                                   font=ctk.CTkFont(size=13))
        input_label.grid(row=2, column=0, sticky="w", pady=(8, 4))

        self.input_box = ctk.CTkTextbox(self, height=120, font=ctk.CTkFont(size=13), wrap="word")
        self.input_box.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        # File upload
        self.file_upload = FileUploadWidget(self)
        self.file_upload.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        # Generate button
        self.generate_btn = ctk.CTkButton(
            self, text="✍️ Generate Update", height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._generate
        )
        self.generate_btn.grid(row=5, column=0, sticky="w", pady=(0, 8))

        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=13), text_color="gray")
        self.status_label.grid(row=6, column=0, sticky="w", pady=(0, 4))

        # Output
        output_label = ctk.CTkLabel(self, text="Generated Update", font=ctk.CTkFont(size=13, weight="bold"))
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
        report_type = self.type_var.get()
        audience = self.audience_var.get()

        if not text_input and not files:
            self.status_label.configure(text="⚠️ Please enter context or attach files.", text_color="orange")
            return

        self.generate_btn.configure(state="disabled", text="Generating...")
        self.status_label.configure(text="⏳ Drafting stakeholder update...", text_color="gray")

        def run():
            try:
                from core.copilot_client import CopilotClient
                from core.file_processor import FileProcessor

                client = CopilotClient(token=token, model=self.settings.get("model", "gpt-4o"))
                processor = FileProcessor()

                system_prompt = self._get_system_prompt()
                user_content = []
                user_content.append({"type": "text", "text": f"Report type: {report_type}\nAudience: {audience}"})

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

                result = client.complete_multimodal(system=system_prompt, content=user_content)
                self.after(0, lambda: self._set_output(result))
                self.after(0, lambda: self.status_label.configure(text="✅ Update generated.", text_color="#2ecc71"))
                self.after(0, lambda: self.generate_btn.configure(state="normal", text="✍️ Generate Update"))
            except Exception as e:
                self.after(0, lambda: self.status_label.configure(text=f"❌ Error: {e}", text_color="red"))
                self.after(0, lambda: self.generate_btn.configure(state="normal", text="✍️ Generate Update"))

        threading.Thread(target=run, daemon=True).start()

    def _get_system_prompt(self) -> str:
        return """You help a project manager communicate project status to stakeholders who don't read sprint boards.
Your job is translation: take technical team output and turn it into clear, relevant updates for business people.

Tone & Style:
- Professional but readable. Stakeholders are busy — make every sentence count.
- Active voice. Short paragraphs.
- Never use sprint jargon in the final output unless the audience is also Scrum-familiar.
- Lead with the key message — don't bury the headline.

Output Rules:
- Status Reports: Start with a one-line status: On Track / At Risk / Needs Attention. Include what was delivered, what's coming next, any open risks. Keep under one page.
- Executive Summaries: Three paragraphs max: What happened, What it means for the business, What comes next.
- Milestone Announcements: Lead with milestone name and date. One sentence on why it matters. One sentence on what's next.
- Meeting Follow-Ups: List decisions made, action items with owner and deadline, open questions.

What to Avoid:
- Don't use phrases like 'the team is working hard' — show outcomes instead.
- Don't include raw metrics (velocity, story points) unless specifically asked.
- Never sugarcoat a risk or slip — just frame it clearly with mitigation context."""
