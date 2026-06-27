import tkinter as tk
from pathlib import Path

import customtkinter as ctk

from pdf_summarizer.core.model_catalog import (
    ModelEntry,
    catalog_from_config,
    catalog_to_config,
    ensure_entry_in_catalog,
)
from pdf_summarizer.ui.widgets.model_picker import ModelPicker


def test_model_picker_starts_with_catalog():
    root = ctk.CTk()
    root.withdraw()
    catalog = [
        ModelEntry("gemma3:270m", "ollama"),
        ModelEntry("nvidia/test:free", "openrouter"),
    ]
    picker = ModelPicker(root)
    picker.set_catalog(catalog)
    picker.select_model("openrouter", "nvidia/test:free")
    assert picker.get_selection() == ModelEntry("nvidia/test:free", "openrouter")
    root.destroy()


def test_model_picker_remove_keeps_at_least_one():
    root = ctk.CTk()
    root.withdraw()
    catalog = [
        ModelEntry("gemma3:270m", "ollama"),
        ModelEntry("phi3", "ollama"),
    ]
    picker = ModelPicker(root)
    picker.set_catalog(catalog)
    picker.select_model("ollama", "phi3")
    picker._on_remove()
    assert len(picker.get_catalog()) == 1
    assert picker.get_selection() == ModelEntry("gemma3:270m", "ollama")
    root.destroy()
