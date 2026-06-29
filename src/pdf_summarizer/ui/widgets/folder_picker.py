import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog


class FolderPicker(tk.Frame):
    """Campo de texto + botão para selecionar pasta."""

    def __init__(
        self,
        master,
        label: str,
        on_change: Callable[[], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_change = on_change
        self._var = tk.StringVar()
        self._var.trace_add("write", self._handle_var_change)

        tk.Label(self, text=label, anchor="w").pack(fill="x")
        self._row = tk.Frame(self)
        self._row.pack(fill="x", pady=(2, 8))

        self._entry = tk.Entry(self._row, textvariable=self._var)
        self._entry.pack(side="left", fill="x", expand=True)

        tk.Button(self._row, text="Procurar...", command=self._browse).pack(
            side="left", padx=(4, 0)
        )

    def _handle_var_change(self, *_args) -> None:
        if self._on_change is not None:
            self._on_change()

    def _browse(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self._var.set(path)

    def get(self) -> str:
        return self._var.get().strip()

    def set(self, value: str) -> None:
        self._var.set(value)

    def configure_state(self, state: str) -> None:
        self._entry.configure(state=state)

    def get_row_frame(self) -> tk.Frame:
        return self._row
