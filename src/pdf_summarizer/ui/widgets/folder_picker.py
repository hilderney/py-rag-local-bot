import tkinter as tk
from tkinter import filedialog


class FolderPicker(tk.Frame):
    """Campo de texto + botão para selecionar pasta."""

    def __init__(self, master, label: str, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._var = tk.StringVar()

        tk.Label(self, text=label, anchor="w").pack(fill="x")
        row = tk.Frame(self)
        row.pack(fill="x", pady=(2, 8))

        self._entry = tk.Entry(row, textvariable=self._var)
        self._entry.pack(side="left", fill="x", expand=True)

        tk.Button(row, text="Procurar...", command=self._browse).pack(side="left", padx=(4, 0))

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
