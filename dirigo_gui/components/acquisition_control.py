import customtkinter as ctk

from dirigo import units
from dirigo.components.hardware import Hardware
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
    def __init__(self, parent, timing_indicator: 'TimingIndicator', spec_name = "default"):
        super().__init__(parent)

        spec: FrameAcquisitionSpec = FrameAcquisition.get_specification(spec_name) # TODO, load from previous session

        self._pixel_time = spec.pixel_time if hasattr(spec, 'pixel_time') else None # aka dwell time
        self._frame_width = spec.line_width
        self._frame_height = spec.frame_height
        self._pixel_width = spec.pixel_size
        self._pixel_height = spec.pixel_height
        self._shape_width = 100
        self._shape_height = 100
        self._fill_fraction = spec.fill_fraction
        self._frames_per_acquisition = spec.buffers_per_acquisition
        self._timing_indicator = timing_indicator

        font = ctk.CTkFont(size=14, weight='bold')

        # Directions selector
        self.directions_var = ctk.StringVar(
            value="Bidirectional" if spec.bidirectional_scanning else "Unidirectional"
        )
        self.directions = ctk.CTkSegmentedButton(
            self, 
            values=["Bidirectional", "Unidirectional"],
            variable=self.directions_var,
            command=lambda e: self.update_bidi()
        )
        self.directions.pack(padx=5, pady=10)

        # Frame size
        frame_size_frame = ctk.CTkFrame(self, fg_color="transparent")
        r = 0

        frame_size_label = ctk.CTkLabel(frame_size_frame, text="Frame Size:", font=font)
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

        array_shape_label = ctk.CTkLabel(frame_size_frame, text="Array Shape:", font=font)
        array_shape_label.grid(row=r, columnspan=2, sticky="w")
        r += 1

        shape_width_label = ctk.CTkLabel(frame_size_frame, text="Width:")
        shape_width_label.grid(row=r, column=0, padx=4)
        self.shape_width = ctk.CTkEntry(frame_size_frame, width=60)
        self.shape_width.insert(0, str(self._shape_width))
        self.shape_width.grid(row=r, column=1)
        self.shape_width.bind("<Return>", lambda e: self.update_shape_width())
        self.shape_width.bind("<FocusOut>", lambda e: self.update_shape_width())

        shape_height_label = ctk.CTkLabel(frame_size_frame, text="Height:")
        shape_height_label.grid(row=r, column=2, padx=4)
        self.shape_height = ctk.CTkEntry(frame_size_frame, width=60)
        self.shape_height.insert(0, str(self._shape_height))
        self.shape_height.grid(row=r, column=3)
        self.shape_height.bind("<Return>", lambda e: self.update_shape_height())
        self.shape_height.bind("<FocusOut>", lambda e: self.update_shape_height())
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

        pixel_size_label = ctk.CTkLabel(pixel_size_frame, text="Pixel Size:", font=font)
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

        # Misc settings put in to orderly grid
        settings_grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        r = 0

        # Pixel (dwell) time (if applicable)
        if self._pixel_time:
            pixel_time_label = ctk.CTkLabel(settings_grid_frame, text="Pixel Time:", font=font)
            pixel_time_label.grid(row=r, column=0, padx=5, sticky="e")
            self.pixel_time = ctk.CTkEntry(settings_grid_frame, width=70)
            self.pixel_time.grid(row=r, pady=3, column=1, sticky='w')
            self.pixel_time.insert(0, str(self._pixel_time))
            self.pixel_time.bind("<Return>", lambda e: self.update_pixel_time())
            self.pixel_time.bind("<FocusOut>", lambda e: self.update_pixel_time())
            r += 1

        # fill fraction
        fill_fraction_label = ctk.CTkLabel(settings_grid_frame, text="Fill Fraction:", font=font)
        fill_fraction_label.grid(row=r, column=0, padx=5, sticky='e')
        self.fill_fraction = ctk.CTkEntry(settings_grid_frame, width=70)
        self.fill_fraction.insert(0, str(self._fill_fraction))
        self.fill_fraction.grid(row=r, pady=3, column=1, sticky='w')
        self.fill_fraction.bind("<Return>", lambda e: self.update_fill_fraction())
        self.fill_fraction.bind("<FocusOut>", lambda e: self.update_fill_fraction())
        r += 1

        # frames per acquisition
        frames_per_acq_label = ctk.CTkLabel(settings_grid_frame, text="Frames:", font=font)
        frames_per_acq_label.grid(row=r, column=0, padx=5, sticky='e')
        self.frames_per_acquisition = ctk.CTkEntry(settings_grid_frame, width=70)
        self.frames_per_acquisition.insert(0, str(self._frames_per_acquisition))
        self.frames_per_acquisition.grid(row=r, pady=3, column=1, sticky='w')
        self.frames_per_acquisition.bind(
            "<Return>", lambda e: self.update_frames_per_acquisition()
        )
        self.frames_per_acquisition.bind(
            "<FocusOut>", lambda e: self.update_frames_per_acquisition()
        )
        r += 1

        # flyback periods

        settings_grid_frame.pack(padx=0, pady=0, fill='x')

        # update some calculated settings
        self.update_array_shape()

    def update_bidi(self):
        self._timing_indicator.update(self.generate_spec())

    def update_pixel_time(self):
        try:
            self._pixel_time = units.Time(self.pixel_time.get())
        except ValueError:
            pass # probably something should happen instead

        self.pixel_time.delete(0, ctk.END)
        self.pixel_time.insert(0, str(self._pixel_time))

        self._timing_indicator.update(self.generate_spec())

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

        self.update_array_shape()
        self._timing_indicator.update(self.generate_spec())

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

        self.update_array_shape()
        self._timing_indicator.update(self.generate_spec())

    def update_shape_width(self):
        # When changing the image array shape (ie resolution)
        try:
            self._shape_width = int(self.shape_width.get())
        except:
            self.shape_width.delete(0, ctk.END)
            self.shape_width.insert(0, str(self._shape_width))
            return

        # adjust pixel width
        self._pixel_width = self._frame_width / self._shape_width
        self.pixel_width.delete(0, ctk.END)
        self.pixel_width.insert(0, str(self._pixel_width))
        self.update_pixel_width()

    def update_shape_height(self):
        # When changing the image array shape (ie resolution)
        try:
            self._shape_height = int(self.shape_height.get())
        except:
            self.shape_height.delete(0, ctk.END)
            self.shape_height.insert(0, str(self._shape_height))
            return

        # adjust pixel height
        self._pixel_height = self._frame_height / self._shape_height
        self.pixel_height.delete(0, ctk.END)
        self.pixel_height.insert(0, str(self._pixel_height))
        self.update_pixel_height()

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

        self.update_array_shape()
        self._timing_indicator.update(self.generate_spec())

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

        self.update_array_shape()
        self._timing_indicator.update(self.generate_spec())

    def update_fill_fraction(self):
        new_ff = float(self.fill_fraction.get())
        if not (0 < new_ff <= 1):
            # revert
            self.fill_fraction.delete(0, ctk.END)
            self.fill_fraction.insert(0, str(self._fill_fraction))
            return
        self._fill_fraction = new_ff
        self.fill_fraction.delete(0, ctk.END)
        self.fill_fraction.insert(0, str(self._fill_fraction))

        self._timing_indicator.update(self.generate_spec())

    def update_frames_per_acquisition(self):
        self._timing_indicator.update(self.generate_spec())

    def update_array_shape(self):
        self._shape_width = round(self._frame_width / self._pixel_width)
        self._shape_height = round(self._frame_height / self._pixel_height)
        self.shape_width.delete(0, ctk.END)
        self.shape_width.insert(0, str(self._shape_width))
        self.shape_height.delete(0, ctk.END)
        self.shape_height.insert(0, str(self._shape_height))
    
    def generate_spec(self) -> FrameAcquisitionSpec:
        return FrameAcquisitionSpec(
            bidirectional_scanning=(self.directions_var.get() == "Bidirectional"),
            line_width=self._frame_width,
            frame_height=self._frame_height,
            pixel_time=self._pixel_time,
            pixel_size=self._pixel_width,
            pixel_height=self._pixel_height,
            fill_fraction = self._fill_fraction,
            buffers_per_acquisition=self._frames_per_acquisition,
            buffers_allocated=4, # TODO not hardcode
            digitizer_profile = "default",
            flyback_periods=32 # TODO update this
        )
    

