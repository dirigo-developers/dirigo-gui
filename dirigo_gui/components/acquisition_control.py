from dataclasses import dataclass
import math

import customtkinter as ctk

from dirigo import units
from dirigo.components.hardware import Hardware
from dirigo.plugins.acquisitions import (
    FrameAcquisitionSpec, FrameAcquisition, StackAcquisitionSpec
)
from dirigo_gui.components.common import LabeledEntry



class AcquisitionControl(ctk.CTkFrame):
    BUTTON_WIDTH = 100
    BUTTON_HEIGHT = 34
    BUTTON_FONT_SIZE = 16

    def __init__(self, parent, start_callback, stop_callback):
        super().__init__(parent)
        
        self._start_callback = start_callback
        self._stop_callback = stop_callback
        self._preview_running = False
        self._series_running = False
        self._stack_running = False

        title = ctk.CTkLabel(self, text="Capture", font=ctk.CTkFont(size=16, weight='bold'))
        title.grid(row=0, columnspan=2, padx=5, sticky="w")

        self.preview_button = ctk.CTkButton(
            self, 
            text="PREVIEW", 
            font=ctk.CTkFont(size=self.BUTTON_FONT_SIZE, weight="bold"),
            width=self.BUTTON_WIDTH,
            height=self.BUTTON_HEIGHT,
            command=lambda: self.start('preview')
        )
        self.preview_button.grid(row=1, column=0, padx=5, pady=5)

        self.series_button = ctk.CTkButton(
            self, 
            text="SERIES",
            font=ctk.CTkFont(size=self.BUTTON_FONT_SIZE, weight="bold"),
            width=self.BUTTON_WIDTH,
            height=self.BUTTON_HEIGHT,
            command=lambda: self.start('capture')
        )
        self.series_button.grid(row=1, column=1, padx=5, pady=5)

        self.stack_button = ctk.CTkButton(
            self, 
            text="STACK",
            font=ctk.CTkFont(size=self.BUTTON_FONT_SIZE, weight="bold"),
            width=self.BUTTON_WIDTH,
            height=self.BUTTON_HEIGHT,
            command=lambda: self.start('stack')
        )
        self.stack_button.grid(row=2, column=0, padx=5, pady=5)

        self.calibrate_button = ctk.CTkButton(
            self, 
            text="CALIB...",
            font=ctk.CTkFont(size=self.BUTTON_FONT_SIZE, weight="bold"),
            width=self.BUTTON_WIDTH,
            height=self.BUTTON_HEIGHT,
            command=lambda: self.start('calibrate')
        )
        self.calibrate_button.grid(row=2, column=1, padx=5, pady=5)


    def start(self, type: str):
        if type == 'preview':
            self._preview_running = not self._preview_running

            # enable/disable capture, stack
            self.series_button.configure(
                state=ctk.DISABLED if self._preview_running else ctk.NORMAL
            )
            self.stack_button.configure(
                state=ctk.DISABLED if self._preview_running else ctk.NORMAL
            )

            if self._preview_running:
                self.preview_button.configure(text="STOP")
                self._start_callback(log_frames=False)
            else:
                self._stop_callback()

        elif type == 'capture':
            self._series_running = not self._series_running

            # enable/disable preview, stack
            self.preview_button.configure(
                state=ctk.DISABLED if self._series_running else ctk.NORMAL
            )
            self.stack_button.configure(
                state=ctk.DISABLED if self._series_running else ctk.NORMAL
            )

            if self._series_running:
                self.series_button.configure(text="ABORT")
                self._start_callback(log_frames=True)
            else:
                self._stop_callback()

        elif type == 'stack':
            self._stack_running = not self._stack_running

            # enable/disable preview, capture
            self.preview_button.configure(
                state=ctk.DISABLED if self._stack_running else ctk.NORMAL
            )
            self.series_button.configure(
                state=ctk.DISABLED if self._stack_running else ctk.NORMAL
            )

            if self._stack_running:
                self.stack_button.configure(text="ABORT")
                self._start_callback(acq_type="raster_stack", log_frames=True)
            else:
                self._stop_callback()

    def stopped(self):
        """Reset internal flags and button states"""
        self._preview_running = False
        self._series_running = False
        self._stack_running = False

        self.preview_button.configure(state=ctk.NORMAL, text="PREVIEW")
        self.series_button.configure(state=ctk.NORMAL, text="SERIES")
        self.stack_button.configure(state=ctk.NORMAL, text="STACK")

    @property  
    def acquisition_running(self) -> bool:
        if self._preview_running or self._series_running or self._stack_running:
            return True 
        else:
            return False


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

        # Title
        title = ctk.CTkLabel(self, text="Frame Specification", font=ctk.CTkFont(size=16, weight='bold'), anchor="w")
        title.pack(padx=5, pady=5, fill="x")

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
        self.directions.pack(padx=5, pady=2)

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
        frames_per_acq_label = ctk.CTkLabel(settings_grid_frame, text="Frames/Series:", font=font)
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

        # flyback periods - TODO

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
        new_frames = int(self.frames_per_acquisition.get())
        if new_frames <= 0:
            # revert
            self.frames_per_acquisition.delete(0, ctk.END)
            self.frames_per_acquisition.insert(0, str(self._frames_per_acquisition))
            return
        self._frames_per_acquisition = new_frames
        self.frames_per_acquisition.delete(0, ctk.END)
        self.frames_per_acquisition.insert(0, str(self._frames_per_acquisition))

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
            bidirectional_scanning  = (self.directions_var.get() == "Bidirectional"),
            line_width              = self._frame_width,
            frame_height            = self._frame_height,
            pixel_time              = self._pixel_time,
            pixel_size              = self._pixel_width,
            pixel_height            = self._pixel_height,
            fill_fraction           = self._fill_fraction,
            buffers_per_acquisition = self._frames_per_acquisition,
            flyback_periods         = 32 # TODO update this
        )


