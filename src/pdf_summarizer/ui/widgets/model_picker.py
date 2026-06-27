import tkinter as tk
from collections.abc import Callable

import customtkinter as ctk

from pdf_summarizer.core.model_catalog import (
    PROVIDER_LABELS,
    ModelEntry,
    ProviderName,
    parse_model_label,
)


class ModelPicker(ctk.CTkFrame):
    """Dropdown de modelos com origem (Ollama/OpenRouter) e inclusão/remoção."""

    def __init__(
        self,
        master,
        label: str = "Modelo:",
        on_change: Callable[[ModelEntry], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_change = on_change
        self._catalog: list[ModelEntry] = []
        self._selected: ModelEntry | None = None

        ctk.CTkLabel(self, text=label).pack(side="left")
        self._combo = ctk.CTkComboBox(
            self,
            values=[],
            command=self._handle_selection,
            width=420,
        )
        self._combo.pack(side="left", padx=(8, 4), fill="x", expand=True)

        self._add_button = ctk.CTkButton(
            self,
            text="+",
            width=32,
            command=self._on_add,
        )
        self._add_button.pack(side="left", padx=(0, 4))
        self._remove_button = ctk.CTkButton(
            self,
            text="−",
            width=32,
            command=self._on_remove,
        )
        self._remove_button.pack(side="left")

    def set_catalog(self, catalog: list[ModelEntry]) -> None:
        self._catalog = list(catalog)
        self._refresh_combo_values()

    def get_catalog(self) -> list[ModelEntry]:
        return list(self._catalog)

    def get_selection(self) -> ModelEntry | None:
        return self._selected

    def select_model(self, provider: ProviderName, model: str) -> None:
        for entry in self._catalog:
            if entry.model == model and entry.provider == provider:
                self._set_selection(entry)
                return
        if self._catalog:
            self._set_selection(self._catalog[0])

    def configure_state(self, state: str) -> None:
        self._combo.configure(state=state)
        self._add_button.configure(state=state)
        self._remove_button.configure(state=state)

    def _refresh_combo_values(self) -> None:
        labels = [entry.label for entry in self._catalog]
        self._combo.configure(command=None)
        self._combo.configure(values=labels)
        self._combo.configure(command=self._handle_selection)
        self._remove_button.configure(state="normal" if len(self._catalog) > 1 else "disabled")
        current_label = self._selected.label if self._selected else ""
        if current_label not in labels and labels:
            self._set_selection(self._catalog[0])

    def _set_selection(self, entry: ModelEntry) -> None:
        self._selected = entry
        self._combo.configure(command=None)
        self._combo.set(entry.label)
        self._combo.configure(command=self._handle_selection)

    def _handle_selection(self, choice: str) -> None:
        try:
            entry = parse_model_label(choice)
        except ValueError:
            return
        self._selected = entry
        if self._on_change is not None:
            self._on_change(entry)

    def _on_add(self) -> None:
        dialog = _AddModelDialog(self)
        self.wait_window(dialog)
        if dialog.result is None:
            return

        if dialog.result in self._catalog:
            self.select_model(dialog.result.provider, dialog.result.model)
            return

        self._catalog.append(dialog.result)
        self._refresh_combo_values()
        self._set_selection(dialog.result)
        if self._on_change is not None:
            self._on_change(dialog.result)

    def _on_remove(self) -> None:
        if self._selected is None or len(self._catalog) <= 1:
            return

        self._catalog = [item for item in self._catalog if item != self._selected]
        self._refresh_combo_values()
        if self._catalog:
            self._set_selection(self._catalog[0])
            if self._on_change is not None:
                self._on_change(self._catalog[0])


class _AddModelDialog(ctk.CTkToplevel):
    def __init__(self, parent: ModelPicker) -> None:
        super().__init__(parent)
        self.result: ModelEntry | None = None
        self.title("Adicionar modelo")
        self.geometry("420x180")
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(frame, text="Nome do modelo:").pack(anchor="w")
        self._model_entry = ctk.CTkEntry(frame, width=360)
        self._model_entry.pack(fill="x", pady=(4, 12))
        self._model_entry.focus()

        ctk.CTkLabel(frame, text="Origem:").pack(anchor="w")
        self._provider_var = tk.StringVar(value="ollama")
        provider_row = ctk.CTkFrame(frame, fg_color="transparent")
        provider_row.pack(fill="x", pady=(4, 12))
        ctk.CTkRadioButton(
            provider_row,
            text=PROVIDER_LABELS["ollama"],
            variable=self._provider_var,
            value="ollama",
        ).pack(side="left", padx=(0, 12))
        ctk.CTkRadioButton(
            provider_row,
            text=PROVIDER_LABELS["openrouter"],
            variable=self._provider_var,
            value="openrouter",
        ).pack(side="left")

        buttons = ctk.CTkFrame(frame, fg_color="transparent")
        buttons.pack(fill="x")
        ctk.CTkButton(buttons, text="Cancelar", command=self._cancel, width=100).pack(
            side="right", padx=(8, 0)
        )
        ctk.CTkButton(buttons, text="Adicionar", command=self._confirm, width=100).pack(
            side="right"
        )

        self.bind("<Return>", lambda _event: self._confirm())
        self.bind("<Escape>", lambda _event: self._cancel())

    def _confirm(self) -> None:
        model = self._model_entry.get().strip()
        if not model:
            return
        provider: ProviderName = self._provider_var.get()  # type: ignore[assignment]
        self.result = ModelEntry(model=model, provider=provider)
        self.destroy()

    def _cancel(self) -> None:
        self.destroy()