class TimingIndicator(ctk.CTkFrame):
    def __init__(self, parent, hardware: Hardware):
        super().__init__(parent)
        self._hw = hardware

        timing_label = ctk.CTkLabel(self, text="Timing", font=ctk.CTkFont(size=14, weight='bold'))
        timing_label.grid(row=0, columnspan=2, padx=10, sticky="w")

        line_rate_label = ctk.CTkLabel(self, text="Line Rate:")
        line_rate_label.grid(row=1, column=0, padx=5, sticky="e")

        self.line_rate = ctk.CTkLabel(self, text="")
        self.line_rate.grid(row=1, column=1, padx=5, sticky="w")

        line_rate_label = ctk.CTkLabel(self, text="Frame Rate:")
        line_rate_label.grid(row=2, column=0, padx=5, sticky="e")

        self.frame_rate = ctk.CTkLabel(self, text="")
        self.frame_rate.grid(row=2, column=1, padx=5, sticky="w")

    def update(self, spec: FrameAcquisitionSpec):
        """Receive a FrameAcquisitionSpec and update accordingly"""
        if spec.pixel_time:
            fast_period_time = spec.pixel_time * round(spec.pixels_per_line / spec.fill_fraction)
            line_rate = units.Frequency(1 / fast_period_time)
            self.line_rate.configure(
                text=str(line_rate)
            )
            self.frame_rate.configure(
                text=str(line_rate / spec.lines_per_frame)
            )
        
        else:
            if spec.bidirectional_scanning:
                line_rate = 2 * self._hw.fast_raster_scanner.frequency
            else:
                line_rate = self._hw.fast_raster_scanner.frequency

            self.line_rate.configure(text=str(line_rate))
            self.frame_rate.configure(text=str(line_rate/spec.lines_per_frame))


