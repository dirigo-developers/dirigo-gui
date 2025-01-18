import customtkinter as ctk

from dirigo import units
from dirigo.hw_interfaces.stage import MultiAxisStage
from dirigo.hw_interfaces.scanner import ObjectiveZScanner


XY_VELOCITY = units.Velocity("2 mm/s")
Z_VELOCITY = units.Velocity("0.02 mm/s")


class XYControl(ctk.CTkFrame):
    """
    A simple frame containing four arrow buttons in a clockwise layout:
    Up, Right, Down, and Left.
    """

    def __init__(self, parent: 'StageControl', *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Create arrow buttons
        font = ctk.CTkFont(weight="bold")
        self.btn_up = ctk.CTkButton(self, text="↑", font=font, width=30)
        self.btn_right = ctk.CTkButton(self, text="→", font=font, width=30)
        self.btn_down = ctk.CTkButton(self, text="↓", font=font, width=30)
        self.btn_left = ctk.CTkButton(self, text="←", font=font, width=30)

        self.btn_up.bind("<ButtonPress-1>", lambda event: parent.on_press('+y', XY_VELOCITY))
        self.btn_up.bind("<ButtonRelease-1>", lambda event: parent.on_release())
        self.btn_right.bind("<ButtonPress-1>", lambda event: parent.on_press('+x', XY_VELOCITY))
        self.btn_right.bind("<ButtonRelease-1>", lambda event: parent.on_release())
        self.btn_down.bind("<ButtonPress-1>", lambda event: parent.on_press('-y', XY_VELOCITY))
        self.btn_down.bind("<ButtonRelease-1>", lambda event: parent.on_release())
        self.btn_left.bind("<ButtonPress-1>", lambda event: parent.on_press('-x', XY_VELOCITY))
        self.btn_left.bind("<ButtonRelease-1>", lambda event: parent.on_release())

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

    def __init__(self, parent: 'StageControl', *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Create arrow buttons 
        font = ctk.CTkFont(weight="bold")
        self.btn_up = ctk.CTkButton(self, text="↑", font=font, width=30)
        self.btn_down = ctk.CTkButton(self, text="↓", font=font, width=30)

        self.btn_up.bind("<ButtonPress-1>", lambda event: parent.on_press('+z', Z_VELOCITY))
        self.btn_up.bind("<ButtonRelease-1>", lambda event: parent.on_release())
        self.btn_down.bind("<ButtonPress-1>", lambda event: parent.on_press('-z', Z_VELOCITY))
        self.btn_down.bind("<ButtonRelease-1>", lambda event: parent.on_release())

        # Button grid:
        #
        #   (0,0) Up
        #   (1,0) 'Z'  
        #   (2,0) Down
        #
        self.btn_up.grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkLabel(self, text="Z").grid(row=1, column=0)
        self.btn_down.grid(row=2, column=0, padx=5, pady=5)


class StageControl(ctk.CTkFrame):
    def __init__(self, parent, stage: MultiAxisStage, objective_scanner: ObjectiveZScanner, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._stage = stage
        self._objective_scanner = objective_scanner
        self._is_pressed = False

        self.xy = XYControl(self, fg_color="transparent")
        self.xy.pack(side=ctk.LEFT, expand=True, fill="x", padx=5, pady=5)

        self.z = ZControl(self, fg_color="transparent")
        self.z.pack(side=ctk.RIGHT, fill="x", padx=5, pady=5)

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
            self._objective_scanner.move_velocity(velocity)
        elif direction == "-z":
            self._objective_scanner.move_velocity(-velocity)

    def on_release(self):
        """Stops all motors."""
        self._stage.x.stop()
        self._stage.y.stop()
        self._objective_scanner.stop()



if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Stage Jog Controls Demo")

    stage_jog_controls = StageControl(root, None)
    stage_jog_controls.pack(expand=True, fill="x", padx=20, pady=20)

    root.mainloop()