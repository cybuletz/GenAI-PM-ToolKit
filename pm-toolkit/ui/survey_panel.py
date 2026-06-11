import customtkinter as ctk
import threading
import json
import os
import sys
from datetime import datetime, timezone

# Must match tools/survey/survey.py exactly so token.json is always valid
_SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.send",
]


class SurveyPanel(ctk.CTkFrame):
    def __init__(self, parent, settings: dict):
        super().__init__(parent, fg_color="transparent")
        self.settings = settings
        self._creds = None
        self._store = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build()

    # ------------------------------------------------------------------ #
    #  Build UI                                                            #
    # ------------------------------------------------------------------ #

    def _build(self):
        self.tab_view = ctk.CTkTabview(self, height=600)
        self.tab_view.grid(row=0, column=0, sticky="nsew")
        self.tab_view.add("New Survey")
        self.tab_view.add("History")
        self._build_new_tab(self.tab_view.tab("New Survey"))
        self._build_history_tab(self.tab_view.tab("History"))

    # ---- New Survey tab ------------------------------------------------ #

    def _build_new_tab(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(parent, text="\U0001f4cb Survey Agent",
                     font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 16))

        form = ctk.CTkFrame(parent)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        form.grid_columnconfigure(1, weight=1)

        fields = [
            ("Survey Topic:", "e.g. Sprint 24 Retro, Team Health Check Q2"),
            ("Deadline:", "e.g. Friday EOD, June 20"),
            ("Recipients (comma-separated emails):", "alice@company.com, bob@company.com"),
        ]
        self.entries = {}
        for i, (label, placeholder) in enumerate(fields):
            ctk.CTkLabel(form, text=label, font=ctk.CTkFont(size=13)).grid(
                row=i, column=0, sticky="w", padx=(12, 8), pady=8)
            entry = ctk.CTkEntry(form, placeholder_text=placeholder,
                                 height=36, font=ctk.CTkFont(size=13))
            entry.grid(row=i, column=1, sticky="ew", padx=(0, 12), pady=8)
            self.entries[i] = entry

        self.send_btn = ctk.CTkButton(
            parent, text="\U0001f4e4 Send Survey", width=160, height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._send_survey
        )
        self.send_btn.grid(row=2, column=0, sticky="w", pady=(0, 12))

        self.new_status = ctk.CTkLabel(parent, text="",
                                       font=ctk.CTkFont(size=13), text_color="gray")
        self.new_status.grid(row=3, column=0, sticky="w", pady=(0, 8))

        ctk.CTkLabel(parent, text="Output",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=4, column=0, sticky="w", pady=(8, 4))

        self.new_output = ctk.CTkTextbox(parent, font=ctk.CTkFont(size=13), wrap="word")
        self.new_output.grid(row=5, column=0, sticky="nsew")
        self.new_output.configure(state="disabled")

        ctk.CTkButton(
            parent, text="\U0001f4cb Copy", width=80, height=28,
            font=ctk.CTkFont(size=12),
            fg_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray40"),
            command=lambda: self._copy(self.new_output)
        ).grid(row=6, column=0, sticky="e", pady=(4, 0))

    # ---- History tab --------------------------------------------------- #

    def _build_history_tab(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            top, text="\U0001f504 Refresh", width=110, height=32,
            font=ctk.CTkFont(size=13),
            fg_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray40"),
            command=self._load_history
        ).grid(row=0, column=0, padx=(0, 12))

        self.hist_status = ctk.CTkLabel(top, text="",
                                        font=ctk.CTkFont(size=12), text_color="gray")
        self.hist_status.grid(row=0, column=1, sticky="w")

        # Scrollable survey list
        self.survey_list_frame = ctk.CTkScrollableFrame(parent, label_text="")
        self.survey_list_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        self.survey_list_frame.grid_columnconfigure(0, weight=1)

        # Analysis section
        analysis_frame = ctk.CTkFrame(parent)
        analysis_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        analysis_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(analysis_frame, text="Analysis:",
                     font=ctk.CTkFont(size=13)).grid(
            row=0, column=0, padx=(12, 8), pady=10, sticky="w")

        self.analysis_mode = ctk.StringVar(value="This survey only")
        mode_menu = ctk.CTkOptionMenu(
            analysis_frame,
            values=["This survey only", "Trend across last X surveys"],
            variable=self.analysis_mode,
            width=220, height=32,
            font=ctk.CTkFont(size=13),
            button_color=("gray75", "gray35"),
            button_hover_color=("gray65", "gray45"),
            fg_color=("gray85", "gray25"),
            text_color=("gray10", "gray90"),
            command=self._on_mode_change
        )
        mode_menu.grid(row=0, column=1, sticky="w", pady=10)

        self.trend_label = ctk.CTkLabel(analysis_frame, text="Last X surveys:",
                                        font=ctk.CTkFont(size=13))
        self.trend_label.grid(row=0, column=2, padx=(16, 4), pady=10)
        self.trend_label.grid_remove()

        self.trend_x = ctk.CTkEntry(analysis_frame, width=60, height=32,
                                    font=ctk.CTkFont(size=13))
        self.trend_x.insert(0, "3")
        self.trend_x.grid(row=0, column=3, padx=(0, 12), pady=10)
        self.trend_x.grid_remove()

        self.analyse_btn = ctk.CTkButton(
            analysis_frame, text="\U0001f50d Analyse", width=120, height=32,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._analyse
        )
        self.analyse_btn.grid(row=0, column=4, padx=(0, 12), pady=10)

        ctk.CTkLabel(parent, text="Analysis Output",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=3, column=0, sticky="w", pady=(4, 4))

        self.hist_output = ctk.CTkTextbox(parent, height=200,
                                          font=ctk.CTkFont(size=13), wrap="word")
        self.hist_output.grid(row=4, column=0, sticky="nsew")
        self.hist_output.configure(state="disabled")
        parent.grid_rowconfigure(4, weight=1)

        ctk.CTkButton(
            parent, text="\U0001f4cb Copy", width=80, height=28,
            font=ctk.CTkFont(size=12),
            fg_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray40"),
            command=lambda: self._copy(self.hist_output)
        ).grid(row=5, column=0, sticky="e", pady=(4, 0))

    # ------------------------------------------------------------------ #
    #  History helpers                                                     #
    # ------------------------------------------------------------------ #

    def _on_mode_change(self, value: str):
        if value == "Trend across last X surveys":
            self.trend_label.grid()
            self.trend_x.grid()
        else:
            self.trend_label.grid_remove()
            self.trend_x.grid_remove()

    def _get_store(self):
        if self._store:
            return self._store
        creds = self._get_creds()
        if not creds:
            return None
        from core.survey_store import SurveyStore
        self._store = SurveyStore(creds)
        return self._store

    def _get_creds(self):
        if self._creds:
            return self._creds
        survey_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "tools", "survey")
        )
        token_path = os.path.join(survey_dir, "token.json")
        if not os.path.exists(token_path):
            return None
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            creds = Credentials.from_authorized_user_file(token_path, _SCOPES)
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            self._creds = creds
            return creds
        except Exception:
            return None

    def _load_history(self):
        self.hist_status.configure(text="Loading...")
        for w in self.survey_list_frame.winfo_children():
            w.destroy()

        def run():
            store = self._get_store()
            if not store:
                self.after(0, lambda: self.hist_status.configure(
                    text="\u26a0\ufe0f Sign in with Gmail first.",
                    text_color="orange"))
                return
            surveys = store.all_surveys()
            self.after(0, lambda: self._populate_survey_list(surveys))
            self.after(0, lambda: self.hist_status.configure(
                text=f"{len(surveys)} survey(s) found.", text_color="gray"))

        threading.Thread(target=run, daemon=True).start()

    def _populate_survey_list(self, surveys: list):
        for w in self.survey_list_frame.winfo_children():
            w.destroy()
        if not surveys:
            ctk.CTkLabel(
                self.survey_list_frame,
                text="No surveys yet. Send your first one from the New Survey tab.",
                font=ctk.CTkFont(size=13), text_color="gray"
            ).pack(pady=16)
            return
        for survey in surveys:
            self._make_survey_row(survey)

    def _make_survey_row(self, survey: dict):
        row = ctk.CTkFrame(self.survey_list_frame, corner_radius=8)
        row.pack(fill="x", pady=4, padx=2)
        row.grid_columnconfigure(1, weight=1)

        sent = survey.get("sent_at", "")
        try:
            dt = datetime.fromisoformat(sent)
            sent_str = dt.strftime("%d %b %Y  %H:%M")
        except Exception:
            sent_str = sent[:16]

        ctk.CTkLabel(
            row, text=survey["title"],
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w"
        ).grid(row=0, column=1, sticky="w", padx=(8, 8), pady=(8, 2))

        resp_count = survey.get("response_count", 0)
        total = len(survey.get("recipients", []))
        meta_lbl = ctk.CTkLabel(
            row,
            text=f"{sent_str}  \u2022  {resp_count}/{total} responses",
            font=ctk.CTkFont(size=11), text_color="gray", anchor="w"
        )
        meta_lbl.grid(row=1, column=1, sticky="w", padx=(8, 8), pady=(0, 8))

        ctk.CTkButton(
            row, text="\U0001f4e5 Collect", width=90, height=28,
            font=ctk.CTkFont(size=12),
            fg_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray40"),
            command=lambda s=survey, lbl=meta_lbl: self._collect_for(s, lbl)
        ).grid(row=0, column=2, rowspan=2, padx=(0, 8), pady=8)

    def _collect_for(self, survey: dict, meta_lbl: ctk.CTkLabel | None = None) -> list:
        creds = self._get_creds()
        if not creds:
            return []
        try:
            from core.response_collector import ResponseCollector
            collector = ResponseCollector(creds)

            sheet_id = survey.get("sheet_id") or ""
            if not sheet_id:
                sheet_id = collector.get_linked_sheet_id(survey.get("form_id", ""))

            if not sheet_id:
                if meta_lbl:
                    self.after(0, lambda: self.hist_status.configure(
                        text=(
                            "\u274c No linked Sheet found. "
                            "Open the form in Google Forms and link a Sheet manually."
                        ),
                        text_color="red"))
                return []

            responses = collector.collect(sheet_id)
            count = len(responses)

            store = self._get_store()
            if store:
                store.update_response_count(survey["id"], count)
                if not survey.get("sheet_id") and sheet_id:
                    survey["sheet_id"] = sheet_id
                    for s in store._data["surveys"]:
                        if s["id"] == survey["id"]:
                            s["sheet_id"] = sheet_id
                            break
                    store._save()

            survey["response_count"] = count
            survey["_responses"] = responses

            if meta_lbl:
                sent_str = survey.get("sent_at", "")[:16]
                total = len(survey.get("recipients", []))
                self.after(0, lambda: meta_lbl.configure(
                    text=f"{sent_str}  \u2022  {count}/{total} responses"
                ))
                self.after(0, lambda: self.hist_status.configure(
                    text=f"\u2705 {count} response(s) collected.",
                    text_color="#2ecc71"))

            return responses

        except Exception as e:
            if meta_lbl:
                self.after(0, lambda: self.hist_status.configure(
                    text=f"\u274c {e}", text_color="red"))
            return []

    # ------------------------------------------------------------------ #
    #  Analysis                                                            #
    # ------------------------------------------------------------------ #

    def _analyse(self):
        token = self.settings.get("github_token", "")
        if not token:
            self.hist_status.configure(
                text="\u26a0\ufe0f Sign in to GitHub Copilot first.",
                text_color="orange")
            return

        mode = self.analysis_mode.get()

        if mode == "This survey only":
            store = self._get_store()
            if not store:
                self.hist_status.configure(
                    text="\u26a0\ufe0f Sign in with Gmail first.",
                    text_color="orange")
                return
            surveys = store.all_surveys()
            if not surveys:
                self.hist_status.configure(
                    text="\u26a0\ufe0f No surveys in history yet.",
                    text_color="orange")
                return
            target = surveys[0]
            self.analyse_btn.configure(state="disabled", text="Collecting...")
            self.hist_status.configure(
                text=f"\u23f3 Collecting responses for: {target['title']}...",
                text_color="gray")

            def run_single():
                responses = self._collect_for(target)
                if not responses:
                    self.after(0, lambda: self.hist_status.configure(
                        text="\u26a0\ufe0f No responses found yet.",
                        text_color="orange"))
                    self.after(0, lambda: self.analyse_btn.configure(
                        state="normal", text="\U0001f50d Analyse"))
                    return
                self.after(0, lambda: self.analyse_btn.configure(
                    state="disabled", text="Analysing..."))
                self._run_single_analysis(target, responses)

            threading.Thread(target=run_single, daemon=True).start()

        else:
            try:
                x = int(self.trend_x.get().strip())
                if x < 2:
                    raise ValueError
            except ValueError:
                self.hist_status.configure(
                    text="\u26a0\ufe0f Enter a number \u2265 2 for trend analysis.",
                    text_color="orange")
                return
            self._run_trend_analysis(x)

    def _run_single_analysis(self, survey: dict, responses: list):
        def run():
            try:
                from core.copilot_client import CopilotClient
                client = CopilotClient(
                    token=self.settings["github_token"],
                    model=self.settings.get("model", "gpt-4o")
                )
                result = client.complete(
                    system=self._analysis_system_prompt(),
                    user=self._format_single(survey, responses)
                )
                self.after(0, lambda: self._set_hist_output(result))
                self.after(0, lambda: self.hist_status.configure(
                    text="\u2705 Analysis complete.", text_color="#2ecc71"))
            except Exception as e:
                self.after(0, lambda: self.hist_status.configure(
                    text=f"\u274c {e}", text_color="red"))
            finally:
                self.after(0, lambda: self.analyse_btn.configure(
                    state="normal", text="\U0001f50d Analyse"))

        threading.Thread(target=run, daemon=True).start()

    def _run_trend_analysis(self, x: int):
        store = self._get_store()
        if not store:
            self.hist_status.configure(
                text="\u26a0\ufe0f Sign in with Gmail first.",
                text_color="orange")
            return

        self.analyse_btn.configure(state="disabled", text="Collecting...")
        self.hist_status.configure(
            text=f"\u23f3 Collecting responses for last {x} surveys...",
            text_color="gray")

        def run():
            try:
                surveys = store.last_n(x)
                for s in surveys:
                    if not s.get("_responses"):
                        self._collect_for(s)

                surveys_with_data = [s for s in surveys if s.get("_responses")]
                if not surveys_with_data:
                    self.after(0, lambda: self.hist_status.configure(
                        text="\u26a0\ufe0f No responses found in any of the selected surveys.",
                        text_color="orange"))
                    self.after(0, lambda: self.analyse_btn.configure(
                        state="normal", text="\U0001f50d Analyse"))
                    return

                self.after(0, lambda: self.analyse_btn.configure(
                    state="disabled", text="Analysing..."))

                from core.copilot_client import CopilotClient
                client = CopilotClient(
                    token=self.settings["github_token"],
                    model=self.settings.get("model", "gpt-4o")
                )
                result = client.complete(
                    system=self._trend_system_prompt(),
                    user=self._format_trend(surveys_with_data)
                )
                self.after(0, lambda: self._set_hist_output(result))
                self.after(0, lambda: self.hist_status.configure(
                    text="\u2705 Trend analysis complete.",
                    text_color="#2ecc71"))
            except Exception as e:
                self.after(0, lambda: self.hist_status.configure(
                    text=f"\u274c {e}", text_color="red"))
            finally:
                self.after(0, lambda: self.analyse_btn.configure(
                    state="normal", text="\U0001f50d Analyse"))

        threading.Thread(target=run, daemon=True).start()

    # ------------------------------------------------------------------ #
    #  Prompt helpers                                                      #
    # ------------------------------------------------------------------ #

    def _format_single(self, survey: dict, responses: list) -> str:
        lines = [
            f"Survey: {survey['title']}",
            f"Sent: {survey.get('sent_at', '')[:10]}",
            f"Responses: {len(responses)} / {len(survey.get('recipients', []))}",
            "",
        ]
        for i, r in enumerate(responses, 1):
            lines.append(f"Respondent {i} (submitted {r.get('submitted_at', '')[:16]}):")
            for q, a in r.get("answers", {}).items():
                lines.append(f"  Q: {q}")
                lines.append(f"  A: {a}")
            lines.append("")
        return "\n".join(lines)

    def _format_trend(self, surveys: list) -> str:
        lines = [f"Trend analysis across {len(surveys)} surveys:", ""]
        for survey in surveys:
            responses = survey.get("_responses", [])
            lines.append(
                f"--- {survey['title']} ({survey.get('sent_at', '')[:10]}) ---"
            )
            lines.append(
                f"Responses: {len(responses)} / {len(survey.get('recipients', []))}"
            )
            for r in responses:
                for q, a in r.get("answers", {}).items():
                    lines.append(f"  Q: {q}  |  A: {a}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _analysis_system_prompt() -> str:
        return (
            "You are analysing PM team survey responses. "
            "Produce a clear, structured summary covering: participation rate, "
            "key themes from scale questions (averages), dominant patterns in "
            "multiple choice, and notable open-text responses. "
            "Flag any strong signals \u2014 positive or negative. "
            "Be concise and actionable. Do not pad the output."
        )

    @staticmethod
    def _trend_system_prompt() -> str:
        return (
            "You are analysing a series of PM team surveys over time. "
            "For each question that appears across surveys, identify the direction "
            "of change (improving / stable / declining). "
            "Highlight any consistent concerns, improvements, or emerging patterns. "
            "Conclude with 2\u20133 actionable recommendations based on the trend. "
            "Be direct and evidence-based."
        )

    # ------------------------------------------------------------------ #
    #  Send survey                                                         #
    # ------------------------------------------------------------------ #

    def _send_survey(self):
        topic = self.entries[0].get().strip()
        deadline = self.entries[1].get().strip() or "end of this week"
        emails = self.entries[2].get().strip()

        if not topic:
            self.new_status.configure(
                text="\u26a0\ufe0f Please enter a survey topic.",
                text_color="orange")
            return
        if not emails:
            self.new_status.configure(
                text="\u26a0\ufe0f Please enter at least one email.",
                text_color="orange")
            return

        self.send_btn.configure(state="disabled", text="Sending...")
        self.new_status.configure(
            text="\u23f3 Generating questions and creating form...",
            text_color="gray")

        def run():
            try:
                questions = self._generate_questions(topic)
                self._write_questions(questions)
                email_list = [e.strip() for e in emails.split(",") if e.strip()]

                survey_dir = os.path.abspath(
                    os.path.join(os.path.dirname(__file__),
                                 "..", "..", "tools", "survey")
                )
                sys.path.insert(0, survey_dir)

                from survey import authenticate, create_form, link_response_sheet, \
                    send_emails, save_form_metadata
                from googleapiclient.discovery import build

                creds = authenticate()
                self._creds = creds
                forms_service = build("forms", "v1", credentials=creds)
                gmail_service = build("gmail", "v1", credentials=creds)
                drive_service = build("drive", "v3", credentials=creds)

                form_id, form_url = create_form(forms_service, topic, questions)

                self.after(0, lambda: self.new_status.configure(
                    text="\u23f3 Linking response sheet...", text_color="gray"))

                # Pass creds directly — not forms_service
                sheet_id = link_response_sheet(creds, drive_service, form_id, topic)

                send_emails(gmail_service, email_list, topic, form_url, deadline)
                save_form_metadata(form_id, form_url, topic, email_list, deadline)

                from core.survey_store import SurveyStore
                store = SurveyStore(creds)
                self._store = store
                store.add_survey(
                    title=topic,
                    form_id=form_id,
                    sheet_id=sheet_id,
                    recipients=email_list,
                    question_count=len(questions)
                )

                sheet_note = (
                    f"\n\U0001f4ca Responses sheet: "
                    f"https://docs.google.com/spreadsheets/d/{sheet_id}"
                    if sheet_id else
                    "\n\u26a0\ufe0f Sheet not linked \u2014 open the form in Google Forms to link manually."
                )
                self.after(0, lambda: self.new_status.configure(
                    text="\u2705 Survey sent and saved to Drive history!",
                    text_color="#2ecc71"))
                self.after(0, lambda: self._set_new_output(
                    "\u2705 Survey created and sent!\n\n"
                    f"Topic: {topic}\n"
                    f"Deadline: {deadline}\n"
                    f"Recipients: {', '.join(email_list)}\n\n"
                    "\U0001f517 Form URL:\n" + form_url +
                    sheet_note + "\n\n"
                    "Questions sent:\n" +
                    "\n".join(f"  {i+1}. {q['text']}"
                              for i, q in enumerate(questions))
                ))
                self.after(0, lambda: self.send_btn.configure(
                    state="normal", text="\U0001f4e4 Send Survey"))

            except Exception as e:
                self.after(0, lambda: self.new_status.configure(
                    text=f"\u274c Error: {e}", text_color="red"))
                self.after(0, lambda: self.send_btn.configure(
                    state="normal", text="\U0001f4e4 Send Survey"))

        threading.Thread(target=run, daemon=True).start()

    def _generate_questions(self, topic: str) -> list:
        token = self.settings.get("github_token", "")
        model = self.settings.get("model", "gpt-4o")
        if token:
            try:
                from core.copilot_client import CopilotClient
                client = CopilotClient(token=token, model=model)
                prompt = (
                    f"Generate exactly 5 survey questions for a PM team survey "
                    f"about: '{topic}'.\n"
                    "Rules:\n"
                    "- 2 scale questions (rating 1-5)\n"
                    "- 2 multiple choice questions (provide 3-4 options each)\n"
                    "- 1 open text question\n"
                    "Return ONLY valid JSON array, no markdown, no explanation.\n"
                    'Format: [{"text": "...", "type": "scale" | "multiple_choice" | "text", "options": ["..."]}]\n'
                    "options field only required for multiple_choice type."
                )
                response = client.complete(
                    system="You are a survey designer for project management teams.",
                    user=prompt
                )
                clean = (
                    response.strip()
                    .lstrip("```json").lstrip("```")
                    .rstrip("```").strip()
                )
                return json.loads(clean)
            except Exception:
                pass
        return [
            {"text": f"How satisfied are you with the team's progress on {topic}?",
             "type": "scale"},
            {"text": "How effective was communication within the team?",
             "type": "scale"},
            {"text": "What was the biggest blocker this sprint?",
             "type": "multiple_choice",
             "options": ["Technical debt", "Unclear requirements",
                         "External dependencies", "Team capacity"]},
            {"text": "How would you rate the sprint planning quality?",
             "type": "multiple_choice",
             "options": ["Excellent", "Good", "Needs improvement", "Poor"]},
            {"text": "What one change would most improve how we work together?",
             "type": "text"},
        ]

    def _write_questions(self, questions: list):
        survey_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         "..", "..", "tools", "survey")
        )
        path = os.path.join(survey_dir, "questions.json")
        with open(path, "w") as f:
            json.dump(questions, f, indent=2)

    def _set_new_output(self, text: str):
        self.new_output.configure(state="normal")
        self.new_output.delete("1.0", "end")
        self.new_output.insert("1.0", text)
        self.new_output.configure(state="disabled")

    def _set_hist_output(self, text: str):
        self.hist_output.configure(state="normal")
        self.hist_output.delete("1.0", "end")
        self.hist_output.insert("1.0", text)
        self.hist_output.configure(state="disabled")

    def _copy(self, box: ctk.CTkTextbox):
        text = box.get("1.0", "end").strip()
        self.clipboard_clear()
        self.clipboard_append(text)
