import cairo

from gi.repository import Gtk

CEL_WIDTH = 55
CEL_HEIGHT = 25

BACKGROUND_COLOR = 0.9, 0.9, 0.9
SOFT_LINE_WIDTH = 0.5
STRONG_LINE_WIDTH = 1.5
SOFT_LINE_COLOR = 0.6, 0.6, 0.6
STRONG_LINE_COLOR = 0.3, 0.3, 0.3

class XSheetWidget(Gtk.DrawingArea):
    def __init__(self, xsheet):
        Gtk.DrawingArea.__init__(self)

        self._xsheet = xsheet
        self.pixbuf = None

        self.connect('draw', self.draw_cb)
        self.connect('configure-event', self.configure_event_cb)
        #self._xsheet.connect('changed', self.xsheet_changed_cb)
        self.set_size_request(CEL_WIDTH * xsheet.layers_length, 0)

    def configure_event_cb(self, widget, event, data=None):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()

        # Destroy previous buffer
        if self.pixbuf is not None:
            self.pixbuf.finish()
            self.pixbuf = None

        # Create a new buffer
        self.pixbuf = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)

        return False

    def xsheet_changed_cb(self, xsheet):
        print("changed")

    def draw_cb(self, widget, context):
        if self.pixbuf is None:
            print('No buffer to paint')
            return False

        drawing_context = cairo.Context(self.pixbuf)

        self.draw_background(drawing_context)
        self.draw_grid(drawing_context)

        context.set_source_surface(self.pixbuf, 0.0, 0.0)
        context.paint()

    def draw_background(self, context):
        width = context.get_target().get_width()
        height = context.get_target().get_height()
        context.set_source_rgb(*BACKGROUND_COLOR)
        context.rectangle(0, 0, width, height)
        context.fill()

    def draw_grid_horizontal(self, context):
        x1 = 0
        x2 = CEL_WIDTH * self._xsheet.layers_length
        for i in range(24):
            if i % self._xsheet.frames_separation:
                context.set_line_width(SOFT_LINE_WIDTH)
                context.set_source_rgb(*SOFT_LINE_COLOR)
            else:
                context.set_line_width(STRONG_LINE_WIDTH)
                context.set_source_rgb(*STRONG_LINE_COLOR)

            y = i * CEL_HEIGHT
            context.move_to(x1, y)
            context.line_to(x2, y)
            context.stroke()

    def draw_grid_vertical(self, context):
        context.set_source_rgb(*SOFT_LINE_COLOR)
        context.set_line_width(SOFT_LINE_WIDTH)

        y1 = 0
        y2 = 24 * CEL_HEIGHT
        for i in range(self._xsheet.layers_length):
            x = i * CEL_WIDTH
            context.move_to(x, y1)
            context.line_to(x, y2)
        context.stroke()

    def draw_grid(self, context):
        self.draw_grid_horizontal(context)
        self.draw_grid_vertical(context)
