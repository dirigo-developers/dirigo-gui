import customtkinter as ctk

from dirigo import units
from dirigo.hw_interfaces.beam_attenuator import BeamAttenuator


class PowerFrame(ctk.CTkFrame):
    def __init__(self, parent, beam_attenuator: BeamAttenuator):
        super().__init__(parent, fg_color="transparent")

        if not isinstance(beam_attenuator, BeamAttenuator):
            raise ValueError("PowerFrame must be initialized with a BeamAttenuator object")
        self._beam_attenuator = beam_attenuator

        # Make laser power slider
        slider_frame = ctk.CTkFrame(self, fg_color = "transparent")

        slider_label = ctk.CTkLabel(slider_frame, text="Power:")
        slider_label.grid(row=0, column=0, padx=5)
        self.entry = ctk.CTkEntry(slider_frame, width=56)
        self.entry.insert(0, f"{round(100*self._beam_attenuator.fraction)}")
        self.entry.grid(row=0, column=2, padx=5, pady=2)

        self.slider = ctk.CTkSlider(
            slider_frame, 
            from_=round(100*self._beam_attenuator.fraction_limits.min), 
            to=round(100*self._beam_attenuator.fraction_limits.max), 
            orientation="horizontal", 
            width=150,
            command=lambda value: self.update_entry(value)
        )
        self.slider.set(round(100*self._beam_attenuator.fraction))
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

    def update_entry(self, value):
        if self.entry is None:
            raise RuntimeError("Entry not initialized")

        self.entry.delete(0, ctk.END)
        self.entry.insert(0, str(value))
        self._beam_attenuator.set_fraction(value/100.0)

    def update_slider(self):
        """Update the slider when the entry box value changes."""
        if self.slider is None or self.entry is None:
            raise RuntimeError("Slider and/or entry not initialized")
        
        value = self.clamp_value(self.entry.get())
        self.slider.set(value)
        self.entry.delete(0, ctk.END)
        self.entry.insert(0, str(value))  # Update entry with clamped value
        self._beam_attenuator.set_fraction(value/100.0)

    def clamp_value(self, value) -> int :
        value = int(value)
        if value < 100*self._beam_attenuator.fraction_limits.min:  # Clamp to minimum
            value = round(100*self._beam_attenuator.fraction_limits.min)
        elif value > 100*self._beam_attenuator.fraction_limits.max:  # Clamp to maximum
            value = round(100*self._beam_attenuator.fraction_limits.max)
        return value

class LaserControl(ctk.CTkFrame):
    def __init__(self, parent, beam_attenuator: BeamAttenuator):
        super().__init__(parent)

        if not isinstance(beam_attenuator, BeamAttenuator):
            raise ValueError("LaserControl must be initialized with a BeamAttenuator hardware object")
        self._beam_attenuator = beam_attenuator

        # Make title label
        title_label = ctk.CTkLabel(self, text="Laser", font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(anchor="nw", pady=(10,0), padx=10)

        # Create PowerFrame
        power_frame = PowerFrame(self, self._beam_attenuator)
        power_frame.pack(fill="x", pady=2, padx=2)
