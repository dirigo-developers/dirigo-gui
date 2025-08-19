from typing import Optional

import customtkinter as ctk

from dirigo.main import Dirigo
from dirigo.sw_interfaces import Display
from dirigo.sw_interfaces.display import get_available_color_vector_names
from dirigo.plugins.processors import RollingAverageProcessor
from dirigo.plugins.displays import DisplayChannel, FrameDisplay, Gamma


class ChannelFrame(ctk.CTkFrame):
    """
    Encapsulates channel display properties:
        - display on/off
        - LUT name
        - min display value
        - max display value

    """
    def __init__(self, parent, dirigo: Dirigo, channel_index: int):
        """Constructs a frame with channel display properties."""
        super().__init__(parent, corner_radius=10, fg_color="transparent")
        self.index = channel_index
        self._display_channel: Optional[DisplayChannel] = None # A display channel object is linked to this later

        # Slider limits -- set up a dummy acquisition/processor to return data range min/max 
        acq = dirigo.make("acquisition", "raster_frame")
        proc = dirigo.make("processor", "raster_frame", upstream=acq, autostart=False)
        self.slider_min = proc.data_range.min
        self.slider_max = proc.data_range.max

        # Enable/Disable Checkbox
        self.enabled_var = ctk.BooleanVar(value=True)
        self.enable_checkbox = ctk.CTkCheckBox(
            self, 
            text=f"Channel {self.index + 1}",
            variable=self.enabled_var,
            command=self.update_enabled
        )
        self.enable_checkbox.grid(row=0, column=0, padx=5, pady=(10,0), sticky="w")

        # LUT Dropdown
        self.color_vector_var = ctk.StringVar(value="Blue")  # Default value
        self.color_vector_menu = ctk.CTkOptionMenu(
            self,
            values=get_available_color_vector_names(), 
            variable=self.color_vector_var,
            command=self.update_color_vector
        )
        self.color_vector_menu.grid(row=0, column=1, padx=5, pady=(10,0), sticky="e")

        # Sliders Frame (to stack sliders vertically)
        sliders_frame = ctk.CTkFrame(self, fg_color="transparent")
        sliders_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")

        # Min Slider with Input Box
        min_slider_label = ctk.CTkLabel(sliders_frame, text="Min:")
        min_slider_label.grid(row=0, column=0, padx=5)
        self.min_entry = ctk.CTkEntry(sliders_frame, width=50)
        self.min_entry.insert(0, f"{self.slider_min}")
        self.min_entry.grid(row=0, column=2, padx=5, pady=2)

        self.min_slider = ctk.CTkSlider(
            sliders_frame, 
            from_=self.slider_min, 
            to=self.slider_max, 
            orientation="horizontal", 
            width=150,
            command=lambda value: self.update_min_entry(value)
        )
        self.min_slider.set(self.slider_min)  # Default min value
        self.min_slider.grid(row=0, column=1, padx=5, sticky="ew")

        self.min_entry.bind(
            "<Return>", 
            lambda event: self.update_min_slider()
        )
        self.min_entry.bind(
            "<FocusOut>",
            lambda event: self.update_min_slider()
        )

        # Max Slider with Input Box
        max_slider_label = ctk.CTkLabel(sliders_frame, text="Max:")
        max_slider_label.grid(row=1, column=0, padx=5)
        self.max_entry = ctk.CTkEntry(sliders_frame, width=50)
        self.max_entry.insert(0, f"{self.slider_max}")
        self.max_entry.grid(row=1, column=2, padx=5, pady=2)

        self.max_slider = ctk.CTkSlider(
            sliders_frame, 
            from_=self.slider_min, 
            to=self.slider_max, 
            orientation="horizontal", 
            width=150,
            command=lambda value: self.update_max_entry(value)
        )
        self.max_slider.set(self.slider_max)  # Default max value
        self.max_slider.grid(row=1, column=1, padx=5, sticky="ew")

        self.max_entry.bind(
            "<Return>", 
            lambda event: self.update_max_slider()
        )
        self.max_entry.bind(
            "<FocusOut>",
            lambda event: self.update_max_slider()
        )

    def update_enabled(self):
        if self._display_channel:
            self._display_channel.enabled = self.enabled_var.get()

    def update_color_vector(self, new_vector: str):
        if self._display_channel:
            self._display_channel.color_vector_name = new_vector

    def update_min_entry(self, value):
        """Update the min entry box and display_min property."""
        self.min_entry.delete(0, ctk.END)
        self.min_entry.insert(0, str(int(value)))
        if self._display_channel: # only updates if a display channel has been associated with this frame
            self._display_channel.display_min = int(value)

    def update_max_entry(self, value):
        """Update the max entry box and display_min property."""
        self.max_entry.delete(0, ctk.END)
        self.max_entry.insert(0, str(int(value)))
        if self._display_channel: # only updates if a display channel has been associated with this frame
            self._display_channel.display_max = int(value)

    def update_min_slider(self):
        """Update the min slider when the entry box value changes."""
        try:
            value = self.clamp_value(self.min_entry.get())
            self.min_slider.set(value)
            self.min_entry.delete(0, ctk.END)
            self.min_entry.insert(0, str(value))  # Update entry with clamped value
            if self._display_channel:
                self._display_channel.display_min = value
        except ValueError:
            # If invalid input, restore the slider's current value
            self.min_entry.delete(0, ctk.END)
            self.min_entry.insert(0, str(int(self.min_slider.get())))

    def update_max_slider(self):
        """Update the max slider when the entry box value changes."""
        try:
            value = self.clamp_value(self.max_entry.get())
            self.max_slider.set(value)
            self.max_entry.delete(0, ctk.END)
            self.max_entry.insert(0, str(value))  # Update entry with clamped value
            if self._display_channel:
                self._display_channel.display_max = value
        except ValueError:
            # If invalid input, restore the slider's current value
            self.max_entry.delete(0, ctk.END)
            self.max_entry.insert(0, str(int(self.max_slider.get())))

    def clamp_value(self, value) -> int :
        value = int(value)
        if value < self.slider_min:  # Clamp to minimum
            value = self.slider_min
        elif value > self.slider_max:  # Clamp to maximum
            value = self.slider_max
        return value
    
    @property
    def enabled(self) -> bool:
        return bool(self.enabled_var.get())
    
    @enabled.setter
    def enabled(self, new_state: bool):
        if not isinstance(new_state, bool):
            raise ValueError("`enabled` must be set with a boolean value")
        self.enabled_var.set(new_state)
    
    @property
    def color_vector_name(self) -> 'str':
        return self.color_vector_var.get()
    
    @color_vector_name.setter
    def color_vector_name(self, new_color_vector_name: str):
        if not isinstance(new_color_vector_name, str):
            raise ValueError("`color_vector_name` must be set with a string value")
        if new_color_vector_name.lower() not in get_available_color_vector_names():
            raise ValueError(f"Invalid ColorVector name: {new_color_vector_name}")
        self.color_vector_var.set(new_color_vector_name)

    @property
    def min(self) -> int:
        return int(self.min_entry.get())
    
    @min.setter
    def min(self, new_value: int):
        new_value = self.clamp_value(new_value)
        self.min_slider.set(new_value)
        self.min_entry.delete(0, ctk.END)
        self.min_entry.insert(0, str(new_value))
    
    @property
    def max(self) -> int:
        return int(self.max_entry.get())
    
    @max.setter
    def max(self, new_value: int):
        new_value = self.clamp_value(new_value)
        self.max_slider.set(new_value)
        self.max_entry.delete(0, ctk.END)
        self.max_entry.insert(0, str(new_value))
    
    def set_widgets_state(self, new_state):
        self.enable_checkbox.configure(state=new_state)
        self.color_vector_menu.configure(state=new_state)
        self.min_slider.configure(state=new_state)
        self.max_slider.configure(state=new_state)
        self.min_entry.configure(state=new_state)
        self.max_entry.configure(state=new_state)


