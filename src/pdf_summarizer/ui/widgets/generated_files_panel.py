import os
from pathlib import Path

import customtkinter as ctk

from pdf_summarizer.core.artifacts import ArtifactPaths, scan_generated_files


class GeneratedFilesPanel(ctk.CTkFrame):
    """Lista artefatos gerados por PDF com botões para abrir arquivos."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._input_dir = Path()
        self._output_dir = Path()

        ctk.CTkLabel(self, text="Arquivos gerados:", anchor="w").pack(
            fill="x", padx=4, pady=(0, 4)
        )
        self._scroll = ctk.CTkScrollableFrame(self, height=140)
        self._scroll.pack(fill="both", expand=True)

    def set_directories(self, input_dir: Path, output_dir: Path) -> None:
        self._input_dir = input_dir
        self._output_dir = output_dir

    def clear(self) -> None:
        for widget in self._scroll.winfo_children():
            widget.destroy()

    def refresh(self) -> None:
        self.clear()
        if not self._input_dir.is_dir():
            ctk.CTkLabel(
                self._scroll,
                text="Selecione a pasta de PDFs para listar arquivos.",
                anchor="w",
            ).pack(fill="x", padx=4, pady=2)
            return

        artifacts = scan_generated_files(self._input_dir, self._output_dir)
        if not artifacts:
            ctk.CTkLabel(
                self._scroll,
                text="Nenhum PDF encontrado na pasta de entrada.",
                anchor="w",
            ).pack(fill="x", padx=4, pady=2)
            return

        for item in artifacts:
            self._add_row(item)

    def _add_row(self, item: ArtifactPaths) -> None:
        row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        row.pack(fill="x", padx=2, pady=2)

        label = item.stem
        if len(label) > 40:
            label = label[:37] + "..."
        ctk.CTkLabel(row, text=label, width=180, anchor="w").pack(side="left")

        self._add_open_button(row, "TXT", item.txt)
        self._add_open_button(row, "CSV", item.csv)
        self._add_open_button(row, "JSON", item.json)

    def _add_open_button(
        self,
        parent: ctk.CTkFrame,
        kind: str,
        path: Path | None,
    ) -> None:
        enabled = path is not None and path.is_file()
        button = ctk.CTkButton(
            parent,
            text=kind,
            width=56,
            height=24,
            state="normal" if enabled else "disabled",
            command=lambda p=path: self._open_file(p),
        )
        button.pack(side="left", padx=2)

    @staticmethod
    def _open_file(path: Path | None) -> None:
        if path is None or not path.is_file():
            return
        os.startfile(path)
