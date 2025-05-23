import queue
from pathlib import Path
import toml
import warnings

from platformdirs import user_config_dir
import customtkinter as ctk

from dirigo.main import Dirigo
from dirigo.sw_interfaces import Acquisition, Processor, Display

from dirigo_gui.widgets.image_display import LiveViewer
from dirigo_gui.components.detector_control import DetectorSetControl
from dirigo_gui.components.display_control import DisplayControl
from dirigo_gui.components.logger_control import LoggerControl
from dirigo_gui.components.acquisition_control import (
    AcquisitionControl, FrameSpecificationControl, TimingIndicator,
    StackSpecificationControl
)
from dirigo_gui.components.stage_control import StageControl



class LeftPanel(ctk.CTkFrame):
    def __init__(self, parent, controller: Dirigo, start_callback, stop_callback):
        super().__init__(parent, width=200, corner_radius=0)
        self._start_callback = start_callback
        self._stop_callback = stop_callback

        self.acquisition_control = AcquisitionControl(self, self._start_callback, self._stop_callback)
        
        self.timing_indicator = TimingIndicator(self, controller.hw)
        self.frame_specification = FrameSpecificationControl(self, self.timing_indicator)
        self.stack_specification = StackSpecificationControl(self, self.frame_specification)
        self.timing_indicator.update(self.frame_specification.generate_spec())

        self.stage_control = StageControl(
            self, 
            controller.hw.stages, 
            controller.hw.objective_z_scanner, 
        )

        self.acquisition_control.pack(pady=10, padx=10, fill="x")
        
        self.frame_specification.pack(pady=10, padx=10, fill="x")
        if controller.hw.objective_z_scanner:
            self.stack_specification.pack(pady=10, padx=10, fill="x")
        self.timing_indicator.pack(pady=10, padx=10, fill="x")
        if controller.hw.stages:
            self.stage_control.pack(side=ctk.BOTTOM, fill="x", padx=10, pady=5)


class RightPanel(ctk.CTkFrame):
    def __init__(self, parent, controller: Dirigo, toggle_theme_callback):
        super().__init__(parent, width=200, corner_radius=0)

        self._toggle_theme_callback = toggle_theme_callback

        if controller.hw.detectors:
            self.detector_control = DetectorSetControl(self, controller.hw.detectors)
            self.detector_control.pack(padx=10, pady=10, fill="x")
        
        self.display_control = DisplayControl(self, controller)
        self.display_control.pack(padx=10, pady=10, fill="x")

        self.logger_control = LoggerControl(self)
        self.logger_control.pack(padx=10, pady=10, fill="x")

        self.theme_switch = ctk.CTkSwitch(self, text="Color Mode: ", command=self._toggle_theme_callback)
        self.theme_switch.pack(side=ctk.BOTTOM, pady=10, padx=10, fill="x")


