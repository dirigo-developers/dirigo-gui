from typing import Callable, Iterable, Optional
import queue

import customtkinter as ctk
from PIL import Image, ImageTk
import numpy as np



class ImageViewer(ctk.CTkFrame):
    """
    Stand-alone viewer widget for numpy images (RGB).
    """
    def __init__(self, parent, width: int, height: int, *, bg: str = "black"):
        
        super().__init__(parent)

        self._canvas = ctk.CTkCanvas(self, width=width, height=height,
                                     bg=bg, highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)

        self._photo: Optional[ImageTk.PhotoImage] = None
        self._canvas_img: Optional[int] = None
        #self._callbacks: dict[str, Iterable[Callable]] = {}
        self._overlay_items: dict[str, int] = {}

    def show(self, frame: np.ndarray) -> None:
        """Display an image."""
        if (not isinstance(frame, np.ndarray)
            or frame.dtype != np.uint8
            or frame.shape[2] != 3):
            raise ValueError("ImageView can only display 8-bit RGB numpy images.")

        pil_img = Image.fromarray(frame, mode="RGB")

        if self._photo is None:                 # create PhotoImage on 1st call
            self._photo = ImageTk.PhotoImage(pil_img)
            self._canvas_img = self._canvas.create_image(
                0, 0, anchor="nw", image=self._photo, tags=("bitmap",)
            )
            self._canvas.tag_raise("overlay")
        else:                                   # subsequent calls: in-place
            self._photo.paste(pil_img)
            self._canvas.itemconfig(self._canvas_img, image=self._photo)

    def configure_size(self, width: int, height: int) -> None:
        self._canvas.config(width=width, height=height)

        # Trigger regneration of the PhotoImage
        if self._canvas_img is not None:
            self._canvas.delete(self._canvas_img)
            self._canvas_img = None
            self._photo = None

    # def bind_events(self, **events) -> None:
    #     """
    #     Add callbacks: viewer.bind_events(click=func, motion=func)
    #     Callbacks receive (event, x_pix, y_pix) arguments.
    #     """
    #     mapping = {"click": "<Button-1>", "motion": "<Motion>"}
    #     for key, callback in events.items():
    #         sequence = mapping.get(key)
    #         if sequence:
    #             self._canvas.bind(sequence,
    #                 lambda e, cb=callback: cb(e, e.x, e.y))

    def add_overlay(self, name: str, kind: str = "rect",
                    *, outline="yellow", width=2, **coords):
        """
        name   - unique key so you can update/remove later
        kind   - 'rect', 'oval', 'line', 'crosshair'
        coords - supply either (x0,y0,x1,y1) or (cx,cy,r) for circle
        """
        if name in self._overlay_items:
            self.remove_overlay(name)

        if kind == "rect":
            item = self._canvas.create_rectangle(
                coords["x0"], coords["y0"], coords["x1"], coords["y1"],
                outline=outline, width=width, tags=("overlay",)
            )
        elif kind == "oval":
            item = self._canvas.create_oval(
                coords["x0"], coords["y0"], coords["x1"], coords["y1"],
                outline=outline, width=width, tags=("overlay",)
            )
        elif kind == "crosshair":
            cx, cy, r = coords["cx"], coords["cy"], coords["r"]
            item = self._canvas.create_line(
                cx-r, cy, cx+r, cy, fill=outline, width=width, tags=("overlay",)
            )
            _ = self._canvas.create_line(
                cx, cy-r, cx, cy+r, fill=outline, width=width, tags=("overlay",)
            )
            item = "crosshair"  # sentinel to say we created two items
        else:
            raise ValueError("unknown overlay kind")

        self._overlay_items[name] = item
        self._canvas.tag_raise("overlay")          # keep on top

    def update_overlay(self, name: str, **coords):
        """
        Fast path: just move existing geometry.
        """
        item = self._overlay_items.get(name)
        if item is None:
            raise KeyError(name)

        if isinstance(item, str) and item == "crosshair":
            # we stored sentinel: fetch both lines via canvas.find_withtag
            lines = self._canvas.find_withtag(name)
            cx, cy, r = coords["cx"], coords["cy"], coords["r"]
            self._canvas.coords(lines[0], cx-r, cy, cx+r, cy)
            self._canvas.coords(lines[1], cx, cy-r, cx, cy+r)
        else:
            self._canvas.coords(
                item, coords["x0"], coords["y0"], coords["x1"], coords["y1"]
            )

    def remove_overlay(self, name: str):
        item = self._overlay_items.pop(name, None)
        if item is None:
            return
        if isinstance(item, str) and item == "crosshair":
            self._canvas.delete(name)         # deletes both lines via tag
        else:
            self._canvas.delete(item)


class LiveViewer(ImageViewer):
    """Viewer widget with polling for automatic image updates."""
    POLLING_INTERVAL_MS = 16

    def __init__(self, parent, width: int, height: int, *, bg: str = "black"):
        super().__init__(parent, width, height, bg=bg)
        self.inbox = queue.Queue()   # provides inbox for Workers to publish to

        # Start polling
        self.poll_queue()

    def poll_queue(self):
        try:
            image: np.ndarray = self.inbox.get(block=False)

            if image is None:           # codes for end of acquisition stream
                pass
            else:
                self.show(image)

        except queue.Empty:
            pass
        
        finally:
            self.after(self.POLLING_INTERVAL_MS, self.poll_queue)