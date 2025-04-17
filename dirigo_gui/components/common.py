from typing import Callable

import customtkinter as ctk



class LabeledEntry(ctk.CTkFrame):
    """Label + CTkEntry whose value lives in a StringVar."""
    def __init__(self, parent, text: str, *, 
                 default: str,
                 on_validate: Callable[[str], None], 
                 width: int = 60):
        
        super().__init__(parent, fg_color="transparent")
        self.var = ctk.StringVar(value=default)
        ctk.CTkLabel(self, text=text).pack(side="left", padx=(0, 4))
        self._ent = ctk.CTkEntry(self, textvariable=self.var, width=width)
        self._ent.pack(side="left")
        # Call once per keystroke *and* when set programmatically.
        #self.var.trace_add("write", lambda *_: on_change(self.var.get()))
        self._ent.bind("<Return>",   lambda _e: on_validate(self.var.get()))
        self._ent.bind("<FocusOut>", lambda _e: on_validate(self.var.get()))

        self._normal_color = self._ent.cget("text_color")

    def set_text_red(self) -> None:
        self._ent.configure(text_color="red")

    def set_text_normal(self) -> None:
        self._ent.configure(text_color=self._normal_color)

    def set(self, value: str) -> None:
        self.var.set(value)