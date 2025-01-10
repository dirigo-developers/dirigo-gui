import queue
import time
from pathlib import Path
import toml

from platformdirs import user_config_dir
import customtkinter as ctk
from PIL import Image, ImageTk
import numpy as np

from dirigo.main import Dirigo
from dirigo.sw_interfaces import Acquisition, Processor, Display
from dirigo_gui.components.channels import ChannelsControl



class LeftPanel(ctk.CTkFrame):
    def __init__(self, parent, acquisition_options, start_callback, toggle_theme_callback):
        super().__init__(parent, width=200, corner_radius=0)
        self.start_callback = start_callback
        self.toggle_theme_callback = toggle_theme_callback
        self._configure_ui(acquisition_options)

    def _configure_ui(self, acquisitions: set[str]):
        self.acquisition_button = ctk.CTkButton(self, text="Start Acquisition", command=self.start_callback)
        self.acquisition_button.pack(pady=10, padx=10)

        self.dummy_button_1 = ctk.CTkButton(self, text="Dummy Button 1")
        self.dummy_button_1.pack(pady=10, padx=10)

        self.dummy_button_2 = ctk.CTkButton(self, text="Dummy Button 2")
        self.dummy_button_2.pack(pady=10, padx=10)

        self.options_menu = ctk.CTkOptionMenu(
            self,
            values=list(acquisitions),
        )
        self.options_menu.pack(pady=10, padx=10)
        self.options_menu.set("Select an Option")

        self.theme_switch = ctk.CTkSwitch(self, text="Toggle Mode", command=self.toggle_theme_callback)
        self.theme_switch.pack(pady=10, padx=10)


class RightPanel(ctk.CTkFrame):
    def __init__(self, parent, dirigo: Dirigo):
        super().__init__(parent, width=200, corner_radius=0)
        
        self.channels_control = ChannelsControl(self, dirigo)
        self.channels_control.pack()

      
