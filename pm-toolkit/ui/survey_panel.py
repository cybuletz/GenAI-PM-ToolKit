import customtkinter as ctk
import threading
import json
import os
import sys


class SurveyPanel(ctk.CTkFrame):
    def __init__(self, parent, settings: dict):
        super().__init__(parent, fg_color="transparent")
        self.settings = settings
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)
        self._build()

    def _build(self):
        title = ctk.CTkLabel(self, text="📋 Survey Agent", font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, sticky="w", pady=(0, 16))

        form = ctk.CTkFrame(self)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        form.grid_columnconfigure(1, weight=1)

        fields = [
            ("Survey Topic:", "e.g. Sprint 24 Retro, Team Health Check Q2"),
            ("Deadline:", "e.g. Friday EOD, June 20"),
            ("Recipients (comma-separated emails):", "alice@company.com, bob@company.com"),
        ]
        self.entries = {}
        for i, (label, placeholder) in enumerate(fields):
            lbl = ctk.CTkLabel(form, text=label, font=ctk.CTkFont(size=13))
            lbl.grid(row=i, column=0, sticky="w", padx=(12, 8), pady=8)
            entry = ctk.CTkEntry(form, placeholder_text=placeholder, height=36, font=ctk.CTkFont(size=13))
            entry.grid(row=i, column=1, sticky="ew", padx=(0, 12), pady=8)
            self.entries[i] = entry

        # Buttons row
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="w", pady=(0, 12))

        self.send_btn = ctk.CTkButton(
            btn_frame, text="📤 Send Survey", width=160, height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._send_survey
        )
        self.send_btn.grid(row=0, column=0, padx=(0, 12))

        self.collect_btn = ctk.CTkButton(
            btn_frame, text="📥 Collect Results", width=160, height=40,
            font=ctk.CTkFont(size=14),
            fg_color="gray50",
            command=self._collect_results
        )
        self.collect_btn.grid(row=0, column=1)

        # Status label
        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=13), text_color="gray")
        self.status_label.grid(row=3, column=0, sticky="w", pady=(0, 8))

        # Output area
        output_label = ctk.CTkLabel(self, text="Output", font=ctk.CTkFont(size=13, weight="bold"))
        output_label.grid(row=4, column=0, sticky="w", pady=(8, 4))

        self.output_box = ctk.CTkTextbox(self, font=ctk.CTkFont(size=13), wrap="word")
        self.output_box.grid(row=5, column=0, sticky="nsew")
        self.output_box.configure(state="disabled")

        copy_btn = ctk.CTkButton(
            self, text="📋 Copy", width=80, height=28,
            font=ctk.CTkFont(size=12), fg_color="transparent",
            border_width=1, command=self._copy_output
        )
        copy_btn.grid(row=6, column=0, sticky="e", pady=(4, 0))

    def _set_output(self, text: str):
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", text)
        self.output_box.configure(state="disabled")

    def _copy_output(self):
        text = self.output_box.get("1.0", "end").strip()
        self.clipboard_clear()
        self.clipboard_append(text)

    def _set_status(self, text: str, color: str = "gray"):
        self.status_label.configure(text=text, text_color=color)

    def _send_survey(self):
        topic = self.entries[0].get().strip()
        deadline = self.entries[1].get().strip() or "end of this week"
        emails = self.entries[2].get().strip()

        if not topic:
            self._set_status("⚠️ Please enter a survey topic.", "orange")
            return
        if not emails:
            self._set_status("⚠️ Please enter at least one email.", "orange")
            return

        self.send_btn.configure(state="disabled", text="Sending...")
        self._set_status("⏳ Generating questions and creating form...", "gray")

        def run():
            try:
                questions = self._generate_questions(topic)
                questions_path = self._write_questions(questions)
                email_list = [e.strip() for e in emails.split(",") if e.strip()]

                # Import and call survey.py logic directly — no shell commands
                survey_dir = os.path.join(os.path.dirname(__file__), "..", "..", "tools", "survey")
                survey_dir = os.path.abspath(survey_dir)
                sys.path.insert(0, survey_dir)

                from survey import authenticate, create_form, send_emails, save_form_metadata
                from googleapiclient.discovery import build

                creds = authenticate()
                forms_service = build("forms", "v1", credentials=creds)
                gmail_service = build("gmail", "v1", credentials=creds)

                form_id, form_url = create_form(forms_service, topic, questions)
                send_emails(gmail_service, email_list, topic, form_url, deadline)
                save_form_metadata(form_id, form_url, topic, email_list, deadline)

                self.after(0, lambda: self._set_status("✅ Survey sent successfully!", "#2ecc71"))
                self.after(0, lambda: self._set_output(
                    f"✅ Survey created and sent!\n\n"
                    f"Topic: {topic}\n"
                    f"Deadline: {deadline}\n"
                    f"Recipients: {', '.join(email_list)}\n\n"
                    f"🔗 Form URL:\n{form_url}\n\n"
                    f"Questions sent:\n" +
                    "\n".join(f"  {i+1}. {q['text']}" for i, q in enumerate(questions))
                ))
                self.after(0, lambda: self.send_btn.configure(state="normal", text="📤 Send Survey"))
            except Exception as e:
                self.after(0, lambda: self._set_status(f"❌ Error: {e}", "red"))
                self.after(0, lambda: self.send_btn.configure(state="normal", text="📤 Send Survey"))

        threading.Thread(target=run, daemon=True).start()

    def _collect_results(self):
        self.collect_btn.configure(state="disabled", text="Collecting...")
        self._set_status("⏳ Fetching responses...", "gray")

        def run():
            try:
                survey_dir = os.path.join(os.path.dirname(__file__), "..", "..", "tools", "survey")
                survey_dir = os.path.abspath(survey_dir)
                sys.path.insert(0, survey_dir)

                import importlib
                import collect_responses as cr
                importlib.reload(cr)

                meta_path = os.path.join(survey_dir, "form_meta.json")
                if not os.path.exists(meta_path):
                    self.after(0, lambda: self._set_status("❌ No form found. Send a survey first.", "red"))
                    self.after(0, lambda: self.collect_btn.configure(state="normal", text="📥 Collect Results"))
                    return

                with open(meta_path) as f:
                    meta = json.load(f)

                cr.collect(meta["form_id"])

                responses_path = os.path.join(survey_dir, "responses.json")
                with open(responses_path) as f:
                    responses = json.load(f)

                report = self._build_report(meta, responses)
                self.after(0, lambda: self._set_output(report))
                self.after(0, lambda: self._set_status(f"✅ {len(responses)} response(s) collected.", "#2ecc71"))
                self.after(0, lambda: self.collect_btn.configure(state="normal", text="📥 Collect Results"))
            except Exception as e:
                self.after(0, lambda: self._set_status(f"❌ Error: {e}", "red"))
                self.after(0, lambda: self.collect_btn.configure(state="normal", text="📥 Collect Results"))

        threading.Thread(target=run, daemon=True).start()

    def _generate_questions(self, topic: str) -> list:
        """
        Calls GitHub Models API to generate 5 relevant questions for the given topic.
        Falls back to generic questions if no GitHub token is set.
        """
        token = self.settings.get("github_token", "")
        model = self.settings.get("model", "gpt-4o")

        if token:
            try:
                from core.copilot_client import CopilotClient
                client = CopilotClient(token=token, model=model)
                prompt = (
                    f"Generate exactly 5 survey questions for a PM team survey about: '{topic}'.\n"
                    "Rules:\n"
                    "- 2 scale questions (rating 1-5)\n"
                    "- 2 multiple choice questions (provide 3-4 options each)\n"
                    "- 1 open text question\n"
                    "Return ONLY valid JSON array, no markdown, no explanation.\n"
                    "Format: [{\"text\": \"...\", \"type\": \"scale\" | \"multiple_choice\" | \"text\", \"options\": [\"...\"] }]\n"
                    "options field only required for multiple_choice type."
                )
                response = client.complete(system="You are a survey designer for project management teams.", user=prompt)
                # Strip markdown code fences if present
                clean = response.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
                return json.loads(clean)
            except Exception:
                pass

        # Fallback generic questions
        return [
            {"text": f"How satisfied are you with the team's progress on {topic}?", "type": "scale"},
            {"text": "How effective was communication within the team?", "type": "scale"},
            {"text": "What was the biggest blocker this sprint?", "type": "multiple_choice",
             "options": ["Technical debt", "Unclear requirements", "External dependencies", "Team capacity"]},
            {"text": "How would you rate the sprint planning quality?", "type": "multiple_choice",
             "options": ["Excellent", "Good", "Needs improvement", "Poor"]},
            {"text": "What one change would most improve how we work together?", "type": "text"},
        ]

    def _write_questions(self, questions: list) -> str:
        survey_dir = os.path.join(os.path.dirname(__file__), "..", "..", "tools", "survey")
        survey_dir = os.path.abspath(survey_dir)
        path = os.path.join(survey_dir, "questions.json")
        with open(path, "w") as f:
            json.dump(questions, f, indent=2)
        return path

    def _build_report(self, meta: dict, responses: list) -> str:
        if not responses:
            return "⚠️ No responses yet. Check back later."

        lines = [
            f"Survey Results: {meta.get('title', 'N/A')}",
            f"={'='*50}",
            f"📊 Participation: {len(responses)} response(s)",
            "",
        ]

        # Aggregate answers
        aggregated = {}
        for r in responses:
            for question, answers in r.get("answers", {}).items():
                if question not in aggregated:
                    aggregated[question] = []
                aggregated[question].extend(answers)

        for question, answers in aggregated.items():
            lines.append(f"Q: {question}")
            # Try numeric average for scale questions
            try:
                nums = [float(a) for a in answers]
                avg = sum(nums) / len(nums)
                lines.append(f"   Average score: {avg:.1f} / 5")
            except (ValueError, ZeroDivisionError):
                from collections import Counter
                counts = Counter(answers)
                for val, count in counts.most_common():
                    lines.append(f"   {val}: {count} response(s)")
            lines.append("")

        return "\n".join(lines)
