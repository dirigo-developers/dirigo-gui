import customtkinter as ctk

from dirigo import units
from dirigo.hw_interfaces.stage import MultiAxisStage, LinearStage
from dirigo_gui.components.common import LabeledDisplay


XY_VELOCITY_DEFAULT = units.Velocity("2 mm/s") # TODO set these somewhere else
Z_VELOCITY_DEFAULT = units.Velocity("0.03 mm/s")

XY_STEP_DEFAULT = units.Position("100 μm")
Z_STEP_DEFAULT  = units.Position("10 μm")


class LabeledEntry(ctk.CTkFrame):
    """Small label + editable entry."""
    def __init__(self, parent, text: str, default: str, width: int = 90):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text=text).pack(side=ctk.LEFT, padx=(0, 6))
        self.entry = ctk.CTkEntry(self, width=width)
        self.entry.insert(0, default)
        self.entry.pack(side=ctk.LEFT)

    def get(self) -> str:
        return self.entry.get().strip()

    def set(self, s: str) -> None:
        self.entry.delete(0, "end")
        self.entry.insert(0, s)


class LiveLabeledEntry(ctk.CTkFrame):
    """
    Entry that can be updated programmatically, but won't be overwritten while
    the user is typing. Call .set_live(value_str) from your poll loop.
    """
    def __init__(
        self,
        parent,
        text: str,
        default: str = "",
        width: int = 70,
        label_width: int = 26,
        on_commit=None,  # fn(str) -> None
        unit_hint: str | None = None,
    ):
        super().__init__(parent, fg_color="transparent")

        self._on_commit = on_commit
        self._editing = False

        label_text = text if unit_hint is None else f"{text}"
        self.label = ctk.CTkLabel(self, text=label_text, width=label_width, anchor="e")
        self.label.pack(side=ctk.LEFT, padx=(0, 2))

        self.entry = ctk.CTkEntry(self, width=width)
        self.entry.insert(0, default)
        self.entry.pack(side=ctk.LEFT)

        # Track editing state
        self.entry.bind("<FocusIn>", lambda e: self._set_editing(True))
        self.entry.bind("<FocusOut>", self._commit_if_needed)
        self.entry.bind("<Return>", self._commit_if_needed)

    def _set_editing(self, v: bool) -> None:
        self._editing = v

    def _commit_if_needed(self, event=None) -> None:
        self._editing = False
        if self._on_commit:
            self._on_commit(self.entry.get().strip())

    def set_live(self, s: str) -> None:
        """Update displayed value unless user is editing."""
        if self._editing:
            return
        self.entry.delete(0, "end")
        self.entry.insert(0, s)

    def get(self) -> str:
        return self.entry.get().strip()


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

        self.btn_up.bind("<ButtonPress-1>",     lambda e: stage_control.on_button_press('+y'))
        self.btn_up.bind("<ButtonRelease-1>",   lambda e: stage_control.on_button_release('+y'))
        self.btn_right.bind("<ButtonPress-1>",  lambda e: stage_control.on_button_press('+x'))
        self.btn_right.bind("<ButtonRelease-1>",lambda e: stage_control.on_button_release('+x'))
        self.btn_down.bind("<ButtonPress-1>",   lambda e: stage_control.on_button_press('-y'))
        self.btn_down.bind("<ButtonRelease-1>", lambda e: stage_control.on_button_release('-y'))
        self.btn_left.bind("<ButtonPress-1>",   lambda e: stage_control.on_button_press('-x'))
        self.btn_left.bind("<ButtonRelease-1>", lambda e: stage_control.on_button_release('-x'))

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

        self.btn_up.bind("<ButtonPress-1>",     lambda e: stage_control.on_button_press('+z'))
        self.btn_up.bind("<ButtonRelease-1>",   lambda e: stage_control.on_button_release('+z'))
        self.btn_down.bind("<ButtonPress-1>",   lambda e: stage_control.on_button_press('-z'))
        self.btn_down.bind("<ButtonRelease-1>", lambda e: stage_control.on_button_release('-z'))

        # Button grid:
        #
        #   (0,0) Up
        #   (1,0) 'Z'  
        #   (2,0) Down
        #
        self.btn_up.grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkLabel(self, text="Z").grid(row=1, column=0)
        self.btn_down.grid(row=2, column=0, padx=5, pady=5)


