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
    "https://www.googleapis.com/auth/gmail.send",
]

QUESTION_TYPES = ["scale", "multiple_choice", "text"]


class SurveyPanel(ctk.CTkFrame):
    def __init__(self, parent, settings: dict):
        super().__init__(parent, fg_color="transparent")
        self.settings = settings
        self._creds = None
        self._store = None
        self._template_store = None

        # Question-editor state
        self._step = "compose"           # "compose" | "edit"
        self._pending_questions: list[dict] = []
        self._question_widgets: list[dict] = []  # per-row widget refs
        self._selected_template_id: str | None = None
        self._templates_cache: list[dict] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build()

    # ================================================================== #
    #  Build UI                                                           #
    # ================================================================== #

    def _build(self):
        self.tab_view = ctk.CTkTabview(self, height=600)
        self.tab_view.grid(row=0, column=0, sticky="nsew")
        self.tab_view.add("New Survey")
        self.tab_view.add("History")
        self._build_new_tab(self.tab_view.tab("New Survey"))
        self._build_history_tab(self.tab_view.tab("History"))

    # ------------------------------------------------------------------ #
    #  New Survey tab                                                      #
    # ------------------------------------------------------------------ #

    def _build_new_tab(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(6, weight=1)  # editor row expands

        ctk.CTkLabel(
            parent, text="\U0001f4cb Survey Agent",
            font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 16))

        # ---- compose form (Step 1) ------------------------------------ #
        self._compose_frame = ctk.CTkFrame(parent)
        self._compose_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self._compose_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("Survey Topic:",
             "e.g. Sprint 24 Retro, Team Health Check Q2"),
            ("Deadline:",
             "e.g. Friday EOD, June 20"),
            ("Recipients (comma-separated emails):",
             "alice@company.com, bob@company.com"),
        ]
        self.entries = {}
        for i, (label, placeholder) in enumerate(fields):
            ctk.CTkLabel(
                self._compose_frame, text=label,
                font=ctk.CTkFont(size=13)
            ).grid(row=i, column=0, sticky="w", padx=(12, 8), pady=8)
            entry = ctk.CTkEntry(
                self._compose_frame, placeholder_text=placeholder,
                height=36, font=ctk.CTkFont(size=13)
            )
            entry.grid(row=i, column=1, sticky="ew", padx=(0, 12), pady=8)
            self.entries[i] = entry

        # ---- template selector --------------------------------------- #
        tpl_row = ctk.CTkFrame(parent, fg_color="transparent")
        tpl_row.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        tpl_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            tpl_row, text="Template:",
            font=ctk.CTkFont(size=13)
        ).grid(row=0, column=0, sticky="w", padx=(0, 8))

        self._tpl_var = ctk.StringVar(value="-- None (AI will generate) --")
        self._tpl_menu = ctk.CTkOptionMenu(
            tpl_row,
            values=["-- None (AI will generate) --"],
            variable=self._tpl_var,
            width=300, height=32,
            font=ctk.CTkFont(size=13),
            button_color=("gray75", "gray35"),
            button_hover_color=("gray65", "gray45"),
            fg_color=("gray85", "gray25"),
            text_color=("gray10", "gray90"),
            command=self._on_template_selected,
        )
        self._tpl_menu.grid(row=0, column=1, sticky="w")

        ctk.CTkButton(
            tpl_row, text="\U0001f504", width=32, height=32,
            font=ctk.CTkFont(size=13),
            fg_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray40"),
            command=self._refresh_templates,
        ).grid(row=0, column=2, padx=(6, 0))

        # ---- Step-1 action buttons ----------------------------------- #
        btn_row1 = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row1.grid(row=3, column=0, sticky="w", pady=(0, 12))

        self.preview_btn = ctk.CTkButton(
            btn_row1, text="\U0001f50d Preview Questions",
            width=180, height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._preview_questions,
        )
        self.preview_btn.grid(row=0, column=0, padx=(0, 8))

        ctk.CTkButton(
            btn_row1, text="\u270f\ufe0f Start Blank",
            width=140, height=40,
            font=ctk.CTkFont(size=13),
            fg_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray40"),
            command=self._start_blank_editor,
        ).grid(row=0, column=1)

        self.new_status = ctk.CTkLabel(
            parent, text="",
            font=ctk.CTkFont(size=13), text_color="gray"
        )
        self.new_status.grid(row=4, column=0, sticky="w", pady=(0, 4))

        # ---- Question editor (Step 2, hidden initially) -------------- #
        self._editor_outer = ctk.CTkFrame(parent, fg_color="transparent")
        self._editor_outer.grid(row=5, column=0, sticky="nsew", pady=(0, 8))
        self._editor_outer.grid_columnconfigure(0, weight=1)
        self._editor_outer.grid_rowconfigure(1, weight=1)
        self._editor_outer.grid_remove()  # hidden until Step 2

        # Editor header
        ed_hdr = ctk.CTkFrame(self._editor_outer, fg_color="transparent")
        ed_hdr.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ed_hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            ed_hdr, text="\U0001f4dd Survey Questions",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            ed_hdr, text="+ Add Question",
            width=130, height=28,
            font=ctk.CTkFont(size=12),
            fg_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray40"),
            command=self._add_blank_question,
        ).grid(row=0, column=1, padx=(8, 0))

        # Scrollable question list
        self._editor_scroll = ctk.CTkScrollableFrame(
            self._editor_outer, label_text="", height=280
        )
        self._editor_scroll.grid(row=1, column=0, sticky="nsew")
        self._editor_scroll.grid_columnconfigure(0, weight=1)

        # Editor footer buttons
        ed_ftr = ctk.CTkFrame(self._editor_outer, fg_color="transparent")
        ed_ftr.grid(row=2, column=0, sticky="ew", pady=(8, 0))

        ctk.CTkButton(
            ed_ftr, text="\u2190 Back",
            width=80, height=36,
            font=ctk.CTkFont(size=13),
            fg_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray40"),
            command=self._back_to_compose,
        ).grid(row=0, column=0, padx=(0, 8))

        ctk.CTkButton(
            ed_ftr, text="\U0001f504 Regenerate AI",
            width=150, height=36,
            font=ctk.CTkFont(size=13),
            fg_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray40"),
            command=self._regenerate_questions,
        ).grid(row=0, column=1, padx=(0, 8))

        ctk.CTkButton(
            ed_ftr, text="\U0001f4be Save as Template",
            width=170, height=36,
            font=ctk.CTkFont(size=13),
            fg_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray40"),
            command=self._save_as_template,
        ).grid(row=0, column=2, padx=(0, 8))

        self.send_btn = ctk.CTkButton(
            ed_ftr, text="\U0001f4e4 Send Survey",
            width=150, height=36,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._send_survey,
        )
        self.send_btn.grid(row=0, column=3)

        # ---- Output (Step 2 completion) ------------------------------ #
        ctk.CTkLabel(
            parent, text="Output",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=6, column=0, sticky="w", pady=(8, 4))

        self.new_output = ctk.CTkTextbox(
            parent, font=ctk.CTkFont(size=13), wrap="word"
        )
        self.new_output.grid(row=7, column=0, sticky="nsew")
        self.new_output.configure(state="disabled")
        parent.grid_rowconfigure(7, weight=1)

        ctk.CTkButton(
            parent, text="\U0001f4cb Copy", width=80, height=28,
            font=ctk.CTkFont(size=12),
            fg_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray40"),
            command=lambda: self._copy(self.new_output)
        ).grid(row=8, column=0, sticky="e", pady=(4, 0))

    # ------------------------------------------------------------------ #
    #  History tab (unchanged)                                            #
    # ------------------------------------------------------------------ #

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

        self.hist_status = ctk.CTkLabel(
            top, text="",
            font=ctk.CTkFont(size=12), text_color="gray"
        )
        self.hist_status.grid(row=0, column=1, sticky="w")

        self.survey_list_frame = ctk.CTkScrollableFrame(parent, label_text="")
        self.survey_list_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        self.survey_list_frame.grid_columnconfigure(0, weight=1)

        analysis_frame = ctk.CTkFrame(parent)
        analysis_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        analysis_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            analysis_frame, text="Analysis:",
            font=ctk.CTkFont(size=13)
        ).grid(row=0, column=0, padx=(12, 8), pady=10, sticky="w")

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

        self.trend_label = ctk.CTkLabel(
            analysis_frame, text="Last X surveys:",
            font=ctk.CTkFont(size=13)
        )
        self.trend_label.grid(row=0, column=2, padx=(16, 4), pady=10)
        self.trend_label.grid_remove()

        self.trend_x = ctk.CTkEntry(
            analysis_frame, width=60, height=32,
            font=ctk.CTkFont(size=13)
        )
        self.trend_x.insert(0, "3")
        self.trend_x.grid(row=0, column=3, padx=(0, 12), pady=10)
        self.trend_x.grid_remove()

        self.analyse_btn = ctk.CTkButton(
            analysis_frame, text="\U0001f50d Analyse",
            width=120, height=32,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._analyse
        )
        self.analyse_btn.grid(row=0, column=4, padx=(0, 12), pady=10)

        ctk.CTkLabel(
            parent, text="Analysis Output",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=3, column=0, sticky="w", pady=(4, 4))

        self.hist_output = ctk.CTkTextbox(
            parent, height=200,
            font=ctk.CTkFont(size=13), wrap="word"
        )
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

    # ================================================================== #
    #  Question editor logic                                              #
    # ================================================================== #

    def _show_editor(self, questions: list):
        """Switch from compose step to question-editor step."""
        self._pending_questions = [dict(q) for q in questions]
        self._step = "edit"
        self._compose_frame.grid_remove()
        self._editor_outer.grid()
        self._refresh_editor()

    def _back_to_compose(self):
        """Return to Step 1 without sending."""
        self._step = "compose"
        self._editor_outer.grid_remove()
        self._compose_frame.grid()
        self.new_status.configure(text="", text_color="gray")

    def _refresh_editor(self):
        """Re-render all question rows from self._pending_questions."""
        for w in self._editor_scroll.winfo_children():
            w.destroy()
        self._question_widgets = []
        for idx, q in enumerate(self._pending_questions):
            self._make_question_row(idx, q)

    def _make_question_row(self, idx: int, question: dict):
        """
        Render one question row with:
          - type dropdown  (fully editable)
          - question text  (fully editable CTkEntry)
          - options list   (for multiple_choice, each option is an editable CTkEntry)
          - reorder arrows + delete button
        """
        row_frame = ctk.CTkFrame(
            self._editor_scroll, corner_radius=8,
            border_width=1, border_color=("gray75", "gray35")
        )
        row_frame.pack(fill="x", pady=4, padx=2)
        row_frame.grid_columnconfigure(1, weight=1)

        # -- type badge ------------------------------------------------ #
        type_var = ctk.StringVar(value=question.get("type", "scale"))
        type_menu = ctk.CTkOptionMenu(
            row_frame,
            values=QUESTION_TYPES,
            variable=type_var,
            width=140, height=30,
            font=ctk.CTkFont(size=12),
            button_color=("gray75", "gray35"),
            button_hover_color=("gray65", "gray45"),
            fg_color=("gray85", "gray25"),
            text_color=("gray10", "gray90"),
            command=lambda val, i=idx: self._on_type_change(i, val),
        )
        type_menu.grid(row=0, column=0, padx=(8, 6), pady=(8, 4), sticky="w")

        # -- question text --------------------------------------------- #
        text_var = ctk.StringVar(value=question.get("text", ""))
        text_entry = ctk.CTkEntry(
            row_frame,
            textvariable=text_var,
            height=32,
            font=ctk.CTkFont(size=13),
            placeholder_text="Question text...",
        )
        text_entry.grid(row=0, column=1, padx=(0, 6), pady=(8, 4), sticky="ew")

        # -- reorder + delete ------------------------------------------ #
        ctrl = ctk.CTkFrame(row_frame, fg_color="transparent")
        ctrl.grid(row=0, column=2, padx=(0, 8), pady=(8, 4))

        ctk.CTkButton(
            ctrl, text="\u2191", width=26, height=26,
            font=ctk.CTkFont(size=11),
            fg_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray40"),
            command=lambda i=idx: self._move_question(i, -1),
        ).grid(row=0, column=0, padx=(0, 2))

        ctk.CTkButton(
            ctrl, text="\u2193", width=26, height=26,
            font=ctk.CTkFont(size=11),
            fg_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray40"),
            command=lambda i=idx: self._move_question(i, 1),
        ).grid(row=0, column=1, padx=(0, 2))

        ctk.CTkButton(
            ctrl, text="\u2715", width=26, height=26,
            font=ctk.CTkFont(size=11),
            fg_color=("gray80", "gray30"),
            text_color=("#cc4444", "#ff6666"),
            hover_color=("gray70", "gray40"),
            command=lambda i=idx: self._delete_question(i),
        ).grid(row=0, column=2)

        # -- options sub-section (multiple_choice only) ---------------- #
        options_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        options_frame.grid(
            row=1, column=0, columnspan=3,
            padx=8, pady=(0, 8), sticky="ew"
        )
        options_frame.grid_columnconfigure(0, weight=1)

        widget_ref = {
            "type_var": type_var,
            "text_var": text_var,
            "options_frame": options_frame,
            "option_vars": [],
        }
        self._question_widgets.append(widget_ref)

        if question.get("type") == "multiple_choice":
            self._render_options(options_frame, widget_ref,
                                 question.get("options", []))
        else:
            options_frame.grid_remove()

    def _render_options(self, frame: ctk.CTkFrame,
                        widget_ref: dict, options: list):
        """Render editable option entries inside the options sub-frame."""
        for w in frame.winfo_children():
            w.destroy()
        widget_ref["option_vars"] = []

        for i, opt in enumerate(options):
            opt_row = ctk.CTkFrame(frame, fg_color="transparent")
            opt_row.pack(fill="x", pady=2)
            opt_row.grid_columnconfigure(0, weight=1)

            var = ctk.StringVar(value=opt)
            ctk.CTkEntry(
                opt_row, textvariable=var,
                height=28, font=ctk.CTkFont(size=12),
                placeholder_text=f"Option {i + 1}",
            ).grid(row=0, column=0, sticky="ew", padx=(16, 4))

            ctk.CTkButton(
                opt_row, text="\u2715", width=24, height=24,
                font=ctk.CTkFont(size=11),
                fg_color="transparent",
                text_color=("#cc4444", "#ff6666"),
                hover_color=("gray80", "gray30"),
                command=lambda v=var: self._remove_option(frame, widget_ref, v),
            ).grid(row=0, column=1)

            widget_ref["option_vars"].append(var)

        ctk.CTkButton(
            frame, text="+ Add option",
            height=24, font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=("gray40", "gray70"),
            hover_color=("gray85", "gray25"),
            anchor="w",
            command=lambda: self._add_option(frame, widget_ref),
        ).pack(anchor="w", padx=16, pady=(2, 0))

    def _remove_option(self, frame: ctk.CTkFrame,
                       widget_ref: dict, var: ctk.StringVar):
        widget_ref["option_vars"] = [
            v for v in widget_ref["option_vars"] if v is not var
        ]
        current = [v.get() for v in widget_ref["option_vars"]]
        self._render_options(frame, widget_ref, current)

    def _add_option(self, frame: ctk.CTkFrame, widget_ref: dict):
        current = [v.get() for v in widget_ref["option_vars"]]
        current.append("")
        self._render_options(frame, widget_ref, current)

    def _on_type_change(self, idx: int, new_type: str):
        """Show/hide the options sub-frame when type changes."""
        if idx >= len(self._question_widgets):
            return
        wr = self._question_widgets[idx]
        frame = wr["options_frame"]
        if new_type == "multiple_choice":
            frame.grid()
            if not wr["option_vars"]:
                self._render_options(frame, wr, ["", ""])
        else:
            frame.grid_remove()

    def _move_question(self, idx: int, direction: int):
        """Swap question at idx with neighbour; re-render."""
        # Flush current text edits into _pending_questions first
        self._flush_editor_to_pending()
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self._pending_questions):
            return
        q = self._pending_questions
        q[idx], q[new_idx] = q[new_idx], q[idx]
        self._refresh_editor()

    def _delete_question(self, idx: int):
        self._flush_editor_to_pending()
        if 0 <= idx < len(self._pending_questions):
            self._pending_questions.pop(idx)
        self._refresh_editor()

    def _add_blank_question(self):
        self._flush_editor_to_pending()
        self._pending_questions.append(
            {"text": "", "type": "scale", "options": []}
        )
        self._refresh_editor()

    def _flush_editor_to_pending(self):
        """
        Read current widget values back into self._pending_questions
        so that reorder/delete/move operations don't lose live edits.
        """
        for i, wr in enumerate(self._question_widgets):
            if i >= len(self._pending_questions):
                break
            self._pending_questions[i]["text"] = wr["text_var"].get()
            self._pending_questions[i]["type"] = wr["type_var"].get()
            if wr["type_var"].get() == "multiple_choice":
                self._pending_questions[i]["options"] = [
                    v.get() for v in wr["option_vars"] if v.get().strip()
                ]

    def _collect_editor_state(self) -> list:
        """
        Return a clean list[dict] from the editor — the authoritative
        questions to be written to questions.json and sent.
        """
        self._flush_editor_to_pending()
        result = []
        for q in self._pending_questions:
            entry = {"text": q["text"].strip(), "type": q["type"]}
            if q["type"] == "multiple_choice":
                entry["options"] = [
                    o for o in q.get("options", []) if o.strip()
                ]
            result.append(entry)
        return [q for q in result if q["text"]]  # drop empty rows

    # ================================================================== #
    #  Step-1 actions                                                     #
    # ================================================================== #

    def _preview_questions(self):
        topic = self.entries[0].get().strip()
        if not topic:
            self.new_status.configure(
                text="\u26a0\ufe0f Please enter a survey topic.",
                text_color="orange")
            return
        if not self.entries[2].get().strip():
            self.new_status.configure(
                text="\u26a0\ufe0f Please enter at least one email.",
                text_color="orange")
            return

        # If a template is selected, skip AI and load template directly
        tpl = self._get_selected_template()
        if tpl:
            self.new_status.configure(
                text=f"\U0001f4cb Loaded template: {tpl['name']}",
                text_color="gray")
            self._show_editor(tpl["questions"])
            return

        self.preview_btn.configure(state="disabled", text="Generating...")
        self.new_status.configure(
            text="\u23f3 Generating questions...", text_color="gray")

        def run():
            questions = self._generate_questions(topic)
            self.after(0, lambda: self.preview_btn.configure(
                state="normal", text="\U0001f50d Preview Questions"))
            self.after(0, lambda: self._show_editor(questions))

        threading.Thread(target=run, daemon=True).start()

    def _start_blank_editor(self):
        """Open the editor with a single blank question row (no AI call)."""
        topic = self.entries[0].get().strip()
        if not topic:
            self.new_status.configure(
                text="\u26a0\ufe0f Please enter a survey topic first.",
                text_color="orange")
            return
        if not self.entries[2].get().strip():
            self.new_status.configure(
                text="\u26a0\ufe0f Please enter at least one email.",
                text_color="orange")
            return
        self.new_status.configure(text="", text_color="gray")
        self._show_editor([{"text": "", "type": "scale", "options": []}])

    def _regenerate_questions(self):
        topic = self.entries[0].get().strip()
        if not topic:
            return
        self.new_status.configure(
            text="\u23f3 Regenerating questions...", text_color="gray")

        def run():
            questions = self._generate_questions(topic)
            self.after(0, lambda: self._show_editor(questions))
            self.after(0, lambda: self.new_status.configure(
                text="\U0001f504 Questions regenerated.", text_color="gray"))

        threading.Thread(target=run, daemon=True).start()

    # ================================================================== #
    #  Template helpers                                                   #
    # ================================================================== #

    def _get_template_store(self):
        if self._template_store:
            return self._template_store
        creds = self._get_creds()
        if not creds:
            return None
        from core.template_store import TemplateStore
        self._template_store = TemplateStore(creds)
        return self._template_store

    def _refresh_templates(self):
        """Reload template list from Drive and update the dropdown."""
        def run():
            store = self._get_template_store()
            if not store:
                self.after(0, lambda: self.new_status.configure(
                    text="\u26a0\ufe0f Sign in with Gmail to load templates.",
                    text_color="orange"))
                return
            self._templates_cache = store.all_templates()
            names = ["-- None (AI will generate) --"] + [
                t["name"] for t in self._templates_cache
            ]
            self.after(0, lambda: self._tpl_menu.configure(values=names))
            self.after(0, lambda: self.new_status.configure(
                text=f"\U0001f4cb {len(self._templates_cache)} template(s) loaded.",
                text_color="gray"))

        threading.Thread(target=run, daemon=True).start()

    def _on_template_selected(self, value: str):
        if value == "-- None (AI will generate) --":
            self._selected_template_id = None
        else:
            for t in self._templates_cache:
                if t["name"] == value:
                    self._selected_template_id = t["id"]
                    break

    def _get_selected_template(self) -> dict | None:
        if not self._selected_template_id:
            return None
        for t in self._templates_cache:
            if t["id"] == self._selected_template_id:
                return t
        return None

    def _save_as_template(self):
        """Collect current editor state and save as a named template."""
        questions = self._collect_editor_state()
        if not questions:
            self.new_status.configure(
                text="\u26a0\ufe0f Add at least one question before saving.",
                text_color="orange")
            return

        dialog = ctk.CTkInputDialog(
            text="Template name:",
            title="Save as Template"
        )
        name = dialog.get_input()
        if not name or not name.strip():
            return
        name = name.strip()

        def run():
            store = self._get_template_store()
            if not store:
                self.after(0, lambda: self.new_status.configure(
                    text="\u26a0\ufe0f Sign in with Gmail to save templates.",
                    text_color="orange"))
                return
            store.add_template(name, questions)
            # Refresh dropdown
            self._templates_cache = store.all_templates()
            names = ["-- None (AI will generate) --"] + [
                t["name"] for t in self._templates_cache
            ]
            self.after(0, lambda: self._tpl_menu.configure(values=names))
            self.after(0, lambda: self.new_status.configure(
                text=f"\u2705 Template '{name}' saved!",
                text_color="#2ecc71"))

        threading.Thread(target=run, daemon=True).start()

    # ================================================================== #
    #  History helpers (unchanged)                                        #
    # ================================================================== #

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

    def _collect_for(self, survey: dict,
                     meta_lbl: ctk.CTkLabel | None = None) -> list:
        creds = self._get_creds()
        if not creds:
            return []
        try:
            from core.response_collector import ResponseCollector
            collector = ResponseCollector(creds)
            form_id = survey.get("form_id", "")
            if not form_id:
                raise ValueError("No form ID found for this survey.")
            responses = collector.collect(form_id)
            count = len(responses)
            store = self._get_store()
            if store:
                store.update_response_count(survey["id"], count)
            survey["response_count"] = count
            survey["_responses"] = responses
            if meta_lbl:
                sent = survey.get("sent_at", "")
                try:
                    dt = datetime.fromisoformat(sent)
                    sent_str = dt.strftime("%d %b %Y  %H:%M")
                except Exception:
                    sent_str = sent[:16]
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

    # ================================================================== #
    #  Analysis (unchanged)                                               #
    # ================================================================== #

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
                surveys_with_data = [
                    s for s in surveys if s.get("_responses")
                ]
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

    # ================================================================== #
    #  Prompt helpers (unchanged)                                         #
    # ================================================================== #

    def _format_single(self, survey: dict, responses: list) -> str:
        lines = [
            f"Survey: {survey['title']}",
            f"Sent: {survey.get('sent_at', '')[:10]}",
            f"Responses: {len(responses)} / {len(survey.get('recipients', []))}",
            "",
        ]
        for i, r in enumerate(responses, 1):
            lines.append(
                f"Respondent {i} ({r.get('respondent_email', 'anonymous')}, "
                f"submitted {r.get('submitted_at', '')[:16]}):"
            )
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

    # ================================================================== #
    #  Send survey                                                        #
    # ================================================================== #

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

        questions = self._collect_editor_state()
        if not questions:
            self.new_status.configure(
                text="\u26a0\ufe0f Add at least one question before sending.",
                text_color="orange")
            return

        self.send_btn.configure(state="disabled", text="Sending...")
        self.new_status.configure(
            text="\u23f3 Creating form and sending emails...",
            text_color="gray")

        template_id = self._selected_template_id

        def run():
            try:
                self._write_questions(questions)
                email_list = [e.strip() for e in emails.split(",") if e.strip()]

                survey_dir = os.path.abspath(
                    os.path.join(os.path.dirname(__file__),
                                 "..", "..", "tools", "survey")
                )
                sys.path.insert(0, survey_dir)

                from survey import (
                    authenticate, create_form, send_emails, save_form_metadata
                )
                from googleapiclient.discovery import build

                creds = authenticate()
                self._creds = creds
                forms_service = build("forms", "v1", credentials=creds)
                gmail_service = build("gmail", "v1", credentials=creds)

                form_id, form_url = create_form(forms_service, topic, questions)
                send_emails(gmail_service, email_list, topic, form_url, deadline)
                save_form_metadata(form_id, form_url, topic, email_list, deadline)

                from core.survey_store import SurveyStore
                store = SurveyStore(creds)
                self._store = store
                store.add_survey(
                    title=topic,
                    form_id=form_id,
                    sheet_id="",
                    recipients=email_list,
                    question_count=len(questions),
                )

                # Record template usage if one was selected
                if template_id:
                    tpl_store = self._get_template_store()
                    if tpl_store:
                        tpl_store.record_use(template_id)

                self.after(0, lambda: self.new_status.configure(
                    text="\u2705 Survey sent and saved to history!",
                    text_color="#2ecc71"))
                self.after(0, lambda: self._set_new_output(
                    "\u2705 Survey created and sent!\n\n"
                    f"Topic: {topic}\n"
                    f"Deadline: {deadline}\n"
                    f"Recipients: {', '.join(email_list)}\n\n"
                    "\U0001f517 Form URL:\n" + form_url + "\n\n"
                    "\U0001f4ca Collect responses any time from the History tab.\n\n"
                    "Questions sent:\n" +
                    "\n".join(
                        f"  {i + 1}. [{q['type']}] {q['text']}"
                        for i, q in enumerate(questions)
                    )
                ))
                # Return to compose step after success
                self.after(0, self._back_to_compose)
                self.after(0, lambda: self.send_btn.configure(
                    state="normal", text="\U0001f4e4 Send Survey"))

            except Exception as e:
                self.after(0, lambda: self.new_status.configure(
                    text=f"\u274c Error: {e}", text_color="red"))
                self.after(0, lambda: self.send_btn.configure(
                    state="normal", text="\U0001f4e4 Send Survey"))

        threading.Thread(target=run, daemon=True).start()

    # ================================================================== #
    #  Question generation (unchanged)                                    #
    # ================================================================== #

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

    # ================================================================== #
    #  Output helpers                                                     #
    # ================================================================== #

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
