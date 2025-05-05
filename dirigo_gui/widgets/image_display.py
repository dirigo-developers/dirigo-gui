from typing import Optional
import queue
import time

import customtkinter as ctk
from PIL import Image, ImageTk
import numpy as np

from dirigo.sw_interfaces.display import DisplayProduct



class ImageViewer(ctk.CTkFrame):
    """
    Stand-alone viewer widget for numpy images (RGB).
    """
    ZOOMS = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 4.0]

    def __init__(self, parent, width: int, height: int, *, bg: str = "black"):
        
        super().__init__(parent)

        self._canvas = ctk.CTkCanvas(self, width=width, height=height,
                                     bg=bg, highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)

        self._photo: Optional[ImageTk.PhotoImage] = None
        self._canvas_img: Optional[int] = None
        #self._callbacks: dict[str, Iterable[Callable]] = {}
        self._overlay_items: dict[str, int] = {}

        self._zoom_idx = 3 # default = 100%
        self._zoom     = self.ZOOMS[self._zoom_idx]

        # save last frame so we can redraw quickly
        self._native_frame: Optional[np.ndarray] = None

    def show(self, frame: np.ndarray) -> None:
        """Display an image."""
        if (not isinstance(frame, np.ndarray)
            or frame.dtype != np.uint8
            or frame.shape[2] != 3):
            raise ValueError("ImageView can only display 8-bit RGB numpy images.")
        self._native_frame = frame  # cache native-res copy

        t0 = time.perf_counter()
        if self._zoom != 1.0:
            
            pil_img = Image.fromarray(frame, mode="RGB").resize(
                (int(frame.shape[1] * self._zoom),
                 int(frame.shape[0] * self._zoom)),
                resample=Image.Resampling.NEAREST   # or BILINEAR
            )
            
        else:
            pil_img = Image.fromarray(frame, mode="RGB")
        t1 = time.perf_counter()
        #print("RESIZE", t1-t0)

        t0 = time.perf_counter()
        if self._photo is None:                 # create PhotoImage on 1st call
            self._photo = ImageTk.PhotoImage(pil_img)
            self._canvas_img = self._canvas.create_image(
                0, 0, anchor="nw", image=self._photo, tags=("bitmap",)
            )
            self._canvas.tag_lower("bitmap") # To keep overlay on top if exists
        else:                                   # subsequent calls: in-place
            self._photo.paste(pil_img)
            self._canvas.itemconfig(self._canvas_img, image=self._photo)
        t1 = time.perf_counter()
        #print("DRAW BITMAP", t1-t0)

    def configure_size(self, width: int, height: int) -> None:
        self._canvas.config(
            width=int(width * self._zoom), 
            height=int(height * self._zoom)
        )

        # Trigger regneration of the PhotoImage
        if self._canvas_img is not None:
            self._canvas.delete(self._canvas_img)
            self._canvas_img = None
            self._photo = None

    def set_zoom(self, factor: float) -> None:
        """Set an arbitrary zoom factor and redraw."""
        self._zoom = max(0.1, factor)
        self._redraw_last_frame()
        self._rescale_overlays()

    def cycle_zoom(self, direction: int = +1) -> None:
        """direction = +1 ➞ next zoom level, -1 ➞ previous."""
        new_zoom = self._zoom_idx + direction
        if not (0 <= new_zoom < len(self.ZOOMS)):
            return # ignore out of range
        self._zoom_idx = new_zoom
        self._zoom = self.ZOOMS[self._zoom_idx]
        self._redraw_last_frame()
        self._rescale_overlays()

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

    def _redraw_last_frame(self):
        if self._native_frame is not None:
            self.configure_size(
                width=int(self._native_frame.shape[1]),
                height=int(self._native_frame.shape[0])
            )
            self._paste(self._native_frame)

    def _paste(self, frame: np.ndarray, is_resize: bool = False):
        """internal: handles the Pillow→PhotoImage transfer"""
        if self._zoom != 1.0:
            # Pillow resize keeps CPU cost low (<3 ms for 1024×1024→2×)
            pil_img = Image.fromarray(frame, mode="RGB").resize(
                (int(frame.shape[1] * self._zoom),
                 int(frame.shape[0] * self._zoom)),
                resample=Image.Resampling.NEAREST   # or BILINEAR
            )
        else:
            pil_img = Image.fromarray(frame, mode="RGB")

        if self._photo is None:
            self._photo = ImageTk.PhotoImage(pil_img)
            self._canvas_img = self._canvas.create_image(
                0, 0, anchor="nw", image=self._photo, tags=("bitmap",)
            )
            self._canvas.tag_lower("bitmap")        # keep overlays on top
        else:
            self._photo.paste(pil_img)

    def _rescale_overlays(self):
        """Multiply every overlay's coords by the current zoom factor."""
        for item in self._canvas.find_withtag("overlay"):
            x0, y0, x1, y1 = self._canvas.coords(item)
            self._canvas.coords(
                item, x0 * self._zoom, y0 * self._zoom,
                      x1 * self._zoom, y1 * self._zoom
            )


class LiveViewer(ImageViewer):
    """Viewer widget with polling for automatic image updates."""
    POLLING_INTERVAL_MS = 16

    def __init__(self, parent, width: int, height: int, *, bg: str = "black"):
        super().__init__(parent, width, height, bg=bg)
        self.inbox = queue.Queue()   # provides inbox for Workers to publish to

        # Start polling
        self.poll_queue()

    def poll_queue(self):
        
        disp_product = None

        while True:
            try:
                if disp_product is not None:
                    disp_product._release()
                disp_product: DisplayProduct = self.inbox.get_nowait()
            except queue.Empty:
                break # queue drained

        if disp_product is not None:
            #t0 = time.perf_counter()
            self.show(disp_product.frame)
            #t1 = time.perf_counter()
            #print(f"TK DISP: {1000*(t1-t0):.3f}")

        #T = max(self.POLLING_INTERVAL_MS - int(1000*(t1-t0)), 0)
        #print("DELAY TIME (ms):", T)
        
        self.after(self.POLLING_INTERVAL_MS, self.poll_queue)