class ReferenceGUI(ctk.CTk):
    def __init__(self, dirigo_controller: Dirigo):
        super().__init__()

        self.dirigo = dirigo_controller

        self.acquisition: Acquisition = None
        self.processor: Processor = None
        self.display: Display = None
        self.inbox = queue.Queue() # to receive queued data from Display

        self.title("Dirigo Reference GUI")
        self._configure_ui()
        self._restore_settings()

        self.protocol("WM_DELETE_WINDOW", self.on_close_request) # custom close function

    def _configure_ui(self):
        self.left_panel = LeftPanel(
            parent=self,
            controller=self.dirigo,
            start_callback=self.start_acquisition,
            stop_callback=self.stop_acquisition,
        )
        self.acquisition_control = self.left_panel.acquisition_control # pass refs up to the parent GUI for easier access
        self.frame_specification = self.left_panel.frame_specification
        self.stack_specification = self.left_panel.stack_specification
        self.stage_control = self.left_panel.stage_control
        self.left_panel.pack(side=ctk.LEFT, fill=ctk.Y)

        self.right_panel = RightPanel(
            parent=self, 
            controller=self.dirigo,
            toggle_theme_callback=self.toggle_mode
        )
        self.display_control = self.right_panel.display_control 
        self.logger_control = self.right_panel.logger_control
        self.right_panel.pack(side=ctk.RIGHT, fill=ctk.Y)

        self.viewer = LiveViewer(
            parent=self,
            width=int(self.frame_specification.shape_width.get()), 
            height=int(self.frame_specification.shape_height.get()),
        )
        self.viewer.pack(expand=True, padx=10, pady=10)

        self.bind("<Control-equal>", lambda e: self.viewer.cycle_zoom(+1))
        self.bind("<Control-minus>", lambda e: self.viewer.cycle_zoom(-1))

    def _restore_settings(self):
        config_dir = Path(user_config_dir("Dirigo-GUI", "Dirigo"))

        try:
            with open(config_dir / "settings.toml", "r") as file:
                settings = toml.load(file)
            # Populate GUI

            if settings["window_color_mode"] == "Dark":
                self.right_panel.theme_switch.select()
            else:
                self.right_panel.theme_switch.deselect()
            ctk.set_appearance_mode(settings["window_color_mode"])

            i = 0
            while f"channel_{i}" in settings:
                channel_settings = settings[f"channel_{i}"]
                channel_frame = self.display_control.channel_frames[i]
                channel_frame.enabled = channel_settings["enabled"]
                channel_frame.color_vector_name = channel_settings["color_vector"]
                channel_frame.min = channel_settings["display_min"]
                channel_frame.max = channel_settings["display_max"]
                i += 1

            self.display_control.gamma.delete(0, ctk.END)
            self.display_control.gamma.insert(0, str(float(settings["gamma"])))

        except FileNotFoundError:
            warnings.warn("Could not find GUI settings file. Using defaults.", UserWarning)

    def start_acquisition(self, log_frames: bool = False, acq_name: str = 'raster_frame'):
        if acq_name not in {'raster_frame', 'raster_stack'}:
            raise ValueError("Unsupported Acquistion type: {acq_type}") 
        self.display_count = 0
        self.tk_image = None # resets the previous image if it exists

        # Over-ride default spec with settings from the GUI
        if acq_name == 'raster_frame':
            spec = self.frame_specification.generate_spec()
        elif acq_name == 'raster_stack':
            spec = self.stack_specification.generate_spec()
        if not log_frames:
            # in focus mode, don't save frames and run indefinitely
            spec.buffers_per_acquisition = float('inf')

        # Create workers
        self.acquisition = self.dirigo.make("acquisition", acq_name, spec=spec)
        self.processor   = self.dirigo.make("processor", acq_name, upstream=self.acquisition)
        self.display     = self.dirigo.make("display", "frame", upstream=self.processor)

        # Connect Display(Worker) to GUI LiveViewer
        self.display.add_subscriber(self.viewer)
        self.viewer.configure_size(spec.pixels_per_line, spec.lines_per_frame)

        # Link workers to GUI control elements
        self.display_control.link_display_worker(self.display)  

        if log_frames:        
            if self.logger_control.save_raw_checkbox.get():
                # To save 'raw', directly connect the Acquisition to Logger
                self.logger = self.dirigo.make("logger", "tiff", upstream=self.acquisition)
                self.logger.basename = self.logger.basename + "_raw"
                self.logger.frames_per_file = self.logger.frames_per_file
            else:
                # Save processed (e.g. resampled/dewarped) frames by connecting to Processor
                self.logger = self.dirigo.make("logger", "tiff", upstream=self.processor)

            self.logger_control.link_logger_worker(self.logger)
        else:
            self.logger = None

        self.acquisition.start()

        # Start polling for acquisition ended, trigger controls update if ended
        self.poll_acquisition_status()

    def poll_acquisition_status(self, interval_ms: int = 100):
        if not self.acquisition.is_alive():
            self.stop_acquisition() 
            # terminates the polling loop
        else:
            self.after(interval_ms, self.poll_acquisition_status, interval_ms)

    def stop_acquisition(self):
        # Send stop to all threads, wait until all complete
        self.acquisition.stop()
        self.processor.stop()
        self.display.stop()
        if self.logger:
            self.logger.stop()

        self.acquisition.join()
        self.processor.join()
        self.display.join()
        if self.logger:
            self.logger.join()
        self.acquisition_control.stopped()

    def toggle_mode(self):
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)

    def on_close_request(self):
        """
        Called when the user clicks the window 'X' button.
        """
        if self.acquisition_control.acquisition_running:
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
        if not self.acquisition_control.acquisition_running:
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
        config_dir.mkdir(parents=True, exist_ok=True)
        
        settings = dict()

        # Light/Dark mode
        mode = "Dark" if self.right_panel.theme_switch.get() else "Light"
        settings["window_color_mode"] = mode

        # Channel controls
        for channel_frame in self.display_control.channel_frames:
            channel_settings = dict()
            channel_settings["enabled"] = channel_frame.enabled
            channel_settings["color_vector"] = channel_frame.color_vector_var.get() # Cyan, Gray, etc
            channel_settings["display_min"] = channel_frame.min
            channel_settings["display_max"] = channel_frame.max
            
            settings[f"channel_{channel_frame.index}"] = channel_settings

        # Other display settings
        settings[f"gamma"] = self.display_control.gamma.get()

        with open(config_dir / "settings.toml", "w") as file:
            toml.dump(settings, file)



if __name__ == "__main__":
    dirigo = Dirigo()
    app = ReferenceGUI(dirigo)
    app.mainloop()
