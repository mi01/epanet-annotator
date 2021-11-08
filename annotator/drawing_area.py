import json
import math

import cairo
import gi  # type: ignore

gi.require_version("Gtk", "3.0")
from enum import Enum, unique
from typing import Optional

from gi.repository import Gdk, GdkPixbuf, GLib, Gtk  # type: ignore

from .network import Network, OverlayElement, OverlayType


@unique
class Layer(str, Enum):
    BACKGROUND = "Background"
    NETWORK = "Network"
    OVERLAY = "Overlay"


class DrawingArea(Gtk.ScrolledWindow):
    def __init__(
        self,
        window: Gtk.Window,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.set_policy(Gtk.PolicyType.ALWAYS, Gtk.PolicyType.ALWAYS)
        self.window = window

        self._current_layer: Layer = Layer.BACKGROUND
        self._overlay_type: OverlayType = OverlayType.HOUSE
        self._ratio_image: float = 1.0
        self._ratio_network: float = 1.0
        self._original_image: Optional[GdkPixbuf.Pixbuf] = None
        self._displayed_image: Optional[GdkPixbuf.Pixbuf] = None
        self._offset_x_image: int = 0
        self._offset_y_image: int = 0
        self._mouse_pressed_x: int = -1
        self._mouse_pressed_y: int = -1
        self._net: Optional[Network] = None
        self._offset_x_net: int = 0
        self._offset_y_net: int = 0

        self.area = Gtk.DrawingArea()
        self.area.set_events(Gdk.EventMask.ALL_EVENTS_MASK)
        self.area.connect("draw", self.on_draw)
        self.area.connect("button-press-event", self.on_drawing_area_mouse_press)
        self.area.connect("button-release-event", self.on_drawing_area_mouse_release)

        self._viewport = Gtk.Viewport()
        self._viewport.add(self.area)
        self.add(self._viewport)

    @property
    def current_layer(self) -> Layer:
        return self._current_layer

    @current_layer.setter
    def current_layer(self, value: Layer) -> None:
        self._current_layer = value

    @property
    def ratio_image(self) -> float:
        return self._ratio_image

    @property
    def ratio_network(self) -> float:
        return self._ratio_network

    @property
    def overlay_type(self) -> OverlayType:
        return self._overlay_type

    @overlay_type.setter
    def overlay_type(self, value: OverlayType):
        self._overlay_type = value

    def net_loaded(self) -> bool:
        return self._net is not None

    def bg_loaded(self) -> bool:
        return self._original_image is not None

    def load_bg_from_file(self, filename: str) -> None:
        try:
            self._original_image = GdkPixbuf.Pixbuf.new_from_file(filename)
            self._displayed_image = GdkPixbuf.Pixbuf.new_from_file(filename)
            self._scale_image()
            self.area.queue_draw()
        except GLib.Error:
            self._original_image = None
            self._displayed_image = None
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CANCEL,
                text="Unable to load image!",
            )
            dialog.run()
            dialog.destroy()

    def load_inp_from_file(self, filename: str) -> None:
        try:
            self._net = Network(self)
            if not self._net.load_network(filename):
                raise Exception("Inappropriate size of network!")
            self.area.queue_draw()
        except Exception as e:
            self._net = None
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CANCEL,
                text=str(e),
            )
            dialog.run()
            dialog.destroy()

    def load_overlay_from_file(self, filename: str) -> None:
        if self._net:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if not isinstance(content, dict):
                        raise Exception("Invalid file format!")
                    if "offset_img_x" in content:
                        self._offset_x_image = float(content["offset_img_x"])
                    if "offset_img_y" in content:
                        self._offset_y_image = float(content["offset_img_y"])
                    if "scale_img" in content:
                        self._ratio_image = float(content["scale_img"])
                    if "offset_net_x" in content:
                        self._offset_x_net = float(content["offset_net_x"])
                    if "offset_net_y" in content:
                        self._offset_y_net = float(content["offset_net_y"])
                    if "scale_net" in content:
                        self._ratio_network = float(content["scale_net"])
                    if "elements" in content and isinstance(content["elements"], list):
                        elements = []
                        for e in content["elements"]:
                            if "x" in e and "y" in e and "type" in e:
                                elements.append(
                                    OverlayElement(
                                        float(e["x"]),
                                        float(e["y"]),
                                        OverlayType(e["type"]),
                                    )
                                )
                        self._net.elements = elements
                    self.area.queue_draw()
            except Exception as e:
                dialog = Gtk.MessageDialog(
                    transient_for=self.window,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.CANCEL,
                    text=str(e),
                )
                dialog.run()
                dialog.destroy()

    def save_overlay_to_file(self, filename: str) -> None:
        if self._net:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "offset_img_x": self._offset_x_image,
                            "offset_img_y": self._offset_y_image,
                            "scale_img": self._ratio_image,
                            "offset_net_x": self._offset_x_net,
                            "offset_net_y": self._offset_y_net,
                            "scale_net": self._ratio_network,
                            "elements": [e.__dict__ for e in self._net.elements],
                        },
                        f,
                        ensure_ascii=False,
                    )
            except Exception as e:
                dialog = Gtk.MessageDialog(
                    transient_for=self.window,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.CANCEL,
                    text=str(e),
                )
                dialog.run()
                dialog.destroy()

    def _scale_image(self) -> None:
        if self._displayed_image:
            self._displayed_image = self._original_image.scale_simple(  # type: ignore
                self._original_image.get_width() * self._ratio_image,  # type: ignore
                self._original_image.get_height() * self._ratio_image,  # type: ignore
                2,
            )

    def on_zoom(self, ratio) -> None:
        if self._current_layer == Layer.BACKGROUND:
            self._ratio_image = ratio
            self._scale_image()
            self.area.queue_draw()
        elif (
            self._current_layer == Layer.NETWORK or self._current_layer == Layer.OVERLAY
        ):
            self._ratio_network = ratio
            self.area.queue_draw()

    def on_drawing_area_mouse_press(self, widget, event) -> None:
        (x, y) = int(event.x), int(event.y)
        if self._current_layer == Layer.BACKGROUND and self._displayed_image:
            if (
                x >= self._offset_x_image
                and x <= self._displayed_image.get_width() + self._offset_x_image
                and y >= self._offset_y_image
                and y <= self._displayed_image.get_height() + self._offset_y_image
            ):
                self._mouse_pressed_x = x
                self._mouse_pressed_y = y
        elif self._current_layer == Layer.NETWORK and self._net:
            (w, h) = self._net.get_dimensions(
                self._ratio_network, self._offset_x_net, self._offset_y_net
            )
            if (
                x >= self._offset_x_net
                and x <= w
                and y >= self._offset_y_net
                and y <= h
            ):
                self._mouse_pressed_x = x
                self._mouse_pressed_y = y
        elif self._current_layer == Layer.OVERLAY and self._net:
            self._net.add_overlay_element(
                int((x - self._offset_x_net) / self._ratio_network),
                int((y - self._offset_y_net) / self._ratio_network),
                self._overlay_type,
            )
            self.area.queue_draw()

    def on_drawing_area_mouse_release(self, widget, event) -> None:
        if self._mouse_pressed_x < 0 or self._mouse_pressed_y < 0:
            return
        (x, y) = int(event.x), int(event.y)
        if self._current_layer == Layer.BACKGROUND and self._displayed_image:
            self._offset_x_image += x - self._mouse_pressed_x
            self._offset_y_image += y - self._mouse_pressed_y
            self.area.queue_draw()
        elif self._current_layer == Layer.NETWORK and self._net:
            self._offset_x_net += x - self._mouse_pressed_x
            self._offset_y_net += y - self._mouse_pressed_y
            self.area.queue_draw()
        self._mouse_pressed_x = -1
        self._mouse_pressed_y = -1

    def on_draw(self, drawable, ctx) -> None:
        height = 0
        width = 0
        if self._displayed_image:
            height = self._displayed_image.get_height() + self._offset_y_image
            width = self._displayed_image.get_width() + self._offset_x_image
        if self._net:
            (w, h) = self._net.get_dimensions(
                self._ratio_network, self._offset_x_net, self._offset_y_net
            )
            width = w if w > width else width
            height = h if h > height else height

        drawable.set_size_request(width, height)

        if self._displayed_image:
            Gdk.cairo_set_source_pixbuf(
                ctx, self._displayed_image, self._offset_x_image, self._offset_y_image
            )
            ctx.paint()

        if self._net:
            self._net.draw(
                ctx,
                self._ratio_network,
                self._offset_x_net,
                self._offset_y_net,
            )
