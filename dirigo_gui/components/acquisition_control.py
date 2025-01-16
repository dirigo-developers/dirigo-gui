import customtkinter as ctk


class AcquisitionControl(ctk.CTkFrame):
    BUTTON_WIDTH = 100
    BUTTON_HEIGHT = 40
    BUTTON_FONT_SIZE = 16

    def __init__(self, parent, start_callback, stop_callback):
        super().__init__(parent)
        
        self._start_callback = start_callback
        self._stop_callback = stop_callback
        self._focus_running = False
        self._capture_running = False

        self.focus_button = ctk.CTkButton(
            self, 
            text="FOCUS", 
            font=ctk.CTkFont(size=self.BUTTON_FONT_SIZE, weight="bold"),
            width=self.BUTTON_WIDTH,
            height=self.BUTTON_HEIGHT,
            command=lambda: self.start('focus')
        )
        self.focus_button.grid(row=0, column=0, padx=5)

        self.capture_button = ctk.CTkButton(
            self, 
            text="CAPTURE",
            font=ctk.CTkFont(size=self.BUTTON_FONT_SIZE, weight="bold"),
            width=self.BUTTON_WIDTH,
            height=self.BUTTON_HEIGHT,
            command=lambda: self.start('capture')
        )
        self.capture_button.grid(row=0, column=1, padx=5)


    def start(self, type: str):
        if type == 'focus':
            self._focus_running = not self._focus_running

            # enable/disable capture
            capture_state = ctk.DISABLED if self._focus_running else ctk.NORMAL
            self.capture_button.configure(state=capture_state)

            if self._focus_running:
                self.focus_button.configure(text="STOP")
                self._start_callback('focus')
            else:
                self._stop_callback()

        elif type == 'capture':
            self._capture_running = not self._capture_running

            # enable/disable capture
            focus_state = ctk.DISABLED if self._capture_running else ctk.NORMAL
            self.focus_button.configure(state=focus_state)

            if self._capture_running:
                self.capture_button.configure(text="ABORT")
                self._start_callback('capture')
            else:
                self._stop_callback()

    def stopped(self):
        """Reset internal flags and button states"""
        self._focus_running = False
        self._capture_running = False

        self.focus_button.configure(state=ctk.NORMAL, text="FOCUS")
        self.capture_button.configure(state=ctk.NORMAL, text="CAPTURE")

    @property  
    def acquisition_running(self) -> bool:
        return True if self._focus_running or self._capture_running else False

