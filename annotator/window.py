import gi  # type: ignore

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # type: ignore

from .drawing_area import DrawingArea
from .menu import MainMenu


class MainWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)
        self.set_title("Epanet Annotator")
        self.maximize()
        self.connect("destroy", Gtk.main_quit)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.box)

        drawing_area = DrawingArea(self)
        main_menu = MainMenu(self, drawing_area)
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)

        self.box.pack_start(main_menu, False, False, 0)
        self.box.pack_start(separator, False, False, 0)
        self.box.pack_start(drawing_area, True, True, 0)

    def main(self):
        self.show_all()
        Gtk.main()
