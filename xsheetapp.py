#!/usr/bin/env python
import sys, os.path

import gi
from gi.repository import Gegl, Gtk, Gdk, GObject
from gi.repository import GeglGtk3 as GeglGtk

from lib import brush

from xsheet import XSheet
from xsheetwidget import XSheetWidget

def print_connections(node):
    def print_node(node, i=0):
        print("  " * i + node.get_operation())
        # FIMXE use gegl_operation_list_properties if that is in the
        # introspection bindings
        for input_pad in ['input', 'aux']:
            connected_node = node.get_producer(input_pad, None)
            if connected_node is not None:
                print_node(connected_node, i+1)

    print_node(node)
    print("")


class XSheetApp(GObject.GObject):
    def __init__(self):
        GObject.GObject.__init__(self)

        brush_file = open('brushes/classic/charcoal.myb')
        brush_info = brush.BrushInfo(brush_file.read())
        brush_info.set_color_rgb((0.0, 0.0, 0.0))
        self.default_eraser = brush_info.get_base_value("eraser")
        self.default_radius = brush_info.get_base_value("radius_logarithmic")
        self.brush = brush.Brush(brush_info)

        self.button_pressed = False
        self.last_event = (0.0, 0.0, 0.0) # (x, y, time)

        self.eraser_on = False
        self.onionskin_on = True

        self.surface = None
        self.surface_node = None

        self.play_hid = None

        self.xsheet = XSheet(24 * 4)
        self.xsheet.connect('changed', self.xsheet_changed_cb)

        self.update_surface()

        self.create_graph()
        self.init_ui()


    def create_graph(self):
        self.graph = Gegl.Node()

        self.background_node = self.graph.create_child("gegl:rectangle")
        self.background_node.set_property('color', Gegl.Color.new("#fff"))

        self.over = self.graph.create_child("gegl:over")
        self.over2 = self.graph.create_child("gegl:over")
        self.opacity_prev1 = self.graph.create_child("gegl:opacity")
        self.opacity_prev1.set_property('value', 0.5)
        self.over3 = self.graph.create_child("gegl:over")
        self.opacity_prev2 = self.graph.create_child("gegl:opacity")
        self.opacity_prev2.set_property('value', 0.5)

        self.background_node.connect_to("output", self.over, "input")
        self.over2.connect_to("output", self.over, "aux")
        self.opacity_prev1.connect_to("output", self.over2, "aux")
        self.over3.connect_to("output", self.opacity_prev1, "input")
        self.opacity_prev2.connect_to("output", self.over3, "aux")

        self.update_graph()

    def update_graph(self):
        self.surface_node.connect_to("output", self.over2, "input")

        if not self.onionskin_on:
            return

        prev_cel1 = self.xsheet.get_cel(self.xsheet.idx-1)
        if prev_cel1:
            prev_surface_node1 = prev_cel1.surface_node
            prev_surface_node1.connect_to("output", self.over3, "input")
        else:
            self.over3.disconnect("input")

        prev_cel2 = self.xsheet.get_cel(self.xsheet.idx-2)
        if prev_cel2:
            prev_surface_node2 = prev_cel2.surface_node
            prev_surface_node2.connect_to("output", self.opacity_prev2, "input")
        else:
            self.opacity_prev2.disconnect("input")

        # debug
        # print_connections(self.over)

    def init_ui(self):
        window = Gtk.Window()
        window.props.title = "Flipbook"
        window.connect("destroy", self.destroy_cb)
        window.connect("size-allocate", self.size_allocate_cb)
        window.connect("key-press-event", self.key_press_cb)
        window.connect("key-release-event", self.key_release_cb)
        window.show()

        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        window.add(top_box)
        top_box.show()

        event_box = Gtk.EventBox()
        event_box.connect("motion-notify-event", self.motion_to_cb)
        event_box.connect("button-press-event", self.button_press_cb)
        event_box.connect("button-release-event", self.button_release_cb)
        top_box.pack_start(event_box, expand=True, fill=True, padding=0)
        event_box.show()

        view_widget = GeglGtk.View()
        view_widget.set_node(self.over)
        view_widget.set_autoscale_policy(GeglGtk.ViewAutoscale.DISABLED)
        view_widget.set_size_request(800, 400)
        event_box.add(view_widget)
        view_widget.show()

        xsheet_widget = XSheetWidget(self.xsheet)
        top_box.pack_start(xsheet_widget, expand=False, fill=False, padding=0)
        xsheet_widget.show()

    def run(self):
        return Gtk.main()

    def destroy_cb(self, *ignored):
        Gtk.main_quit()

    def size_allocate_cb(self, widget, allocation):
        self.background_node.set_property("width", allocation.width)
        self.background_node.set_property("height", allocation.height)

    def motion_to_cb(self, widget, event):
        (x, y, time) = event.x, event.y, event.time

        pressure = 0.5
        dtime = (time - self.last_event[2])/1000.0
        if self.button_pressed:
            self.surface.begin_atomic()
            self.brush.stroke_to(self.surface.backend, x, y, pressure, 0.0, 0.0, dtime)
            self.surface.end_atomic()

        self.last_event = (x, y, time)

    def button_press_cb(self, widget, event):
        self.button_pressed = True

    def button_release_cb(self, widget, event):
        self.button_pressed = False
        self.brush.reset()

    def xsheet_changed_cb(self, xsheet):
        self.update_surface()
        self.update_graph()

    def update_surface(self):
        cel = self.xsheet.get_cel()
        self.surface = cel.surface
        self.surface_node = cel.surface_node

    def go_previous(self, loop=False):
        changed = self.xsheet.go_previous(loop)
        return changed

    def go_next(self, loop=False):
        changed = self.xsheet.go_next(loop)
        return changed

    def toggle_play_stop(self):
        if self.play_hid == None:
            self.play_hid = GObject.timeout_add(42, self.go_next, True)
        else:
            GObject.source_remove(self.play_hid)
            self.play_hid = None

    def toggle_onionskin(self):
        self.onionskin_on = not self.onionskin_on

        if self.onionskin_on:
            self.opacity_prev1.connect_to("output", self.over2, "aux")
        else:
            self.over2.disconnect("aux")

        self.update_graph()

    def toggle_eraser(self):
        self.eraser_on = not self.eraser_on

        if self.eraser_on:
            self.brush.brushinfo.set_base_value("eraser", 1.0)
            self.brush.brushinfo.set_base_value("radius_logarithmic",
                                                self.default_radius * 3)
        else:
            self.brush.brushinfo.set_base_value("eraser", self.default_eraser)
            self.brush.brushinfo.set_base_value("radius_logarithmic",
                                                self.default_radius)

    def key_press_cb(self, widget, event):
        if event.keyval == Gdk.KEY_Up:
            self.go_previous()
        elif event.keyval == Gdk.KEY_Down:
            self.go_next()

    def key_release_cb(self, widget, event):
        if event.keyval == Gdk.KEY_p:
            self.toggle_play_stop()
        elif event.keyval == Gdk.KEY_o:
            self.toggle_onionskin()
        elif event.keyval == Gdk.KEY_e:
            self.toggle_eraser()
        elif event.keyval == Gdk.KEY_BackSpace:
            # FIXME, needs to be done in gegl backend
            self.surface.clear()

if __name__ == '__main__':
    Gegl.init([])
    Gtk.init([])

    app = XSheetApp()
    app.run()
