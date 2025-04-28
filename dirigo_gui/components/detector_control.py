import customtkinter as ctk

from dirigo import units
from dirigo.hw_interfaces.detector import Detector, DetectorSet



class DetectorFrame(ctk.CTkFrame):
    """
    Encapsulates detector properties:
        - enable/disable
        - gain

    """
    def __init__(self, parent, detector: Detector):
        super().__init__(parent, fg_color="transparent")

        if not isinstance(detector, Detector):
            raise ValueError("DetectorFrame must be initialized with a Detector hardware object")
        self._detector = detector

        # Enable/Disable Checkbox
        self.enabled_var = ctk.BooleanVar(value=self._detector.enabled)
        self.enable_checkbox = ctk.CTkCheckBox(
            self, 
            text=f"Detector {self._detector.index + 1}",
            variable=self.enabled_var,
            command=self.update_enabled
        )
        self.enable_checkbox.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        try:
            # Gain slider with Input Box
            slider_frame = ctk.CTkFrame(self, fg_color="transparent")
            
            min_slider_label = ctk.CTkLabel(slider_frame, text="Gain:")
            min_slider_label.grid(row=0, column=0, padx=5)
            self.entry = ctk.CTkEntry(slider_frame, width=56)
            self.entry.insert(0, f"{self._detector.gain}")
            self.entry.grid(row=0, column=2, padx=5, pady=2)

            self.slider = ctk.CTkSlider(
                slider_frame, 
                from_=self._detector.gain_range.min, 
                to=self._detector.gain_range.max, 
                orientation="horizontal", 
                width=150,
                command=lambda value: self.update_entry(value)
            )
            self.slider.set(self._detector.gain)  
            self.slider.grid(row=0, column=1, padx=5, sticky="ew")

            self.entry.bind(
                "<Return>", 
                lambda event: self.update_slider()
            )
            self.entry.bind(
                "<FocusOut>",
                lambda event: self.update_slider()
            )

            slider_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")

        except NotImplementedError:
            # Gain is not adjustable
            self.entry = None
            self.slider = None

    def update_enabled(self):
        self._detector.enabled = self.enabled_var.get()

    def update_entry(self, value):
        """Update the gain entry box and display_min property."""
        if isinstance(self._detector.gain_range, units.VoltageRange):
            self.entry.delete(0, ctk.END)
            self.entry.insert(0, str(units.Voltage(value)))
            self._detector.gain = units.Voltage(value)
        else:
            self.entry.delete(0, ctk.END)
            self.entry.insert(0, str(int(value)))
            self._detector.gain = int(value)

    def update_slider(self):
        """Update the slider when the entry box value changes."""
        try:
            value = self.clamp_value(self.entry.get())
            self.slider.set(value)
            self.entry.delete(0, ctk.END)
            self.entry.insert(0, str(value))  # Update entry with clamped value
            self._detector.gain = int(value) # Handle NotImplementedError?
        except ValueError:
            # If invalid input, restore the slider's current value
            self.entry.delete(0, ctk.END)
            self.entry.insert(0, str(int(self.slider.get())))

    def clamp_value(self, value) -> int :
        value = int(value)
        if value < self._detector.gain_range.min:  # Clamp to minimum
            value = self._detector.gain_range.min
        elif value > self._detector.gain_range.max:  # Clamp to maximum
            value = self._detector.gain_range.max
        return value




class DetectorSetControl(ctk.CTkFrame):
    def __init__(self, parent, detector_set: DetectorSet):
        super().__init__(parent)

        if not isinstance(detector_set, DetectorSet):
            raise ValueError("DetectorFrame must be initialized with a Detector hardware object")
        self._detector_set = detector_set

        # Make title label
        title_label = ctk.CTkLabel(self, text="Detectors", font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(anchor="nw", pady=(10,0), padx=10)

        # Create N DetectorFrames
        self.detector_frames: list[DetectorFrame] = []
        for detector in self._detector_set:
            detector_frame = DetectorFrame(self, detector)
            detector_frame.pack(fill="x", pady=2, padx=2)
            self.detector_frames.append(detector_frame)