# class NumericEntries(ctk.CTkFrame):
#     ENTRY_WIDTH = 52
#     def __init__(self, parent, axes: list = ["x", "y", "z"]):
#         super().__init__(parent, fg_color="transparent")

#         # Create entries
#         self.x = LabeledDisplay(
#             self,
#             text="X:",
#             default="x mm",
#             width=self.ENTRY_WIDTH
#         )
#         if "x" in axes:
#             self.x.grid(row=0, column=0, padx=2)

#         self.y = LabeledDisplay(
#             self,
#             text="Y:",
#             default="y mm",
#             width=self.ENTRY_WIDTH
#         )
#         if "y" in axes:
#             self.y.grid(row=0, column=1, padx=2)

#         self.z = LabeledDisplay(
#             self,
#             text="Z:",
#             default="z um",
#             width=self.ENTRY_WIDTH
#         )
#         if "z" in axes:
#             self.z.grid(row=0, column=2, padx=2)


class StageControl(ctk.CTkFrame):
    POLLING_INTERVAL_MS = 50
    def __init__(self, 
                 parent, 
                 stage: MultiAxisStage, 
                 z_motor: LinearStage | None, 
                 *args, 
                 **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._stage = stage
        self._z_motor = z_motor
        #self._is_pressed = False

        axes = []
        
        # ----------- Header ----------
        stage_label = ctk.CTkLabel(self, text="Stage", anchor="w", font=ctk.CTkFont(size=16, weight='bold'))
        stage_label.pack(fill="x", padx=10, pady=1)

        # ---------- Mode + Settings ----------
        settings = ctk.CTkFrame(self, fg_color="transparent")
        settings.pack(fill="x", padx=10, pady=(0, 6))

        self._mode = ctk.StringVar(value="Step")  # "Step" | "Continuous"

        mode_row = ctk.CTkFrame(settings, fg_color="transparent")
        mode_row.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(mode_row, text="Mode:").pack(side=ctk.LEFT, padx=(0, 8))

        mode_seg = ctk.CTkSegmentedButton(
            mode_row,
            values=["Step", "Continuous"],
            variable=self._mode,
            # Map displayed labels -> internal values
            command=lambda v: self._mode.set(v),
        )
        mode_seg.set("Step")  # initialize
        mode_seg.pack(side=ctk.LEFT)

        edit_grid = ctk.CTkFrame(settings, fg_color="transparent")
        edit_grid.pack(fill="x")

        edit_grid.grid_columnconfigure(0, weight=1)
        edit_grid.grid_columnconfigure(1, weight=1)

        self.xy_step_entry = LabeledEntry(edit_grid, "XY step:", str(XY_STEP_DEFAULT), width=55)
        self.xy_vel_entry  = LabeledEntry(edit_grid, "XY vel:",  str(XY_VELOCITY_DEFAULT), width=60)

        self.xy_step_entry.grid(row=0, column=0, sticky="e", padx=(0, 4), pady=(0, 6))
        self.xy_vel_entry.grid(row=0, column=1, sticky="e", pady=(0, 6))

        if self._z_motor:
            self.z_step_entry = LabeledEntry(edit_grid, "Z step:", str(Z_STEP_DEFAULT), width=55)
            self.z_vel_entry  = LabeledEntry(edit_grid, "Z vel:",  str(Z_VELOCITY_DEFAULT), width=60)

            self.z_step_entry.grid(row=1, column=0, sticky="e", padx=(0, 4))
            self.z_vel_entry.grid(row=1, column=1, sticky="e")

        # ---------- Buttons ----------
        axes = ["x", "y"]

        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.xy = XYControl(self, buttons_frame, fg_color="transparent")
        self.xy.pack(side=ctk.LEFT, expand=True, fill="x", padx=10)

        self.z = ZControl(self, buttons_frame, fg_color="transparent")
        if self._z_motor:
            self.z.pack(side=ctk.RIGHT, fill="x", padx=10)
            axes.append("z")

        buttons_frame.pack(fill="x", padx=5, pady=3)

        # ---------- Position Readout ----------
        pos_row = ctk.CTkFrame(self, fg_color="transparent")
        pos_row.pack(fill="x", padx=2, pady=(3, 6))

        self.x_goto = LiveLabeledEntry(
            pos_row, "X:", default="",
            width=65, label_width=6,
            on_commit=self._goto_x
        )
        self.y_goto = LiveLabeledEntry(
            pos_row, "Y:", default="",
            width=65, label_width=6,
            on_commit=self._goto_y
        )

        self.x_goto.pack(side=ctk.LEFT, padx=(0, 2))
        self.y_goto.pack(side=ctk.LEFT, padx=(0, 2))

        if self._z_motor:
            self.z_goto = LiveLabeledEntry(
                pos_row, "Z:", default="",
                width=65, label_width=6,
                on_commit=self._goto_z
            )
            self.z_goto.pack(side=ctk.LEFT)

        self.poll_stage()

    # ---------------- Polling ----------------
    def poll_stage(self):
        self.x_goto.set_live(str(self._stage.x.position.with_unit("mm")))
        self.y_goto.set_live(str(self._stage.y.position.with_unit("mm")))
        if self._z_motor:
            self.z_goto.set_live(str(self._z_motor.position.with_unit("μm")))

        self.after(self.POLLING_INTERVAL_MS, self.poll_stage)

    # ---------------- Parsing helpers ----------------
    def _xy_velocity(self) -> units.Velocity:
        s = self.xy_vel_entry.get()
        try:
            return units.Velocity(s)
        except Exception:
            return XY_VELOCITY_DEFAULT

    def _z_velocity(self) -> units.Velocity:
        if not self._z_motor:
            return Z_VELOCITY_DEFAULT
        s = self.z_vel_entry.get()
        try:
            return units.Velocity(s)
        except Exception:
            return Z_VELOCITY_DEFAULT

    def _xy_step(self) -> units.Position:
        s = self.xy_step_entry.get()
        try:
            return units.Position(s)
        except Exception:
            return XY_STEP_DEFAULT

    def _z_step(self) -> units.Position:
        if not self._z_motor:
            return Z_STEP_DEFAULT
        s = self.z_step_entry.get()
        try:
            return units.Position(s)
        except Exception:
            return Z_STEP_DEFAULT

    # ---------------- Motion primitives ----------------

    def _move_relative(self, axis_obj: LinearStage, delta: units.Position) -> None:
        new_pos = axis_obj.position + delta
        axis_obj.move_to(new_pos)

    def _start_continuous(self, direction: str) -> None:
        if direction == "+y":
            self._stage.y.move_velocity(-self._xy_velocity())
        elif direction == "+x":
            self._stage.x.move_velocity(-self._xy_velocity())
        elif direction == "-y":
            self._stage.y.move_velocity(self._xy_velocity())
        elif direction == "-x":
            self._stage.x.move_velocity(self._xy_velocity())
        elif direction == "+z" and self._z_motor:
            self._z_motor.move_velocity(self._z_velocity())
        elif direction == "-z" and self._z_motor:
            self._z_motor.move_velocity(-self._z_velocity())

    def _do_step(self, direction: str) -> None:
        if direction in {"+x", "-x", "+y", "-y"}:
            step = self._xy_step()
            if direction == "+x":
                self._move_relative(self._stage.x, -step)
            elif direction == "-x":
                self._move_relative(self._stage.x, step)
            elif direction == "+y":
                self._move_relative(self._stage.y, -step)
            elif direction == "-y":
                self._move_relative(self._stage.y, step)
            return

        if direction in {"+z", "-z"} and self._z_motor:
            step = self._z_step()
            if direction == "+z":
                self._move_relative(self._z_motor, step)
            else:
                self._move_relative(self._z_motor, -step)


    # ---------------- Event handlers ----------------

    def on_button_press(self, direction: str) -> None:
        if self._mode.get() == "Continuous":
            self._start_continuous(direction)
        # In step mode, we do nothing on press (so press-and-hold doesn't “creep”).

    def on_button_release(self, direction: str) -> None:
        if self._mode.get() == "Continuous":
            self.stop_all()
        else:
            # A “click” becomes a step
            self._do_step(direction)

    def stop_all(self) -> None:
        self._stage.x.stop()
        self._stage.y.stop()
        if self._z_motor:
            self._z_motor.stop()

    def _goto_x(self, s: str) -> None:
        try:
            self._stage.x.move_to(units.Position(s))
        except Exception:
            pass  # optionally show validation feedback

    def _goto_y(self, s: str) -> None:
        try:
            self._stage.y.move_to(units.Position(s))
        except Exception:
            pass

    def _goto_z(self, s: str) -> None:
        if not self._z_motor:
            return
        try:
            self._z_motor.move_to(units.Position(s))
        except Exception:
            pass

