import customtkinter as ctk

from dirigo import units
from dirigo.hw_interfaces.stage import MultiAxisStage
from dirigo.hw_interfaces.scanner import ObjectiveZScanner
from dirigo_gui.components.common import LabeledDisplay


XY_VELOCITY = units.Velocity("2 mm/s") # TODO set these somewhere else
Z_VELOCITY = units.Velocity("0.03 mm/s")


class XYControl(ctk.CTkFrame):
    """
    A simple frame containing four arrow buttons in a clockwise layout:
    Up, Right, Down, and Left.
    """

    def __init__(self, stage_control: 'StageControl', parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Create arrow buttons
        font = ctk.CTkFont(weight="bold")
        self.btn_up = ctk.CTkButton(self, text="↑", font=font, width=30)
        self.btn_right = ctk.CTkButton(self, text="→", font=font, width=30)
        self.btn_down = ctk.CTkButton(self, text="↓", font=font, width=30)
        self.btn_left = ctk.CTkButton(self, text="←", font=font, width=30)

        self.btn_up.bind("<ButtonPress-1>", lambda event: stage_control.on_press('+y', XY_VELOCITY))
        self.btn_up.bind("<ButtonRelease-1>", lambda event: stage_control.on_release())
        self.btn_right.bind("<ButtonPress-1>", lambda event: stage_control.on_press('+x', XY_VELOCITY))
        self.btn_right.bind("<ButtonRelease-1>", lambda event: stage_control.on_release())
        self.btn_down.bind("<ButtonPress-1>", lambda event: stage_control.on_press('-y', XY_VELOCITY))
        self.btn_down.bind("<ButtonRelease-1>", lambda event: stage_control.on_release())
        self.btn_left.bind("<ButtonPress-1>", lambda event: stage_control.on_press('-x', XY_VELOCITY))
        self.btn_left.bind("<ButtonRelease-1>", lambda event: stage_control.on_release())

        # Button grid:
        #
        #             (0,1) Up
        # (1,0) Left  (1,1) 'XY'  (1,2) Right
        #             (2,1) Down
        #
        self.btn_up.grid(row=0, column=1, padx=5, pady=5)
        self.btn_left.grid(row=1, column=0, padx=5, pady=5)
        ctk.CTkLabel(self, text="XY").grid(row=1, column=1)
        self.btn_right.grid(row=1, column=2, padx=5, pady=5)
        self.btn_down.grid(row=2, column=1, padx=5, pady=5)


class ZControl(ctk.CTkFrame):
    """
    A simple frame containing four arrow buttons in a clockwise layout:
    Up, Right, Down, and Left.
    """

    def __init__(self, stage_control: 'StageControl', parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Create arrow buttons 
        font = ctk.CTkFont(weight="bold")
        self.btn_up = ctk.CTkButton(self, text="↑", font=font, width=30)
        self.btn_down = ctk.CTkButton(self, text="↓", font=font, width=30)

        self.btn_up.bind("<ButtonPress-1>", lambda event: stage_control.on_press('+z', Z_VELOCITY))
        self.btn_up.bind("<ButtonRelease-1>", lambda event: stage_control.on_release())
        self.btn_down.bind("<ButtonPress-1>", lambda event: stage_control.on_press('-z', Z_VELOCITY))
        self.btn_down.bind("<ButtonRelease-1>", lambda event: stage_control.on_release())

        # Button grid:
        #
        #   (0,0) Up
        #   (1,0) 'Z'  
        #   (2,0) Down
        #
        self.btn_up.grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkLabel(self, text="Z").grid(row=1, column=0)
        self.btn_down.grid(row=2, column=0, padx=5, pady=5)


class NumericEntries(ctk.CTkFrame):
    ENTRY_WIDTH = 52
    def __init__(self, parent, axes: list = ["x", "y", "z"]):
        super().__init__(parent, fg_color="transparent")

        # Create entries
        self.x = LabeledDisplay(
            self,
            text="X:",
            default="x mm",
            width=self.ENTRY_WIDTH
        )
        if "x" in axes:
            self.x.grid(row=0, column=0, padx=2)

        self.y = LabeledDisplay(
            self,
            text="Y:",
            default="y mm",
            width=self.ENTRY_WIDTH
        )
        if "y" in axes:
            self.y.grid(row=0, column=1, padx=2)

        self.z = LabeledDisplay(
            self,
            text="Z:",
            default="z um",
            width=self.ENTRY_WIDTH
        )
        if "z" in axes:
            self.z.grid(row=0, column=2, padx=2)




class StageControl(ctk.CTkFrame):
    POLLING_INTERVAL_MS = 50
    def __init__(self, parent, stage: MultiAxisStage, objective_z_scanner: ObjectiveZScanner, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._stage = stage
        self._objective_z_scanner = objective_z_scanner
        self._is_pressed = False

        axes = []
        
        stage_label = ctk.CTkLabel(self, text="Stage", anchor="w", font=ctk.CTkFont(size=16, weight='bold'))
        stage_label.pack(fill="x", padx=10, pady=1)

        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.xy = XYControl(self, buttons_frame, fg_color="transparent")
        self.xy.pack(side=ctk.LEFT, expand=True, fill="x", padx=10)
        axes.append("x")
        axes.append("y")

        self.z = ZControl(self, buttons_frame, fg_color="transparent")
        if self._objective_z_scanner:
            self.z.pack(side=ctk.RIGHT, fill="x", padx=10)
            axes.append("z")

        buttons_frame.pack(fill="x", padx=5, pady=3)

        self.xyz_entries = NumericEntries(self, axes=axes)
        self.xyz_entries.pack(fill="x", padx=5, pady=3)

        # Start polling
        self.poll_stage()

    def poll_stage(self):
        self.xyz_entries.x.update(self._stage.x.position.with_unit("mm"))
        self.xyz_entries.y.update(self._stage.y.position.with_unit("mm"))
        if self._objective_z_scanner:
            self.xyz_entries.z.update(self._objective_z_scanner.position.with_unit("μm"))
        
        self.after(self.POLLING_INTERVAL_MS, self.poll_stage)

    def on_press(self, direction: str, velocity: units.Velocity):
        """Initiates constant velocity movement"""
        self._is_pressed = True
        if direction == "+y":
            self._stage.y.move_velocity(-velocity)
        elif direction == "+x":
            self._stage.x.move_velocity(velocity)
        elif direction == "-y":
            self._stage.y.move_velocity(velocity)
        elif direction == "-x":
            self._stage.x.move_velocity(-velocity)
        elif direction == "+z":
            self._objective_z_scanner.move_velocity(velocity)
        elif direction == "-z":
            self._objective_z_scanner.move_velocity(-velocity)

    def on_release(self):
        """Stops all motors."""
        self._stage.x.stop()
        self._stage.y.stop()
        self._objective_z_scanner.stop()

