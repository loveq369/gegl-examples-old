import math
import cairo

from gi.repository import Gtk

CEL_WIDTH = 55
CEL_HEIGHT = 25

SOFT_LINE_WIDTH = 0.2
STRONG_LINE_WIDTH = 0.5
ELEMENT_CEL_RADIUS = 3

def _get_cairo_color(gdk_color):
    return (float(gdk_color.red), float(gdk_color.green), float(gdk_color.blue))


class XSheetWidget(Gtk.DrawingArea):
    def __init__(self, xsheet):
        Gtk.DrawingArea.__init__(self)

        self._background_color = self.get_style_context().lookup_color('theme_bg_color')[1]
        self._selected_color = self.get_style_context().lookup_color('theme_selected_bg_color')[1]
        self._fg_color = self.get_style_context().lookup_color('theme_fg_color')[1]

        self._xsheet = xsheet
        self._pixbuf = None

        self.connect('draw', self.draw_cb)
        self.connect('configure-event', self.configure_event_cb)
        self._xsheet.connect('changed', self.xsheet_changed_cb)
        self.set_size_request(CEL_WIDTH * xsheet.layers_length, 0)

    def configure_event_cb(self, widget, event, data=None):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()

        # Destroy previous buffer
        if self._pixbuf is not None:
            self._pixbuf.finish()
            self._pixbuf = None

        # Create a new buffer
        self._pixbuf = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)

        return False

    def xsheet_changed_cb(self, xsheet):
        self.queue_draw()

    def draw_cb(self, widget, context):
        if self._pixbuf is None:
            print('No buffer to paint')
            return False

        drawing_context = cairo.Context(self._pixbuf)

        self.draw_background(drawing_context)
        self.draw_selected_row(drawing_context)
        self.draw_grid(drawing_context)
        self.draw_elements(drawing_context)

        context.set_source_surface(self._pixbuf, 0.0, 0.0)
        context.paint()

    def draw_background(self, context):
        width = context.get_target().get_width()
        height = context.get_target().get_height()
        context.set_source_rgb(*_get_cairo_color(self._background_color))
        context.rectangle(0, 0, width, height)
        context.fill()

    def draw_selected_row(self, context):
        for i in range(len(self._xsheet.frames)):
            if i == self._xsheet.idx:
                y = i * CEL_HEIGHT
                width = CEL_WIDTH * self._xsheet.layers_length
                context.set_source_rgb(*_get_cairo_color(self._selected_color))
                context.rectangle(0, y, width, CEL_HEIGHT)
                context.fill()
                break

    def draw_grid_horizontal(self, context):
        x1 = 0
        x2 = CEL_WIDTH * self._xsheet.layers_length
        context.set_source_rgb(*_get_cairo_color(self._fg_color))
        for i in range(len(self._xsheet.frames) + 1):
            if i % self._xsheet.frames_separation:
                context.set_line_width(SOFT_LINE_WIDTH)
            else:
                context.set_line_width(STRONG_LINE_WIDTH)

            y = i * CEL_HEIGHT
            context.move_to(x1, y)
            context.line_to(x2, y)
            context.stroke()

    def draw_grid_vertical(self, context):
        context.set_source_rgb(*_get_cairo_color(self._fg_color))
        context.set_line_width(SOFT_LINE_WIDTH)

        y1 = 0
        y2 = 24 * CEL_HEIGHT
        for i in range(self._xsheet.layers_length):
            x = i * CEL_WIDTH
            context.move_to(x, y1)
            context.line_to(x, y2)
        context.stroke()

    def draw_grid(self, context):
        self.draw_grid_vertical(context)
        self.draw_grid_horizontal(context)

    def draw_elements(self, context):
        context.set_source_rgb(*_get_cairo_color(self._fg_color))
        context.arc(CEL_WIDTH/2, CEL_HEIGHT/2, ELEMENT_CEL_RADIUS, 0, 2 * math.pi);
        context.fill()
