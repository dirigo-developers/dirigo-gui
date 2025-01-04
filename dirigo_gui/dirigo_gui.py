import queue
import time

import customtkinter as ctk
from PIL import Image, ImageTk
import numpy as np

from dirigo.main import Dirigo



class ButtonPanel(ctk.CTkFrame):
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


class ReferenceGUI(ctk.CTk):
    def __init__(self, dirigo_controller: Dirigo):
        super().__init__()
        self.controller = dirigo_controller
        self.display = None
        self.queue = queue.Queue()

        self.title("Dirigo Reference GUI")
        self.geometry("800x600")
        self.acquisition_running = False
        self._configure_ui()

        self.poll_queue()

    def _configure_ui(self):
        self.button_panel = ButtonPanel(
            self,
            acquisition_options=self.controller.acquisition_types,
            start_callback=self.toggle_acquisition,
            toggle_theme_callback=self.toggle_mode
        )
        self.button_panel.pack(side="left", fill="y")

        self.display_canvas = ctk.CTkCanvas(self, bg="black", highlightthickness=0)
        self.display_canvas.pack(side="right", expand=True, fill="both", padx=10, pady=10)
        self.canvas_image = None  # Store reference to avoid garbage collection

    def toggle_acquisition(self):
        self.acquisition_running = not self.acquisition_running
        text = "Stop Acquisition" if self.acquisition_running else "Start Acquisition"
        self.button_panel.acquisition_button.configure(text=text)

        if self.acquisition_running:
            self.start_acquisition()
        else:
            self.stop_acquisition()

    def start_acquisition(self):
        self.display_count = 0
        self.acquisition = self.controller.acquisition_factory('frame')
        self.processor = self.controller.processor_factory(self.acquisition)
        self.display = self.controller.display_factory(self.processor)

        # Connect threads 
        self.acquisition.publisher.subscribe(self.processor.inbox)
        self.processor.publisher.subscribe(self.display.inbox)
        self.display.publisher.subscribe(self.queue)

        self.display.start()
        self.processor.start()
        self.acquisition.start()

    def stop_acquisition(self):
        self.acquisition.stop()
        self.acquisition_running = False
        text = "Start Acquisition"
        self.button_panel.acquisition_button.configure(text=text)

    def poll_queue(self):
        try:
            if self.display:
                image = self.queue.get(timeout=0.01)

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

        print(f"Image {self.display_count} | Canvas update: {1000*(t3-t2):.1f}ms | PhotoImage: {1000*(t2-t1):.1f}ms | PIL: {1000*(t1-t0):.1f}ms")

    def toggle_mode(self):
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)


if __name__ == "__main__":
    diri = Dirigo()
    app = ReferenceGUI(diri)
    app.mainloop()
