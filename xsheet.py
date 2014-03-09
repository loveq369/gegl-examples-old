from gi.repository import GObject

from lib import tiledsurface

from cellist import CelList


class Cel(object):
    def __init__(self):
        self.surface = tiledsurface.GeglSurface()
        self.surface_node = self.surface.get_node()


class XSheet(GObject.GObject):
    __gsignals__ = {
        "frame-changed": (GObject.SignalFlags.RUN_FIRST, None, []),
        "layer-changed": (GObject.SignalFlags.RUN_FIRST, None, []),
    }

    def __init__(self, frames_length=24, layers_length=3):
        GObject.GObject.__init__(self)

        self._frames_length = frames_length
        self.frame_idx = 0
        self.layer_idx = 0
        self.layers = [CelList() for x in range(layers_length)]

    def go_to_frame(self, frame_idx):
        if frame_idx < 0 or frame_idx > self.frames_length-1 or frame_idx == self.frame_idx:
            return False

        self.frame_idx = frame_idx

        self.emit("frame-changed")
        return True

    def previous_frame(self, loop=False):
        if not loop:
            if self.frame_idx == 0:
                return False
        else:
            if self.frame_idx == 0:
                self.frame_idx = self.frames_length-1
                return True

        self.frame_idx -= 1

        self.emit("frame-changed")
        return True

    def next_frame(self, loop=False):
        if not loop:
            if self.frame_idx == self.frames_length-1:
                return False
        else:
            if self.frame_idx == self.frames_length-1:
                self.frame_idx = 0
                return True

        self.frame_idx += 1

        self.emit("frame-changed")
        return True

    def previous_layer(self):
        if self.layer_idx == 0:
            return False

        self.layer_idx -= 1

        self.emit("layer-changed")
        return True

    def next_layer(self):
        if self.layer_idx == self.layers_length-1:
            return False

        self.layer_idx += 1

        self.emit("layer-changed")
        return True

    def get_cel(self, frame_idx=None, layer_idx=None):
        if frame_idx is None:
            frame_idx = self.frame_idx

        if layer_idx is None:
            layer_idx = self.layer_idx

        return self.layers[layer_idx][frame_idx]

    def add_cel(self, frame_idx=None, layer_idx=None):
        if frame_idx is None:
            frame_idx = self.frame_idx

        if layer_idx is None:
            layer_idx = self.layer_idx

        self.layers[layer_idx][frame_idx] = Cel()

        self.emit("frame-changed")

    def get_cel_relative(self, frame_diff=0, layer_diff=0):
        frame_idx = self.frame_idx + frame_diff
        layer_idx = self.layer_idx + layer_diff
        return self.get_cel(frame_idx, layer_idx)

    @property
    def frames_length(self):
        return self._frames_length

    @property
    def layers_length(self):
        return len(self.layers)

    @property
    def frames_separation(self):
        return 6
