import gi  # type: ignore

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # type: ignore

from .drawing_area import DrawingArea, Layer
from .network import OverlayType


class MainMenu(Gtk.VBox):
    def __init__(self, window: Gtk.Window, drawing_area: DrawingArea):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.window = window
        self.drawing_area = drawing_area

        filemenu = Gtk.Menu()
        menuitem = Gtk.MenuItem("File")
        menuitem.set_submenu(filemenu)

        load_bg_menu = Gtk.MenuItem("Load Background Image")
        load_bg_menu.connect("activate", self.on_load_bg)

        load_inp_menu = Gtk.MenuItem("Load INP File")
        load_inp_menu.connect("activate", self.on_load_inp)

        self.save_overlay = Gtk.MenuItem("Save Overlay")
        self.save_overlay.connect("activate", self.on_save_overlay)
        self.save_overlay.set_sensitive(False)

        self.load_overlay = Gtk.MenuItem("Load Overlay")
        self.load_overlay.connect("activate", self.on_load_overlay)
        self.load_overlay.set_sensitive(False)

        exit = Gtk.MenuItem("Exit")
        exit.connect("activate", Gtk.main_quit)

        filemenu.append(load_bg_menu)
        filemenu.append(load_inp_menu)
        filemenu.append(Gtk.SeparatorMenuItem())
        filemenu.append(self.save_overlay)
        filemenu.append(self.load_overlay)
        filemenu.append(Gtk.SeparatorMenuItem())
        filemenu.append(exit)

        menubar = Gtk.MenuBar()
        menubar.append(menuitem)

        adjustment = Gtk.Adjustment(
            upper=20.0, lower=0.0, step_increment=0.05, page_increment=0.5
        )
        self.spinbutton = Gtk.SpinButton()
        self.spinbutton.configure(adjustment, 0.05, 3)
        self.spinbutton.set_value(self.drawing_area.ratio_image)
        self.spinbutton.connect("value-changed", self.on_value_changed)
        self._set_margin_top_bottom(self.spinbutton)

        self.combo_overlay = Gtk.ComboBoxText()
        self.combo_overlay.set_entry_text_column(0)
        self.combo_overlay.connect("changed", self.on_overlay_changed)
        for t in OverlayType:
            self.combo_overlay.append_text(t)
        self.combo_overlay.set_active(0)
        self.combo_overlay.set_sensitive(False)
        self._set_margin_top_bottom(self.combo_overlay)

        self.combo_layer = Gtk.ComboBoxText()
        self.combo_layer.set_entry_text_column(0)
        self.combo_layer.connect("changed", self.on_layer_changed)
        for layer in Layer:
            self.combo_layer.append_text(layer)
        self.combo_layer.set_active(0)
        self._set_margin_top_bottom(self.combo_layer)

        lbl_empty = Gtk.Label(label=" ")
        lbl_layer = Gtk.Label(label="Layer: ")
        lbl_layer.set_margin_left(20)
        lbl_zoom = Gtk.Label(label="Zoom: ")
        lbl_zoom.set_margin_left(20)
        lbl_overlay = Gtk.Label(label="Overlay: ")
        lbl_overlay.set_margin_left(20)

        self.pack_start(menubar, False, False, 0)
        self.pack_start(lbl_empty, True, True, 0)
        self.pack_start(lbl_overlay, False, False, 5)
        self.pack_start(self.combo_overlay, False, False, 0)
        self.pack_start(lbl_layer, False, False, 5)
        self.pack_start(self.combo_layer, False, False, 0)
        self.pack_start(lbl_zoom, False, False, 5)
        self.pack_start(self.spinbutton, False, False, 5)

    def _set_margin_top_bottom(self, widget: Gtk.Widget):
        widget.set_margin_top(3)
        widget.set_margin_bottom(3)

    def on_layer_changed(self, combo):
        self.drawing_area.current_layer = Layer(combo.get_active_text())
        if self.drawing_area.current_layer == Layer.BACKGROUND:
            self.spinbutton.set_value(self.drawing_area.ratio_image)
            self.combo_overlay.set_sensitive(False)
        elif self.drawing_area.current_layer == Layer.NETWORK:
            self.spinbutton.set_value(self.drawing_area.ratio_network)
            self.combo_overlay.set_sensitive(False)
        else:
            self.spinbutton.set_value(self.drawing_area.ratio_network)
            self.combo_overlay.set_sensitive(True)

    def on_overlay_changed(self, combo):
        self.drawing_area.overlay_type = OverlayType(combo.get_active_text())

    def on_value_changed(self, scroll):
        self.drawing_area.on_zoom(self.spinbutton.get_value())

    def _create_load_file_dialog(self):
        dialog = Gtk.FileChooserDialog(
            title="Choose file", parent=self.window, action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )
        return dialog

    def on_load_inp(self, widget):
        dialog = self._create_load_file_dialog()

        filter_inp = Gtk.FileFilter()
        filter_inp.set_name("INP file")
        filter_inp.add_pattern("*.inp")
        dialog.add_filter(filter_inp)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.drawing_area.load_inp_from_file(dialog.get_filename())
        dialog.destroy()

        if self.drawing_area.net_loaded():
            self.load_overlay.set_sensitive(True)
            self.save_overlay.set_sensitive(True)

    def on_load_bg(self, widget):
        dialog = self._create_load_file_dialog()

        filter_jpg = Gtk.FileFilter()
        filter_jpg.set_name("JPG/JPEG")
        filter_jpg.add_mime_type("image/jpeg")
        dialog.add_filter(filter_jpg)

        filter_png = Gtk.FileFilter()
        filter_png.set_name("PNG")
        filter_png.add_mime_type("image/png")
        dialog.add_filter(filter_png)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.drawing_area.load_bg_from_file(dialog.get_filename())
        dialog.destroy()

    def on_save_overlay(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Save file", parent=self.window, action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK,
            Gtk.ResponseType.OK,
        )

        filter_inpx = Gtk.FileFilter()
        filter_inpx.set_name("INPX file")
        filter_inpx.add_pattern("*.inpx")
        dialog.add_filter(filter_inpx)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            if not filename.lower().endswith(".inpx"):
                filename += ".inpx"
            self.drawing_area.save_overlay_to_file(filename)
        dialog.destroy()

    def on_load_overlay(self, widget):
        dialog = self._create_load_file_dialog()

        filter_inpx = Gtk.FileFilter()
        filter_inpx.set_name("INPX file")
        filter_inpx.add_pattern("*.inpx")
        dialog.add_filter(filter_inpx)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.drawing_area.load_overlay_from_file(dialog.get_filename())
        dialog.destroy()
