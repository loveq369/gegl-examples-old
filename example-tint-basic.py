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


class TintApp(object):
    def __init__(self):
        self.create_graph()
        self.init_ui()

    def create_graph(self):
        self.graph = Gegl.Node()

        self.add = self.graph.create_child("gegl:add")

        self.color = self.graph.create_child("gegl:rectangle")
        self.color.set_property('color', Gegl.Color.new("#f00"))

        self.image_node = self.graph.create_child("gegl:load")
        self.image_node.set_property('path', 'test.png')

        self.color.connect_to("output", self.add, "aux")
        self.image_node.connect_to("output", self.add, "input")

    def init_ui(self):
        window = Gtk.Window()
        window.connect("destroy", self.destroy_cb)
        window.connect("size-allocate", self.size_allocate_cb)

        view_widget = GeglGtk.View()
        view_widget.set_node(self.add)
        view_widget.set_autoscale_policy(GeglGtk.ViewAutoscale.DISABLED)
        view_widget.set_size_request(800, 400)
        window.add(view_widget)

        window.show_all()

    def run(self):
        return Gtk.main()

    def destroy_cb(self, *ignored):
        Gtk.main_quit()

    def size_allocate_cb(self, widget, allocation):
        self.color.set_property("width", allocation.width)
        self.color.set_property("height", allocation.height)

if __name__ == '__main__':
    Gegl.init([])
    Gtk.init([])

    app = TintApp()
    app.run()
