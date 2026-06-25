import threading
import json
from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk

BASE_DIR = Path(__file__).parent.parent
TEMPLATE_PATH = BASE_DIR / "templates" / "base_profile_template.pptx"
SPEC_PATH = BASE_DIR / "templates" / "template_spec.json"


class ProfilePanel(ctk.CTkFrame):
    def __init__(self, master, settings: dict):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.settings = settings
        self._source_path: Path | None = None
        self._converted_path: Path | None = None
        self._processing = False

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_file_section()
        self._build_log_section()
        self._build_action_section()

    def _build_file_section(self):
        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="Source File:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=(12, 8), pady=12
        )
        self.file_label = ctk.CTkLabel(
            frame, text="No file selected", anchor="w",
            text_color=("gray50", "gray60")
        )
        self.file_label.grid(row=0, column=1, sticky="ew", padx=8)
        ctk.CTkButton(
            frame, text="Browse…", width=100,
            command=self._browse_file
        ).grid(row=0, column=2, padx=(8, 12), pady=12)

        ctk.CTkLabel(
            frame,
            text="Accepted formats: DOCX, PDF, PPTX, TXT",
            text_color=("gray55", "gray55"),
            font=ctk.CTkFont(size=11)
        ).grid(row=1, column=0, columnspan=3, padx=12, pady=(0, 8))

    def _build_log_section(self):
        ctk.CTkLabel(
            self, text="Processing Log",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(8, 2))

        self.log_box = ctk.CTkTextbox(self, state="disabled", wrap="word", font=ctk.CTkFont(size=12))
        self.log_box.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 8))

    def _build_action_section(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 16))
        frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.btn_preview = ctk.CTkButton(
            frame, text="Extract & Preview",
            command=self._run_extract_preview
        )
        self.btn_preview.grid(row=0, column=0, padx=8, pady=8, sticky="ew")

        self.btn_convert = ctk.CTkButton(
            frame, text="Convert to PPTX",
            command=self._run_convert
        )
        self.btn_convert.grid(row=0, column=1, padx=8, pady=8, sticky="ew")

        self.btn_save = ctk.CTkButton(
            frame, text="Save PPTX",
            state="disabled",
            command=self._save_pptx
        )
        self.btn_save.grid(row=0, column=2, padx=8, pady=8, sticky="ew")

        self.progress = ctk.CTkProgressBar(frame, mode="indeterminate")
        self.progress.grid(row=1, column=0, columnspan=3, padx=8, pady=(0, 4), sticky="ew")
        self.progress.grid_remove()

    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Select Profile Document",
            filetypes=[
                ("Supported files", "*.docx *.pdf *.pptx *.txt"),
                ("Word Document", "*.docx"),
                ("PDF", "*.pdf"),
                ("PowerPoint", "*.pptx"),
                ("Text file", "*.txt"),
                ("All files", "*.*"),
            ]
        )
        if path:
            self._source_path = Path(path)
            self.file_label.configure(text=self._source_path.name)
            self._log(f"Selected: {self._source_path}")

    def _log(self, message: str):
        self.after(0, lambda m=message: self._append_log(m))

    def _append_log(self, message: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _set_processing(self, state: bool):
        self._processing = state
        self.after(0, lambda: self._update_buttons(state))

    def _update_buttons(self, processing: bool):
        s = "disabled" if processing else "normal"
        self.btn_preview.configure(state=s)
        self.btn_convert.configure(state=s)
        if processing:
            self.progress.grid()
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.grid_remove()

    def _get_client(self):
        from core.copilot_client import CopilotClient
        return CopilotClient(
            token=self.settings["github_token"],
            model=self.settings.get("model", "gpt-4o")
        )

    def _run_extract_preview(self):
        if not self._source_path:
            self._log("ERROR: No file selected.")
            return
        if self._processing:
            return
        threading.Thread(target=self._extract_preview_worker, daemon=True).start()

    def _extract_preview_worker(self):
        self._set_processing(True)
        try:
            from core.profile_extractor import ProfileExtractor
            self._log("Extracting text from file…")
            client = self._get_client()
            extractor = ProfileExtractor(client)
            self._log("Calling AI extraction…")
            schema = extractor.extract_from_file(self._source_path)
            self._log("Extraction complete.")
            data = schema.model_dump()
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            self.after(0, lambda: self._show_preview(json_str))
        except Exception as e:
            import traceback
            self._log(f"ERROR during extraction:\n{traceback.format_exc()}")
        finally:
            self._set_processing(False)

    def _show_preview(self, json_str: str):
        win = ctk.CTkToplevel(self)
        win.title("Extracted Profile JSON")
        win.geometry("800x600")
        win.grab_set()
        tb = ctk.CTkTextbox(win, wrap="word", font=ctk.CTkFont(family="Courier", size=11))
        tb.pack(fill="both", expand=True, padx=12, pady=12)
        tb.insert("1.0", json_str)
        tb.configure(state="disabled")
        ctk.CTkButton(win, text="Close", command=win.destroy).pack(pady=(0, 12))

    def _run_convert(self):
        if not self._source_path:
            self._log("ERROR: No file selected.")
            return
        if self._processing:
            return
        if not TEMPLATE_PATH.exists():
            self._log(f"ERROR: Template not found at {TEMPLATE_PATH}")
            self._log("Please add base_profile_template.pptx to pm-toolkit/templates/ (Phase 1).")
            return
        threading.Thread(target=self._convert_worker, daemon=True).start()

    def _convert_worker(self):
        self._set_processing(True)
        self._converted_path = None
        self.after(0, lambda: self.btn_save.configure(state="disabled"))
        try:
            from core.profile_extractor import ProfileExtractor
            from core.profile_trimmer import ProfileTrimmer
            from core.profile_renderer import ProfileRenderer
            import tempfile

            self._log("Step 1/4: Extracting text…")
            client = self._get_client()
            extractor = ProfileExtractor(client)
            schema = extractor.extract_from_file(self._source_path)
            self._log("  ✓ Extraction complete.")

            self._log("Step 2/4: Validating schema…")
            self._log(f"  Name: {schema.name}")
            self._log(f"  Role: {schema.role_title}")
            self._log(f"  Competencies: {len(schema.competencies)}")
            self._log(f"  Experience entries: {len(schema.experience)}")

            self._log("Step 3/4: Trimming to template constraints…")
            trimmer = ProfileTrimmer()
            trimmed = trimmer.trim(schema)
            self._log("  ✓ Trimming complete.")

            self._log("Step 4/4: Rendering PPTX…")
            renderer = ProfileRenderer(TEMPLATE_PATH, SPEC_PATH)
            tmp = tempfile.NamedTemporaryFile(
                suffix=".pptx", delete=False,
                prefix=f"profile_{trimmed.name.replace(' ', '_')}_"
            )
            out_path = Path(tmp.name)
            tmp.close()
            renderer.render(trimmed, out_path)
            self._converted_path = out_path
            self._log(f"  ✓ PPTX rendered to temp: {out_path.name}")
            self._log("\n✅ Conversion complete. Click 'Save PPTX' to export.")
            self.after(0, lambda: self.btn_save.configure(state="normal"))

        except Exception as e:
            import traceback
            self._log(f"ERROR during conversion:\n{traceback.format_exc()}")
        finally:
            self._set_processing(False)

    def _save_pptx(self):
        if not self._converted_path or not self._converted_path.exists():
            self._log("ERROR: No converted file available.")
            return
        dest = filedialog.asksaveasfilename(
            title="Save Profile PPTX",
            defaultextension=".pptx",
            filetypes=[("PowerPoint", "*.pptx"), ("All files", "*.*")]
        )
        if dest:
            import shutil
            shutil.copy2(str(self._converted_path), dest)
            self._log(f"Saved to: {dest}")