class DisplayControl(ctk.CTkFrame): 
    def __init__(self, parent, dirigo:Dirigo, title: str = "Display"):
        """Set up panel with controls for N channels"""
        #super().__init__(parent, fg_color="transparent")
        super().__init__(parent)
        self.dirigo = dirigo
        self._averager: Optional[RollingAverageProcessor] = None
        self._display_worker: Optional[FrameDisplay] = None

        # Make title label
        title_label = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(anchor="nw", pady=(10,0), padx=10)

        # Make N ChannelFrames
        self.channel_frames: list[ChannelFrame] = []
        for i in range(self.dirigo.hw.nchannels_present):
            channel_frame = ChannelFrame(self, self.dirigo, i)
            channel_frame.pack(fill="y", pady=2, padx=2, anchor="n")
            self.channel_frames.append(channel_frame)  # Save reference to each ChannelFrame

        # Make grid for other settings
        # Misc settings put in to orderly grid
        settings_grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        r = 0

        # Display gamma
        gamma_label = ctk.CTkLabel(settings_grid_frame, text="Display Gamma:", 
                                   font=ctk.CTkFont(size=14, weight="bold"))
        gamma_label.grid(row=r, column=0, padx=5, sticky="e")
        self.gamma = ctk.CTkEntry(settings_grid_frame, width=70)
        self.gamma.grid(row=r, pady=3, column=1, sticky='w')
        self.gamma.insert(0, str(1.0)) # This will be overwritten with saved setting, if available
        self.gamma.bind("<Return>", lambda e: self.update_gamma())
        self.gamma.bind("<FocusOut>", lambda e: self.update_gamma())
        r += 1

        average_label = ctk.CTkLabel(settings_grid_frame, text="Frames Averaged:", 
                                     font=ctk.CTkFont(size=14, weight="bold"))
        average_label.grid(row=r, column=0, padx=5, sticky="e")
        self.average = ctk.CTkEntry(settings_grid_frame, width=70)
        self.average.grid(row=r, pady=3, column=1, sticky='w')
        self.average.insert(0, str(1)) 
        self.average.bind("<Return>", lambda e: self.update_average())
        self.average.bind("<FocusOut>", lambda e: self.update_average())
        r += 1

        settings_grid_frame.pack(fill="x", anchor='w')

    def update_gamma(self):
        if self._display_worker:
            try:
                new_gamma = float(self.gamma.get())
                self._display_worker._transfer_function = Gamma(gamma=new_gamma)
                self._display_worker._update_tf_lut()
            except:
                pass
            self.gamma.delete(0, ctk.END)
            valid_gamma = self._display_worker._transfer_function.gamma # type: ignore
            self.gamma.insert(0, str(valid_gamma))
            self._display_worker.update_display()
        else:
            # If no display worker has been linked, we need to validate the 
            # value here (rather than let worker do it)
            try:
                new_gamma = float(self.gamma.get())
                if not (0 < new_gamma <= 10):
                    raise ValueError
                self.gamma.delete(0, ctk.END)
                self.gamma.insert(0, str(new_gamma))
            except:
                self.gamma.delete(0, ctk.END)
                self.gamma.insert(0, str(1.0))

    def update_average(self):
        if self._averager:
            try:
                value = int(self.average.get())
                if not (0 < value < 100):
                    raise ValueError
                self._averager.n_frame_average = value
            except:
                pass
            self.average.delete(0, ctk.END)
            self.average.insert(0, str(self._averager.n_frame_average))
        else:
            # If no averager worker has been linked, we need to validate the value here
            try:
                value = int(self.average.get())
                if not (0 < value < 100):
                    raise ValueError
                self.average.delete(0, ctk.END)
                self.average.insert(0, str(value))
            except:
                self.average.delete(0, ctk.END)
                self.average.insert(0, str(1))
    
    def link_averager_worker(self, averager: RollingAverageProcessor):
        self._averager = averager
        self._averager.n_frame_average = int(self.average.get())

    def link_display_worker(self, display: FrameDisplay):
        """Links GUI properties to the dynamically generated Display worker."""
        self._display_worker = display
        
        display_index = 0 # Display and Digitizer have slightly different indices--Display skips channels that are not enabled
        for channel in self.dirigo.hw.digitizer.channels:
            # Iterate over available digitizer channels
            
            channel_frame = self.channel_frames[channel.index] # This is an object maintained by the GUI

            if channel.enabled:
                display_channel = display.display_channels[display_index] # This is an object under the Display worker

                # if digitizer channel is enabled (because the acquisition configured it to be enabled)
                # then we want to associate display_channel (used by Display worker) with ChannelFrame
                channel_frame._display_channel = display_channel
                    
                # Make sure widgets are enabled
                channel_frame.set_widgets_state(ctk.NORMAL)

                # Transfer GUI properties -> Display worker properties
                display_channel.enabled = channel_frame.enabled_var.get()
                display_channel.color_vector_name = channel_frame.color_vector_var.get().lower()
                display_channel.display_min = channel_frame.min 
                display_channel.display_max = channel_frame.max

                display_index += 1
            else:
                # If the channel is not enabled on the digitizer, disable channel frame objects
                channel_frame.set_widgets_state(ctk.DISABLED)

                # Uncheck checkbox to show that channel is disabled
                channel_frame.enabled_var.set(False)

                channel_frame._display_channel = None

        # Pass misc Display settings to Display worker
        display.gamma = float(self.gamma.get())
               
