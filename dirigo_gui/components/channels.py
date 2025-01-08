import customtkinter as ctk

from dirigo.main import Dirigo
from dirigo.sw_interfaces import Display
from dirigo.sw_interfaces.display import ColorVector
from dirigo.plugins.displays import DisplayChannel


class SingleChannelFrame(ctk.CTkFrame):
    """
    Encapsulates channel display properties:
        - display on/off
        - LUT name
        - min display value
        - max display value

    """
    def __init__(self, parent, dirigo: Dirigo, channel_index: int):
        """Constructs a frame with channel display properties."""
        super().__init__(parent, corner_radius=10)
        self._display_channel: DisplayChannel = None

        # Slider limits
        self.slider_min = 0
        self.slider_max = 2**16 - 1

        # Enable/Disable Checkbox
        self.enabled_var = ctk.BooleanVar(value=True)
        self.enable_checkbox = ctk.CTkCheckBox(
            self, 
            text=f"Channel {channel_index + 1}",
            variable=self.enabled_var,
            command=self.update_enabled
        )
        self.enable_checkbox.grid(row=0, column=0, padx=5, pady=(10,0), sticky="w")

        # LUT Dropdown
        self.color_vector_var = ctk.StringVar(value="Blue")  # Default value
        self.color_vector_menu = ctk.CTkOptionMenu(
            self, 
            values=ColorVector.get_color_names(), 
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
            lambda event: self.update_max_slider(self.max_entry, self.max_slider)
        )
        self.max_entry.bind(
            "<FocusOut>",
            lambda event: self.update_max_slider(self.max_entry, self.max_slider)
        )

    def update_enabled(self):
        if self._display_channel:
            self._display_channel.enabled = self.enabled_var.get()

    def update_color_vector(self, new_lut: str):
        if self._display_channel:
            self._display_channel.color_vector = ColorVector[new_lut.upper()]

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
            value = int(self.min_entry.get())
            if value < self.slider_min:  # Clamp to minimum
                value = self.slider_min
            elif value > self.slider_max:  # Clamp to maximum
                value = self.slider_max
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
            value = int(self.max_entry.get())
            if value < self.slider_min:  # Clamp to minimum
                value = self.slider_min
            elif value > self.slider_max:  # Clamp to maximum
                value = self.slider_max
            self.max_slider.set(value)
            self.max_entry.delete(0, ctk.END)
            self.max_entry.insert(0, str(value))  # Update entry with clamped value
            if self._display_channel:
                self._display_channel.display_max = value
        except ValueError:
            # If invalid input, restore the slider's current value
            self.max_entry.delete(0, ctk.END)
            self.max_entry.insert(0, str(int(self.max_slider.get())))

    @property
    def min(self) -> int:
        return int(self.min_entry.get())
    
    @property
    def max(self) -> int:
        return int(self.max_entry.get())
    
    def set_widgets_state(self, new_state):
        self.enable_checkbox.configure(state=new_state)
        self.color_vector_menu.configure(state=new_state)
        self.min_slider.configure(state=new_state)
        self.max_slider.configure(state=new_state)
        self.min_entry.configure(state=new_state)
        self.max_entry.configure(state=new_state)


class ChannelsControl(ctk.CTkFrame):
    def __init__(self, parent, dirigo:Dirigo, title: str = "Channel Control"):
        """Set up panel with controls for N channels"""
        super().__init__(parent, fg_color="transparent")
        self.dirigo = dirigo

        # Make title label
        font = ctk.CTkFont(size=18, weight="bold")
        title_label = ctk.CTkLabel(self, text=title, font=font)
        title_label.pack(anchor="n", pady=(10,0))

        # Make N SingleChannelFrames
        self.channel_frames: list[SingleChannelFrame] = []
        for i in range(self.dirigo.hw.nchannels):
            channel_frame = SingleChannelFrame(self, self.dirigo, i)
            channel_frame.pack(fill="y", pady=5, padx=10, anchor="n")
            self.channel_frames.append(channel_frame)  # Save reference to each ChannelFrame

    def link_display_worker(self, display: Display):
        """Links GUI properties to the dynamically generated Display worker."""
        
        display_index = 0 # Display and Digitizer have slightly different indices--Display skips channels that are not enabled
        for channel in self.dirigo.hw.digitizer.channels:
            # Iterate over available digitizer channels
            if channel.enabled:
                display_channel = display.display_channels[display_index] # This is an object under the Display worker
                channel_frame = self.channel_frames[channel.index] # This is an object maintained by the GUI

                # if digitizer channel is enabled (because the acquisition configured it to be enabled)
                # then we want to associate display_channel (used by Display worker) with ChannelFrame
                channel_frame._display_channel = display_channel
                    
                # Make sure widgets are enabled
                channel_frame.set_widgets_state(ctk.NORMAL)

                # Transfer GUI properties -> Display worker properties
                display_channel.enabled = channel_frame.enabled_var.get()
                display_channel.color_vector = \
                    ColorVector[channel_frame.color_vector_var.get().upper()]
                display_channel.display_min = channel_frame.min 
                display_channel.display_max = channel_frame.max

                display_index += 1
            else:
                # If the channel is not enabled on the digitizer, disable channel frame objects
                self.channel_frames[channel.index].set_widgets_state(ctk.DISABLED)

                # Uncheck checkbox to show that channel is disabled
                self.channel_frames[channel.index].enabled_var.set(False)

                self.channel_frames[channel.index]._display_channel = None
               