class ReferenceGUI(ctk.CTk):
    def __init__(self, dirigo_controller: Dirigo):
        super().__init__()
        self.dirigo = dirigo_controller

        self.acquisition: Acquisition = None
        self.processor: Processor = None
        self.display: Display = None
        self.inbox = queue.Queue() # to receive queued data from Display

        self.title("Dirigo Reference GUI")
        self.acquisition_running = False
        self._configure_ui()
        self._restore_settings()

        self.poll_queue()

        self.protocol("WM_DELETE_WINDOW", self.on_close_request) # custom close function

    def _configure_ui(self):
        # Need: peek at acqspec
        self.left_panel = LeftPanel(
            self,
            acquisition_options=self.dirigo.acquisition_types,
            start_callback=self.toggle_acquisition,
            toggle_theme_callback=self.toggle_mode
        )
        self.left_panel.pack(side=ctk.LEFT, fill=ctk.Y)

        self.right_panel = RightPanel(self, self.dirigo)
        self.channels_control = self.right_panel.channels_control # pass reference up to the parent GUI
        self.right_panel.pack(side=ctk.RIGHT, fill=ctk.Y)

        self.display_canvas = ctk.CTkCanvas(self, bg="black", highlightthickness=0)
        self.display_canvas.configure(width=1000, height=1000)
        self.display_canvas.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True, padx=10, pady=10)
        self.canvas_image = None  # Store reference to avoid garbage collection

    def _restore_settings(self):
        config_dir = Path(user_config_dir("Dirigo-GUI", "Dirigo"))

        try:
            with open(config_dir / "settings.toml", "r") as file:
                settings = toml.load(file)
            # Populate GUI

            if settings["window_color_mode"] == "Dark":
                self.left_panel.theme_switch.select()
            else:
                self.left_panel.theme_switch.deselect()
            ctk.set_appearance_mode(settings["window_color_mode"])

            i = 0
            while f"channel_{i}" in settings:
                channel_settings = settings[f"channel_{i}"]
                channel_frame = self.channels_control.channel_frames[i]
                channel_frame.enabled = channel_settings["enabled"]
                channel_frame.color_vector_name = channel_settings["color_vector"]
                channel_frame.min = channel_settings["display_min"]
                channel_frame.max = channel_settings["display_max"]
                i += 1

        except FileNotFoundError:
            raise Warning("Could not find GUI settings file. Using defaults.") 


    def toggle_acquisition(self):
        self.acquisition_running = not self.acquisition_running
        text = "Stop Acquisition" if self.acquisition_running else "Start Acquisition"
        self.left_panel.acquisition_button.configure(text=text)

        if self.acquisition_running:
            self.start_acquisition()
        else:
            self.stop_acquisition()

    def start_acquisition(self):
        self.display_count = 0
        self.acquisition = self.dirigo.acquisition_factory('frame')
        self.processor = self.dirigo.processor_factory(self.acquisition)
        self.display = self.dirigo.display_factory(self.processor)

        # Connect threads 
        self.acquisition.add_subscriber(self.processor)
        self.processor.add_subscriber(self.display)
        self.display.add_subscriber(self)

        # Link Display worker with GUI channel control elements 
        self.channels_control.link_display_worker(self.display)

        self.display.start()
        self.processor.start()
        self.acquisition.start()

    def stop_acquisition(self):
        self.acquisition.stop()
        self.acquisition_running = False
        self.left_panel.acquisition_button.configure(text="Start Acquisition")

    def poll_queue(self):
        try:
            if self.display:
                image = self.inbox.get(timeout=0.01)

                if image is None:
                    self.stop_acquisition()
                else:
                    self.update_display(image)
        except queue.Empty:
            pass
        finally:
            self.after(10, self.poll_queue)

    def update_display(self, image: np.ndarray):
        self.display_count += 1
        t0 = time.perf_counter()
        pil_img = Image.fromarray(image, mode="RGB")

        t1 = time.perf_counter()       
        if not hasattr(self, 'tk_image'):
            # Create the PhotoImage only once
            self.tk_image = ImageTk.PhotoImage(pil_img)
            self.canvas_image = self.display_canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        else:
            # Update the existing PhotoImage in-place
            self.tk_image.paste(pil_img)

        t2 = time.perf_counter()
        self.display_canvas.itemconfig(self.canvas_image, image=self.tk_image)
        t3 = time.perf_counter()

        print(f"Image {self.display_count} | Canvas update: {1000*(t3-t2):.1f}ms | PhotoImage: {1000*(t2-t1):.1f}ms | PIL: {1000*(t1-t0):.1f}ms" )

    def toggle_mode(self):
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)

    def on_close_request(self):
        """
        Called when the user clicks the window 'X' button.
        """
        if self.acquisition_running:
            # Signal the acquisition to stop
            self.stop_acquisition()

            # Start polling or waiting to check if the acquisition is truly stopped
            self.after(100, self._check_acquisition_stopped)
        else:
            # No acquisition running, so we can close immediately
            self.destroy()

    def _check_acquisition_stopped(self):
        """
        Poll the acquisition-running status or check if threads have exited.
        If the acquisition is done, destroy the GUI.
        Otherwise, keep polling until it is complete.
        """
        if not self.acquisition_running:
            # The acquisition is fully stopped now; destroy the main window
            self.destroy()
        else:
            # Still waiting for acquisition to finish, check again in 100ms
            self.after(100, self._check_acquisition_stopped)

    def destroy(self):
        # Save GUI settings
        self._save_gui_settings()

        # Close Tkinter
        return super().destroy()
    
    def _save_gui_settings(self):
        config_dir = Path(user_config_dir("Dirigo-GUI", "Dirigo"))
        settings = dict()

        # Light/Dark mode
        mode = "Dark" if self.left_panel.theme_switch.get() else "Light"
        settings["window_color_mode"] = mode

        # Channel controls
        for channel_frame in self.channels_control.channel_frames:
            channel_settings = dict()
            channel_settings["enabled"] = channel_frame.enabled
            channel_settings["color_vector"] = channel_frame.color_vector_var.get() # Cyan, Gray, etc
            channel_settings["display_min"] = channel_frame.min
            channel_settings["display_max"] = channel_frame.max
            
            settings[f"channel_{channel_frame.index}"] = channel_settings

        with open(config_dir / "settings.toml", "w") as file:
            toml.dump(settings, file)



if __name__ == "__main__":
    diri = Dirigo()
    app = ReferenceGUI(diri)
    app.mainloop()
