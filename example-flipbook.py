#!/usr/bin/env python
import sys, os.path

import gi
from gi.repository import Gegl, Gtk, Gdk, GObject
from gi.repository import GeglGtk3 as GeglGtk

from lib import tiledsurface, brush

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


class Cel(object):
    def __init__(self):
        self.surface = tiledsurface.GeglSurface()
        self.surface_node = self.surface.get_node()


class Timeline(object):
    def __init__(self, length):
        self.idx = 0
        self.frames = []
        for idx in range(length):
            self.frames.append(Cel())

    def go_previous(self, loop=False):
        if not loop:
            if self.idx == 0:
                return False
        else:
            if self.idx == 0:
                self.idx = len(self.frames)-1
                return True

        self.idx -= 1
        return True

    def go_next(self, loop=False):
        if not loop:
            if self.idx == len(self.frames)-1:
                return False
        else:
            if self.idx == len(self.frames)-1:
                self.idx = 0
                return True

        self.idx += 1
        return True

    def get_cel(self, idx=None):
        if idx is None:
            idx = self.idx

        if idx < 0 or idx > len(self.frames)-1:
            return False

        return self.frames[idx]


class FlipbookApp(object):
    def __init__(self):
        brush_file = open('brushes/classic/charcoal.myb')
        brush_info = brush.BrushInfo(brush_file.read())
        brush_info.set_color_rgb((0.0, 0.0, 0.0))
        self.brush = brush.Brush(brush_info)

        self.button_pressed = False
        self.last_event = (0.0, 0.0, 0.0) # (x, y, time)

        self.surface = None
        self.surface_node = None

        self.play_hid = None

        self.timeline = Timeline(10)
        self.update_surface()

        self.create_graph()
        self.init_ui()


    def create_graph(self):
        self.graph = Gegl.Node()

        self.background_node = self.graph.create_child("gegl:rectangle")
        self.background_node.set_property('color', Gegl.Color.new("#fff"))

        self.over = self.graph.create_child("gegl:over")
        self.over_prev1 = self.graph.create_child("gegl:over")
        self.opacity_prev1 = self.graph.create_child("gegl:opacity")
        self.opacity_prev1.set_property('value', 0.3)
        self.over_prev2 = self.graph.create_child("gegl:over")
        self.opacity_prev2 = self.graph.create_child("gegl:opacity")
        self.opacity_prev2.set_property('value', 0.3)

        self.background_node.connect_to("output", self.over, "input")

        self.over_prev1.connect_to("output", self.over, "aux")
        self.opacity_prev1.connect_to("output", self.over_prev1, "aux")
        self.over_prev2.connect_to("output", self.opacity_prev1, "input")
        self.opacity_prev2.connect_to("output", self.over_prev2, "aux")

        self.update_graph()

    def update_graph(self):
        self.surface_node.connect_to("output", self.over_prev1, "input")

        prev_cel1 = self.timeline.get_cel(self.timeline.idx-1)
        if prev_cel1:
            prev_surface1 = prev_cel1.surface
            prev_surface_node1 = prev_cel1.surface_node
            prev_surface_node1.connect_to("output", self.over_prev2, "input")

        prev_cel2 = self.timeline.get_cel(self.timeline.idx-2)
        if prev_cel2:
            prev_surface2 = prev_cel2.surface
            prev_surface_node2 = prev_cel2.surface_node
            prev_surface_node2.connect_to("output", self.opacity_prev2, "input")

        # debug
        # print_connections(self.over)

    def init_ui(self):
        window = Gtk.Window()
        window.connect("destroy", self.destroy_cb)
        window.connect("size-allocate", self.size_allocate_cb)
        window.connect("key-release-event", self.key_release_cb)

        top_box = Gtk.VBox()
        window.add(top_box)

        event_box = Gtk.EventBox()
        event_box.connect("motion-notify-event", self.motion_to_cb)
        event_box.connect("button-press-event", self.button_press_cb)
        event_box.connect("button-release-event", self.button_release_cb)
        top_box.pack_start(event_box, expand=True, fill=True, padding=0)

        view_widget = GeglGtk.View()
        view_widget.set_node(self.over)
        view_widget.set_autoscale_policy(GeglGtk.ViewAutoscale.DISABLED)
        view_widget.set_size_request(800, 400)
        event_box.add(view_widget)

        window.show_all()

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

    def update_surface(self):
        cel = self.timeline.get_cel()
        self.surface = cel.surface
        self.surface_node = cel.surface_node

    def go_previous(self, loop=False):
        changed = self.timeline.go_previous(loop)
        if changed:
            self.update_surface()
            self.update_graph()

        return changed

    def go_next(self, loop=False):
        changed = self.timeline.go_next(loop)
        if changed:
            self.update_surface()
            self.update_graph()

        return changed

    def toggle_play_stop(self):
        if self.play_hid == None:
            self.play_hid = GObject.timeout_add(42, self.go_next, True)
        else:
            GObject.source_remove(self.play_hid)
            self.play_hid = None

    def key_release_cb(self, widget, event):
        if event.keyval == Gdk.KEY_Left:
            self.go_previous()
        elif event.keyval == Gdk.KEY_Right:
            self.go_next()
        elif event.keyval == Gdk.KEY_p:
            self.toggle_play_stop()

if __name__ == '__main__':
    Gegl.init([])
    Gtk.init([])

    app = FlipbookApp()
    app.run()