@dataclass
class _StackSpecModel:
    lower: units.Position
    upper: units.Position
    spacing: units.Position
    depths: int

    @property
    def range(self) -> units.Position:
        return self.upper - self.lower

    def recompute_depths(self) -> None:
        """Depths = ⌊range / spacing⌋ + 1 (inclusive endpoints)."""
        self.depths = math.floor(self.range / self.spacing) + 1

    def recompute_spacing(self) -> None:
        """Spacing = range / (depths - 1); guard division‑by‑zero."""
        if self.depths > 1:
            self.spacing = self.range / (self.depths - 1)


class StackSpecificationControl(ctk.CTkFrame):

    _FIELD_INFO = (
        # label text   attribute name in the model
        ("Lower:",  "lower"),
        ("Upper:",  "upper"),
        ("Spacing:","spacing"),
        ("Depths:", "depths"),
    )

    def __init__(self, parent, frame_spec_control: FrameSpecificationControl):
        super().__init__(parent)
        self._frame_spec_control = frame_spec_control

        # Initialize model (TODO, grab defaults from spec toml)
        self._model = _StackSpecModel(
            lower   = units.Position("-200 um"),
            upper   = units.Position("100 um"),
            spacing = units.Position("25 um"),
            depths  = 1, # will be overwritten 
        )
        self._model.recompute_depths()

        # Initialize GUI fields
        COLS = 2
        ctk.CTkLabel(
            self,
            text="Stack Specification",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, columnspan=4, sticky="w", padx=10, pady=(0, 4))

        self._widgets: dict[str, LabeledEntry] = {}
        for i, (text, attr) in enumerate(self._FIELD_INFO):
            widget = LabeledEntry(
                self, text,
                default=str(getattr(self._model, attr)),
                on_validate=lambda val, field=attr: self._on_field_change(field, val)
            )

            row, col = divmod(i, COLS)  # arange in 2X2 grid
            widget.grid(row=row+1, column=col, padx=4, pady=3, sticky="e")
            self._widgets[attr] = widget

    def _on_field_change(self, field: str, raw: str) -> None:
        """
        Parse & validate `raw`, update the model, and refresh any dependent
        widgets. If parsing fails the offending widget background turns red.
        """
        widget = self._widgets[field]
        try:
            if field == "depths":
                value = int(raw)
                if value < 1:
                    raise ValueError
                setattr(self._model, field, value)
                # editing depths => recompute spacing
                self._model.recompute_spacing()
            else:                                    # lower | upper | spacing
                value = units.Position(raw)
                setattr(self._model, field, value)
                if field in ("lower", "upper"):
                    self._model.recompute_depths()
                else:                               # spacing edited
                    self._model.recompute_depths()

            widget.set_text_normal()
            self._sync()                             # push model to GUI
        except Exception:
            widget.set_text_red()       # set to red for failure

    def _sync(self) -> None:
        """Push *validated* model values out to the GUI widgets."""
        for attr in ("lower", "upper", "spacing"):
            self._widgets[attr].set(str(getattr(self._model, attr)))
        self._widgets["depths"].set(str(self._model.depths))

    @property
    def spec_model(self) -> _StackSpecModel:
        """Return a *copy* so callers can’t mutate internal state."""
        return _StackSpecModel(**vars(self._model))
    
    def generate_spec(self) -> StackAcquisitionSpec:
        f = self._frame_spec_control
        m = self._model                          # shorthand
        return StackAcquisitionSpec(
            bidirectional_scanning = (f.directions_var.get() == "Bidirectional"),
            line_width             = f._frame_width,
            frame_height           = f._frame_height,
            pixel_time             = f._pixel_time,
            pixel_size             = f._pixel_width,
            pixel_height           = f._pixel_height,
            fill_fraction          = f._fill_fraction,
            flyback_periods        = 32,         # TODO
            lower_limit            = m.lower,
            upper_limit            = m.upper,
            depth_spacing          = m.spacing,
        )
    

class TimingIndicator(ctk.CTkFrame):
    def __init__(self, parent, hardware: Hardware):
        super().__init__(parent)
        self._hw = hardware

        timing_label = ctk.CTkLabel(self, text="Timing", font=ctk.CTkFont(size=16, weight='bold'))
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


