import math
import cairo

from gi.repository import Gtk
from gi.repository import Gdk

NUMBERS_WIDTH = 45.0
NUMBERS_MARGIN = 5.0
CEL_WIDTH = 55.0
CEL_HEIGHT = 25.0

SOFT_LINE_WIDTH = 0.2
STRONG_LINE_WIDTH = 0.5
ELEMENT_CEL_RADIUS = 3.0

def _get_cairo_color(gdk_color):
    return (float(gdk_color.red), float(gdk_color.green), float(gdk_color.blue))


class XSheetWidget(Gtk.DrawingArea):
    def __init__(self, xsheet):
        Gtk.DrawingArea.__init__(self)

        self._background_color = self.get_style_context().lookup_color('theme_bg_color')[1]
        self._selected_color = self.get_style_context().lookup_color('theme_selected_bg_color')[1]
        self._fg_color = self.get_style_context().lookup_color('theme_fg_color')[1]
        self._selected_fg_color = self.get_style_context().lookup_color('theme_selected_fg_color')[1]

        self._xsheet = xsheet
        self._pixbuf = None
        self._button_pressed = False

        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.SCROLL_MASK)

        self.connect('draw', self.draw_cb)
        self.connect('configure-event', self.configure_event_cb)
        self.connect("motion-notify-event", self.motion_notify_cb)
        self.connect("button-press-event", self.button_press_cb)
        self.connect("button-release-event", self.button_release_cb)

        self._xsheet.connect('changed', self.xsheet_changed_cb)
        widget_width = NUMBERS_WIDTH + CEL_WIDTH * xsheet.layers_length
        self.set_size_request(widget_width, 0)

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
        self.draw_numbers(drawing_context)
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
                width = context.get_target().get_width()
                context.set_source_rgb(*_get_cairo_color(self._selected_color))
                context.rectangle(0, y, width, CEL_HEIGHT)
                context.fill()
                break

    def draw_grid_horizontal(self, context):
        width = context.get_target().get_width()
        context.set_source_rgb(*_get_cairo_color(self._fg_color))
        for i in range(len(self._xsheet.frames) + 1):
            if i % self._xsheet.frames_separation:
                context.set_line_width(SOFT_LINE_WIDTH)
            else:
                context.set_line_width(STRONG_LINE_WIDTH)

            y = i * CEL_HEIGHT
            context.move_to(0, y)
            context.line_to(width, y)
            context.stroke()

    def draw_grid_vertical(self, context):
        context.set_source_rgb(*_get_cairo_color(self._fg_color))
        context.set_line_width(SOFT_LINE_WIDTH)

        y1 = 0
        y2 = 24 * CEL_HEIGHT

        context.move_to(NUMBERS_WIDTH, y1)
        context.line_to(NUMBERS_WIDTH, y2)

        for i in range(self._xsheet.layers_length):
            x = NUMBERS_WIDTH + i * CEL_WIDTH
            context.move_to(x, y1)
            context.line_to(x, y2)
        context.stroke()

    def draw_grid(self, context):
        self.draw_grid_vertical(context)
        self.draw_grid_horizontal(context)

    def draw_numbers(self, context):
        context.select_font_face("sans-serif",
                                 cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        context.set_font_size(13)

        for i in range(len(self._xsheet.frames)):
            if i == self._xsheet.idx:
                context.set_source_rgb(*_get_cairo_color(self._selected_fg_color))
            else:
                context.set_source_rgb(*_get_cairo_color(self._fg_color))

            text = str(i+1).zfill(3)
            x, y, width, height, dx, dy = context.text_extents(text)
            context.move_to(NUMBERS_WIDTH - width - NUMBERS_MARGIN, (i * CEL_HEIGHT) + CEL_HEIGHT/2 + height/2)
            context.show_text(text)

    def draw_elements(self, context):
        i = 0
        if i == self._xsheet.idx:
            context.set_source_rgb(*_get_cairo_color(self._selected_fg_color))
        else:
            context.set_source_rgb(*_get_cairo_color(self._fg_color))

        context.arc(NUMBERS_WIDTH + CEL_WIDTH/2, CEL_HEIGHT/2, ELEMENT_CEL_RADIUS, 0, 2 * math.pi);
        context.fill()

    def _get_frame_from_point(self, x, y):
        return int(y / CEL_HEIGHT)

    def button_press_cb(self, widget, event):
        self._button_pressed = True

    def button_release_cb(self, widget, event):
        self._button_pressed = False

        idx = self._get_frame_from_point(event.x, event.y)
        self._xsheet.go_to_frame(idx)

    def motion_notify_cb(self, widget, event):
        x, y = event.x, event.y
        idx = self._get_frame_from_point(event.x, event.y)
        if self._button_pressed:
            self._xsheet.go_to_frame(idx)
