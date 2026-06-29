import threading
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from pdf_summarizer.core.exceptions import ConfigError
from pdf_summarizer.core.model_catalog import (
    ModelEntry,
    catalog_from_config,
    catalog_to_config,
    ensure_entry_in_catalog,
)
from pdf_summarizer.core.models import (
    DEFAULT_MAX_CHARS_OLLAMA,
    DEFAULT_MAX_CHARS_OPENROUTER,
    DEFAULT_OLLAMA_MODEL,
    JobConfig,
    ProgressEvent,
)
from pdf_summarizer.core.summary.schema import DEFAULT_USER_PROMPT
from pdf_summarizer.infra.config_store import ConfigStore
from pdf_summarizer.infra.filesystem import FileSystem
from pdf_summarizer.infra.providers.base import create_provider
from pdf_summarizer.services.extract_service import ExtractService
from pdf_summarizer.services.llm_service import LlmService
from pdf_summarizer.services.table_service import TableService
from pdf_summarizer.ui.widgets.folder_picker import FolderPicker
from pdf_summarizer.ui.widgets.generated_files_panel import GeneratedFilesPanel
from pdf_summarizer.ui.widgets.log_panel import LogPanel
from pdf_summarizer.ui.widgets.model_picker import ModelPicker


class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PDF Summarizer")
        self.geometry("760x820")
        self.minsize(680, 700)

        self._config_store = ConfigStore()
        self._running = False

        self._build_ui()
        self._load_config()
        self._refresh_files_panel()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        input_row = ctk.CTkFrame(container, fg_color="transparent")
        input_row.pack(fill="x")
        self._input_picker = FolderPicker(
            input_row,
            "Pasta de PDFs:",
            on_change=self._on_input_dir_change,
        )
        self._input_picker.pack(side="left", fill="x", expand=True)
        self._extract_button = ctk.CTkButton(
            input_row,
            text="Extrair dados do PDF",
            command=self._on_extract,
            width=180,
        )
        self._extract_button.pack(side="left", padx=(8, 0))

        output_row = ctk.CTkFrame(container, fg_color="transparent")
        output_row.pack(fill="x", pady=(4, 0))
        self._output_picker = FolderPicker(
            output_row,
            "Pasta de saída:",
            on_change=self._on_output_dir_change,
        )
        self._output_picker.pack(side="left", fill="x", expand=True)
        self._table_button = ctk.CTkButton(
            output_row,
            text="Gerar tabela (CSV)",
            command=self._on_generate_table,
            width=180,
        )
        self._table_button.pack(side="left", padx=(8, 0))

        self._model_picker = ModelPicker(
            container,
            on_change=self._on_model_change,
        )
        self._model_picker.pack(fill="x", pady=(8, 4))

        api_frame = ctk.CTkFrame(container, fg_color="transparent")
        api_frame.pack(fill="x", pady=(4, 4))
        self._api_label = ctk.CTkLabel(api_frame, text="API Key:")
        self._api_label.pack(side="left")
        self._api_entry = ctk.CTkEntry(api_frame, width=400, show="*")
        self._api_entry.pack(side="left", padx=(8, 0), fill="x", expand=True)

        prompt_frame = ctk.CTkFrame(container, fg_color="transparent")
        prompt_frame.pack(fill="x", pady=(4, 4))
        ctk.CTkLabel(prompt_frame, text="Instrução (prompt):", anchor="w").pack(
            anchor="w"
        )
        self._prompt_box = ctk.CTkTextbox(prompt_frame, height=90)
        self._prompt_box.pack(fill="x", pady=(4, 0))

        self._llm_button = ctk.CTkButton(
            container,
            text="Enviar à LLM",
            command=self._on_send_llm,
            height=36,
        )
        self._llm_button.pack(fill="x", pady=(8, 8))

        self._files_panel = GeneratedFilesPanel(container)
        self._files_panel.pack(fill="x", pady=(0, 8))

        self._log_panel = LogPanel(container)
        self._log_panel.pack(fill="both", expand=True)

    def _load_config(self) -> None:
        data = self._config_store.load()
        self._input_picker.set(data.get("input_dir", ""))
        self._output_picker.set(data.get("output_dir", ""))
        self._api_entry.insert(0, data.get("api_key", ""))
        self._set_prompt_text(data.get("user_prompt", DEFAULT_USER_PROMPT))

        catalog = catalog_from_config(data.get("model_catalog"))
        provider = data.get("provider", "ollama")
        model = data.get("model", DEFAULT_OLLAMA_MODEL)
        catalog = ensure_entry_in_catalog(catalog, provider, model)
        self._model_picker.set_catalog(catalog)
        self._model_picker.select_model(provider, model)
        selection = self._model_picker.get_selection()
        if selection is not None:
            self._on_model_change(selection)

    def _save_config(self) -> None:
        selection = self._model_picker.get_selection()
        if selection is None:
            return
        provider = selection.provider
        max_chars = (
            DEFAULT_MAX_CHARS_OPENROUTER
            if provider == "openrouter"
            else DEFAULT_MAX_CHARS_OLLAMA
        )
        self._config_store.save(
            {
                "input_dir": self._input_picker.get(),
                "output_dir": self._output_picker.get(),
                "provider": provider,
                "model": selection.model,
                "api_key": self._api_entry.get().strip(),
                "max_chars": max_chars,
                "model_catalog": catalog_to_config(self._model_picker.get_catalog()),
                "user_prompt": self._get_prompt_text(),
            }
        )

    def _get_prompt_text(self) -> str:
        return self._prompt_box.get("1.0", "end").strip()

    def _set_prompt_text(self, text: str) -> None:
        self._prompt_box.delete("1.0", "end")
        if text:
            self._prompt_box.insert("1.0", text)

    def _on_input_dir_change(self) -> None:
        self._files_panel.clear()

    def _on_output_dir_change(self) -> None:
        self._refresh_files_panel()

    def _refresh_files_panel(self) -> None:
        input_dir = Path(self._input_picker.get()) if self._input_picker.get() else Path()
        output_dir = Path(self._output_picker.get()) if self._output_picker.get() else Path()
        self._files_panel.set_directories(input_dir, output_dir)
        self._files_panel.refresh()

    def _on_model_change(self, selection: ModelEntry | None) -> None:
        if selection is None:
            return
        if selection.provider == "openrouter":
            self._api_label.pack(side="left")
            self._api_entry.pack(side="left", padx=(8, 0), fill="x", expand=True)
        else:
            self._api_label.pack_forget()
            self._api_entry.pack_forget()

    def _set_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self._extract_button.configure(state=state)
        self._table_button.configure(state=state)
        self._llm_button.configure(state=state)
        self._input_picker.configure_state(state)
        self._output_picker.configure_state(state)
        self._model_picker.configure_state(state)
        self._api_entry.configure(state=state)
        self._prompt_box.configure(state=state)

    def _on_progress(self, event: ProgressEvent) -> None:
        self.after(0, lambda: self._log_panel.append(event.message))

    def _validate_input_output_dirs(self) -> tuple[Path, Path] | None:
        if not self._input_picker.get():
            messagebox.showerror("Validação", "Selecione a pasta de PDFs.")
            return None
        if not self._output_picker.get():
            messagebox.showerror("Validação", "Selecione a pasta de saída.")
            return None
        return Path(self._input_picker.get()), Path(self._output_picker.get())

    def _validate_llm_config(self) -> JobConfig | None:
        dirs = self._validate_input_output_dirs()
        if dirs is None:
            return None
        input_dir, output_dir = dirs

        selection = self._model_picker.get_selection()
        if selection is None:
            messagebox.showerror("Validação", "Selecione um modelo.")
            return None

        user_prompt = self._get_prompt_text()
        if not user_prompt:
            messagebox.showerror("Validação", "Digite uma instrução (prompt) para a LLM.")
            return None

        filesystem = FileSystem()
        if not filesystem.list_resultados_txt(output_dir):
            messagebox.showinfo(
                "Validação",
                "Nenhum .txt encontrado em resultados/. Extraia os PDFs primeiro.",
            )
            return None

        provider = selection.provider
        api_key = self._api_entry.get().strip() or None
        max_chars = (
            DEFAULT_MAX_CHARS_OPENROUTER
            if provider == "openrouter"
            else DEFAULT_MAX_CHARS_OLLAMA
        )

        config = JobConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            provider=provider,
            model=selection.model,
            api_key=api_key,
            max_chars=max_chars,
            user_prompt=user_prompt,
        )

        try:
            llm = create_provider(config)
        except ConfigError as exc:
            messagebox.showerror("Validação", str(exc))
            return None

        if provider == "ollama" and not llm.health_check():
            messagebox.showerror(
                "Validação",
                "Ollama não está acessível em http://localhost:11434.",
            )
            return None

        output_dir.mkdir(parents=True, exist_ok=True)
        return config

    def _start_task(self, target, clear_log: bool = True) -> None:
        if clear_log:
            self._log_panel.clear()
        self._running = True
        self._set_controls_enabled(False)
        self._save_config()
        thread = threading.Thread(target=target, daemon=True)
        thread.start()

    def _on_task_complete(self) -> None:
        self._running = False
        self._set_controls_enabled(True)
        self._save_config()
        self._refresh_files_panel()

    def _on_extract(self) -> None:
        dirs = self._validate_input_output_dirs()
        if dirs is None:
            return
        input_dir, output_dir = dirs

        filesystem = FileSystem()
        if not filesystem.list_pdfs(input_dir):
            messagebox.showinfo("Validação", "Nenhum PDF encontrado na pasta de entrada.")
            return

        output_dir.mkdir(parents=True, exist_ok=True)

        def run() -> None:
            try:
                ExtractService(on_progress=self._on_progress).run(input_dir, output_dir)
            finally:
                self.after(0, self._on_task_complete)

        self._start_task(run)

    def _on_generate_table(self) -> None:
        dirs = self._validate_input_output_dirs()
        if dirs is None:
            return
        input_dir, output_dir = dirs

        filesystem = FileSystem()
        if not filesystem.list_resultados_txt(output_dir):
            messagebox.showinfo(
                "Validação",
                "Nenhum .txt encontrado em resultados/. Extraia os PDFs primeiro.",
            )
            return

        def run() -> None:
            try:
                TableService(on_progress=self._on_progress).run(output_dir, input_dir)
            finally:
                self.after(0, self._on_task_complete)

        self._start_task(run, clear_log=False)

    def _on_send_llm(self) -> None:
        config = self._validate_llm_config()
        if config is None:
            return

        def run() -> None:
            try:
                LlmService(on_progress=self._on_progress).run(config)
            finally:
                self.after(0, self._on_task_complete)

        self._start_task(run, clear_log=False)

    def _on_close(self) -> None:
        if self._running:
            if not messagebox.askyesno(
                "Confirmar",
                "Processamento em andamento. Deseja fechar mesmo assim?",
            ):
                return
        self._save_config()
        self.destroy()


def main() -> None:
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = MainWindow()
    app.mainloop()
