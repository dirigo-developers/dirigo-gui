import customtkinter as ctk

from dirigo import units
from dirigo.plugins.acquisitions import FrameAcquisitionSpec, FrameAcquisition


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
                self._start_callback(log_frames=False)
            else:
                self._stop_callback()

        elif type == 'capture':
            self._capture_running = not self._capture_running

            # enable/disable capture
            focus_state = ctk.DISABLED if self._capture_running else ctk.NORMAL
            self.focus_button.configure(state=focus_state)

            if self._capture_running:
                self.capture_button.configure(text="ABORT")
                self._start_callback(log_frames=True)
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


class FrameSpecificationControl(ctk.CTkFrame):
    def __init__(self, parent, spec_name = "default"):
        super().__init__(parent)

        spec: FrameAcquisitionSpec = FrameAcquisition.get_specification(spec_name) # TODO, load from previous session
        self._pixel_rate = spec.pixel_rate
        self._frame_width = spec.line_width
        self._frame_height = spec.frame_height
        self._pixel_width = spec.pixel_size
        self._pixel_height = spec.pixel_height
        self._fill_fraction = spec.fill_fraction
        self._frames_per_acquisition = spec.buffers_per_acquisition

        font = ctk.CTkFont(size=14, weight='bold')

        # Directions selector
        self.directions_var = ctk.StringVar(value="Unidirectional")
        self.directions = ctk.CTkSegmentedButton(
            self, 
            values=["Bidirectional", "Unidirectional"],
            variable=self.directions_var
        )
        self.directions.pack(padx=5, pady=5)

        # Pixel rate (if applicable)
        if self._pixel_rate:
            pixel_rate_frame = ctk.CTkFrame(self, fg_color="transparent")
            pixel_rate_label = ctk.CTkLabel(pixel_rate_frame, text="Pixel Rate", font=font)
            pixel_rate_label.grid(row=0, column=0, sticky="w")
            self.pixel_rate = ctk.CTkEntry(pixel_rate_frame, width=60)
            self.pixel_rate.grid(row=0, column=1)
            self.pixel_rate.insert(0, str(self._pixel_rate))
            self.pixel_rate.bind("<Return>", lambda e: self.update_pixel_rate())
            self.pixel_rate.bind("<FocusOut>", lambda e: self.update_pixel_rate())
            pixel_rate_frame.pack(padx=5, pady=5)

        # Frame size
        frame_size_frame = ctk.CTkFrame(self, fg_color="transparent")
        r = 0

        frame_size_label = ctk.CTkLabel(frame_size_frame, text="Frame Size", font=font)
        frame_size_label.grid(row=r, columnspan=4, sticky="w")
        r += 1

        frame_width_label = ctk.CTkLabel(frame_size_frame, text="Width:")
        frame_width_label.grid(row=r, column=0, padx=4)
        self.frame_width = ctk.CTkEntry(frame_size_frame, width=60)
        self.frame_width.insert(0, str(self._frame_width))
        self.frame_width.grid(row=r, column=1)
        self.frame_width.bind("<Return>", lambda e: self.update_frame_width())
        self.frame_width.bind("<FocusOut>", lambda e: self.update_frame_width())
        
        frame_height_label = ctk.CTkLabel(frame_size_frame, text="Height:")
        frame_height_label.grid(row=r, column=2, padx=4)
        self.frame_height = ctk.CTkEntry(frame_size_frame, width=60)
        self.frame_height.insert(0, str(self._frame_height))
        self.frame_height.grid(row=r, column=3)
        self.frame_height.bind("<Return>", lambda e: self.update_frame_height())
        self.frame_height.bind("<FocusOut>", lambda e: self.update_frame_height())
        r += 1

        self._square_frame_var = ctk.BooleanVar(value=True)
        self.square_frame = ctk.CTkCheckBox(
            frame_size_frame,
            text="Square Frame",
            width=10,
            height=10,
            variable=self._square_frame_var,
            command=None
        )
        self.square_frame.grid(row=r, columnspan=4, padx=5, pady=5, sticky="w")

        frame_size_frame.pack(padx=5, pady=5)

        # Pixel size
        pixel_size_frame = ctk.CTkFrame(self, fg_color="transparent")
        r = 0

        pixel_size_label = ctk.CTkLabel(pixel_size_frame, text="Pixel Size", font=font)
        pixel_size_label.grid(row=r, columnspan=2, sticky="w")
        r += 1

        pixel_width_label = ctk.CTkLabel(pixel_size_frame, text="Width:")
        pixel_width_label.grid(row=r, column=0, padx=4)
        self.pixel_width = ctk.CTkEntry(pixel_size_frame, width=60)
        self.pixel_width.insert(0, str(self._pixel_width))
        self.pixel_width.grid(row=r, column=1)
        self.pixel_width.bind("<Return>", lambda e: self.update_pixel_width())
        self.pixel_width.bind("<FocusOut>", lambda e: self.update_pixel_width())

        pixel_height_label = ctk.CTkLabel(pixel_size_frame, text="Height:")
        pixel_height_label.grid(row=r, column=2, padx=4)
        self.pixel_height = ctk.CTkEntry(pixel_size_frame, width=60)
        self.pixel_height.insert(0, str(self._pixel_height))
        self.pixel_height.grid(row=r, column=3)
        self.pixel_height.bind("<Return>", lambda e: self.update_pixel_height())
        self.pixel_height.bind("<FocusOut>", lambda e: self.update_pixel_height())
        r += 1

        self._square_pixel_var = ctk.BooleanVar(value=True)
        self.square_pixel = ctk.CTkCheckBox(
            pixel_size_frame,
            text="Square Pixel",
            width=10,
            height=10,
            variable=self._square_pixel_var,
            command=None
        )
        self.square_pixel.grid(row=r, columnspan=4, padx=5, pady=5, sticky="w")

        pixel_size_frame.pack(padx=5, pady=5)
        
        # fill fraction
        fill_fraction_frame = ctk.CTkFrame(self, fg_color="transparent")
        fill_fraction_label = ctk.CTkLabel(fill_fraction_frame, text="Fill Fraction")
        fill_fraction_label.grid(row=0, column=0, padx=4)
        self.fill_fraction = ctk.CTkEntry(fill_fraction_label, width=60)
        self.fill_fraction.insert(0, str(self._fill_fraction))
        self.fill_fraction.grid(row=0, column=1)
        self.fill_fraction.bind("<Return>", lambda e: self.update_fill_fraction())
        self.fill_fraction.bind("<FocusOut>", lambda e: self.update_fill_fraction())

        fill_fraction_frame.pack(padx=5, pady=5)

        # frames per acquisition
        frames_per_acq_frame = ctk.CTkFrame(self, fg_color="transparent")
        frames_per_acq_label = ctk.CTkLabel(frames_per_acq_frame, text="Frames to Capture")
        frames_per_acq_label.grid(row=0, column=0, padx=4)
        self.frames_per_acquisition = ctk.CTkEntry(frames_per_acq_frame, width=60)
        self.frames_per_acquisition.insert(0, str(self._frames_per_acquisition))
        self.frames_per_acquisition.grid(row=0, column=1)
        self.frames_per_acquisition.bind(
            "<Return>", lambda e: self.update_frames_per_acquisition()
        )
        self.frames_per_acquisition.bind(
            "<FocusOut>", lambda e: self.update_frames_per_acquisition()
        )

        frames_per_acq_frame.pack(padx=5, pady=5)

        # flyback periods
        pass

    def update_pixel_rate(self):
        try:
            self._pixel_rate = units.Frequency(self.pixel_rate.get())
        except ValueError:
            pass # probably something should happen instead

        self.pixel_rate.delete(0, ctk.END)
        self.pixel_rate.insert(0, str(self._pixel_rate))

    def update_frame_height(self):
        try:
            self._frame_height = units.Position(self.frame_height.get())
        except ValueError:
            pass # probably something should happen instead

        self.frame_height.delete(0, ctk.END)
        self.frame_height.insert(0, str(self._frame_height))

        # If using square frame, then also update frame width
        if self._square_frame_var.get():
            self._frame_width = self._frame_height
            self.frame_width.delete(0, ctk.END)
            self.frame_width.insert(0, str(self._frame_height))

    def update_frame_width(self):
        try:
            self._frame_width = units.Position(self.frame_width.get())
        except ValueError:
            pass # probably something should happen instead

        self.frame_width.delete(0, ctk.END)
        self.frame_width.insert(0, str(self._frame_width))

        # If using square frame, then also update frame height
        if self._square_frame_var.get():
            self._frame_height = self._frame_width
            self.frame_height.delete(0, ctk.END)
            self.frame_height.insert(0, str(self._frame_width))

    def update_pixel_height(self):
        try:
            self._pixel_height = units.Position(self.pixel_height.get())
        except ValueError:
            pass # probably something should happen instead
        
        # Update the pixel height field
        self.pixel_height.delete(0, ctk.END)
        self.pixel_height.insert(0, str(self._pixel_height))

        # If using square pixels, then also update pixel width
        if self._square_pixel_var.get():
            self._pixel_width = self._pixel_height
            self.pixel_width.delete(0, ctk.END)
            self.pixel_width.insert(0, str(self._pixel_height))

    def update_pixel_width(self):
        try:
            self._pixel_width = units.Position(self.pixel_width.get())
        except ValueError:
            pass # probably something should happen instead
        
        # Update the pixel width field
        self.pixel_width.delete(0, ctk.END)
        self.pixel_width.insert(0, str(self._pixel_width))

        # If using square pixels, then also update pixel height
        if self._square_pixel_var.get():
            self._pixel_height = self._pixel_width
            self.pixel_height.delete(0, ctk.END)
            self.pixel_height.insert(0, str(self._pixel_width))

    def update_fill_fraction(self):
        pass

    def update_frames_per_acquisition(self):
        pass
    
    def generate_spec(self) -> FrameAcquisitionSpec:
        return FrameAcquisitionSpec(
            bidirectional_scanning=(self.directions_var.get() == "Bidirectional"),
            line_width=self._frame_width,
            frame_height=self._frame_height,
            pixel_rate=self._pixel_rate,
            pixel_size=self._pixel_width,
            pixel_height=self._pixel_height,
            fill_fraction = self._fill_fraction,
            buffers_per_acquisition=self._frames_per_acquisition,
            buffers_allocated=4, # TODO not hardcode
            digitizer_profile = "default",
            flyback_periods=4 # TODO update this
        )
    



if __name__ == "__main__":
    root = ctk.CTk()
    sc = FrameSpecificationControl(root)
    sc.pack()
    root.mainloop()

