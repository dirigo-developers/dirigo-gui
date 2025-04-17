import customtkinter as ctk
from tkinter import filedialog

from platformdirs import user_documents_path

from dirigo.sw_interfaces import Logger



class LoggerControl(ctk.CTkFrame):
    def __init__(self, parent, title="Data Logging", frames_per_file=256):
        super().__init__(parent)

        # Set default data save path
        self.save_path = user_documents_path() / "Dirigo"
        self.frames_per_file = frames_per_file

        # Title Label
        self.title_label = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=16, weight="bold"))
        self.title_label.grid(row=0, column=0, columnspan=3, pady=(5, 5), padx=10, sticky='w')
        
        # Basename Entry
        self.basename_label = ctk.CTkLabel(self, text="Basename:", font=ctk.CTkFont(size=14, weight="bold"))
        self.basename_label.grid(row=1, column=0, sticky="e", padx=5, pady=2)
        
        self.basename_entry = ctk.CTkEntry(self, placeholder_text="file")
        self.basename_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=2, sticky="ew")

        # Frames per File
        frames_per_file_label = ctk.CTkLabel(self, text="Frames/File:", font=ctk.CTkFont(size=14, weight="bold"))
        frames_per_file_label.grid(row=2, column=0, sticky="e", padx=5, pady=2)
        self._frames_per_file_var = ctk.StringVar(value=int(self.frames_per_file))
        self._frames_per_file_entry = ctk.CTkEntry(self, textvariable=self._frames_per_file_var, width=70)
        self._frames_per_file_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        self._frames_per_file_entry.bind("<Return>", self._validate_frames_per_file_input)  # Enter key
        self._frames_per_file_entry.bind("<FocusOut>", self._validate_frames_per_file_input)  # Focus out

        # Directory Selection
        self.directory_button = ctk.CTkButton(self, text="Path...", command=self.select_save_path, width=20)
        self.directory_button.grid(row=2, column=2, padx=5, pady=2)

        # Save Raw Data
        save_raw_label = ctk.CTkLabel(self, text="Save Raw:", font=ctk.CTkFont(size=14, weight="bold"))
        save_raw_label.grid(row=3, column=0, sticky="e")
        self.save_raw_checkbox = ctk.CTkCheckBox(self, text="")
        self.save_raw_checkbox.grid(row=3, column=1, columnspan=2, sticky="w", padx=5, pady=2)

        # Configure resizing
        self.columnconfigure(1, weight=1)

    def _validate_frames_per_file_input(self, event=None):
        """Validates the input of the Entry widget."""
        value = self._frames_per_file_var.get().strip()

        if value.lower() in {"inf", "infinity", "∞"}:
            self._frames_per_file_var.set("Inf")
            self.frames_per_file = float('Inf')
        else:
            try:
                number = int(value)
                if number < 1:
                    # revert value
                    self._frames_per_file_var.set(str(self.frames_per_file))
                else:
                    # The input is an int and >=1, record it in public attribute
                    self.frames_per_file = value

            except ValueError:
                # revert value
                self._frames_per_file_var.set(str(self.frames_per_file))

    def select_save_path(self):
        self.save_path = filedialog.askdirectory(initialdir=self.save_path)
        if self.save_path:
            print(f"Selected directory: {self.save_path}")

    def link_logger_worker(self, logger_worker: Logger):
        """Transfer logger GUI settings to the logger worker (thread)."""
        logger_worker.save_path = self.save_path
        logger_worker.basename = self.basename_entry.get()
        logger_worker.frames_per_file = int(self._frames_per_file_entry.get())


