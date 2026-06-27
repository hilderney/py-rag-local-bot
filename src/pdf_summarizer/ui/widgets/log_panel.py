import tkinter as tk
from tkinter import scrolledtext


class LogPanel(tk.Frame):
    """Painel de log append-only com auto-scroll."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, **kwargs)
        tk.Label(self, text="Log:", anchor="w").pack(fill="x")
        self._text = scrolledtext.ScrolledText(self, height=16, state="disabled")
        self._text.pack(fill="both", expand=True)

    def append(self, message: str) -> None:
        self._text.configure(state="normal")
        self._text.insert("end", message + "\n")
        self._text.see("end")
        self._text.configure(state="disabled")

    def clear(self) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.configure(state="disabled")
