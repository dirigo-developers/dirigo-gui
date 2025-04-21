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
        super().__init__(parent)

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
        self.enable_checkbox.grid(row=0, column=0, padx=5, pady=(10,0), sticky="w")

    def update_enabled(self):
        self._detector.enabled = self.enabled_var.get()




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