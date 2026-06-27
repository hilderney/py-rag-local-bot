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
from pdf_summarizer.services.pipeline import PipelineService
from pdf_summarizer.ui.widgets.folder_picker import FolderPicker
from pdf_summarizer.ui.widgets.log_panel import LogPanel
from pdf_summarizer.ui.widgets.model_picker import ModelPicker


class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PDF Summarizer")
        self.geometry("720x720")
        self.minsize(640, 600)

        self._config_store = ConfigStore()
        self._running = False

        self._build_ui()
        self._load_config()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        self._input_picker = FolderPicker(container, "Pasta de PDFs:")
        self._input_picker.pack(fill="x")

        self._output_picker = FolderPicker(container, "Pasta de saída:")
        self._output_picker.pack(fill="x")

        self._model_picker = ModelPicker(
            container,
            on_change=self._on_model_change,
        )
        self._model_picker.pack(fill="x", pady=(4, 4))

        api_frame = ctk.CTkFrame(container, fg_color="transparent")
        api_frame.pack(fill="x", pady=(4, 4))
        self._api_label = ctk.CTkLabel(api_frame, text="API Key:")
        self._api_label.pack(side="left")
        self._api_entry = ctk.CTkEntry(api_frame, width=400, show="*")
        self._api_entry.pack(side="left", padx=(8, 0), fill="x", expand=True)

        prompt_frame = ctk.CTkFrame(container, fg_color="transparent")
        prompt_frame.pack(fill="x", pady=(4, 4))
        ctk.CTkLabel(
            prompt_frame,
            text="Instrução (prompt):",
        ).pack(anchor="w")
        self._prompt_box = ctk.CTkTextbox(prompt_frame, height=100)
        self._prompt_box.pack(fill="x", pady=(4, 0))

        self._run_button = ctk.CTkButton(
            container,
            text="▶ Executar",
            command=self._on_run,
            height=36,
        )
        self._run_button.pack(fill="x", pady=(8, 8))

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
        self._run_button.configure(state=state)
        self._input_picker.configure_state(state)
        self._output_picker.configure_state(state)
        self._model_picker.configure_state(state)
        self._api_entry.configure(state=state)
        self._prompt_box.configure(state=state)

    def _on_progress(self, event: ProgressEvent) -> None:
        self.after(0, lambda: self._log_panel.append(event.message))

    def _validate_before_run(self) -> JobConfig | None:
        input_dir = Path(self._input_picker.get())
        output_dir = Path(self._output_picker.get())

        if not self._input_picker.get():
            messagebox.showerror("Validação", "Selecione a pasta de PDFs.")
            return None
        if not self._output_picker.get():
            messagebox.showerror("Validação", "Selecione a pasta de saída.")
            return None

        selection = self._model_picker.get_selection()
        if selection is None:
            messagebox.showerror("Validação", "Selecione um modelo.")
            return None

        user_prompt = self._get_prompt_text()
        if not user_prompt:
            messagebox.showerror("Validação", "Digite uma instrução (prompt) para a LLM.")
            return None

        filesystem = FileSystem()
        pdfs = filesystem.list_pdfs(input_dir)
        if not pdfs:
            messagebox.showinfo(
                "Validação",
                "Nenhum PDF encontrado na pasta de entrada.",
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

    def _run_pipeline(self, config: JobConfig) -> None:
        try:
            pipeline = PipelineService(on_progress=self._on_progress)
            pipeline.run(config)
        finally:
            self.after(0, self._on_run_complete)

    def _on_run_complete(self) -> None:
        self._running = False
        self._set_controls_enabled(True)
        self._save_config()

    def _on_run(self) -> None:
        config = self._validate_before_run()
        if config is None:
            return

        self._log_panel.clear()
        self._running = True
        self._set_controls_enabled(False)
        self._save_config()

        thread = threading.Thread(
            target=self._run_pipeline,
            args=(config,),
            daemon=True,
        )
        thread.start()

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
