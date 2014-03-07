from gi.repository import GObject

from lib import tiledsurface

class Cel(object):
    def __init__(self):
        self.surface = tiledsurface.GeglSurface()
        self.surface_node = self.surface.get_node()


class XSheet(GObject.GObject):
    __gsignals__ = {
        "changed": (GObject.SignalFlags.RUN_FIRST, None, []),
    }

    def __init__(self, frames_length=24, layers_length=3):
        GObject.GObject.__init__(self)

        self.frame_idx = 0
        self.layer_idx = 0
        self.frames = [[] for x in range(layers_length)]
        for frame_idx in range(frames_length):
            for layer_idx in range(layers_length):
                self.frames[layer_idx].append(Cel())

    def go_to_frame(self, frame_idx):
        if frame_idx < 0 or frame_idx > self.frames_length-1 or frame_idx == self.frame_idx:
            return False

        self.frame_idx = frame_idx

        self.emit("changed")
        return True

    def go_previous(self, loop=False):
        if not loop:
            if self.frame_idx == 0:
                return False
        else:
            if self.frame_idx == 0:
                self.frame_idx = self.frames_length-1
                return True

        self.frame_idx -= 1

        self.emit("changed")
        return True

    def go_next(self, loop=False):
        if not loop:
            if self.frame_idx == -1:
                return False
        else:
            if self.frame_idx == self.frames_length-1:
                self.frame_idx = 0
                return True

        self.frame_idx += 1

        self.emit("changed")
        return True

    def get_cel(self, frame_idx=None, layer_idx=None):
        if frame_idx is None:
            frame_idx = self.frame_idx

        if layer_idx is None:
            layer_idx = self.layer_idx

        if frame_idx < 0 or frame_idx > self.frames_length-1:
            return False

        return self.frames[layer_idx][frame_idx]

    def get_cel_relative(self, frame_diff=0, layer_diff=0):
        frame_idx = self.frame_idx + frame_diff
        layer_idx = self.layer_idx + layer_diff
        return self.get_cel(frame_idx, layer_idx)

    @property
    def frames_length(self):
        return len(self.frames[0])

    @property
    def layers_length(self):
        return len(self.frames)

    @property
    def frames_separation(self):
        return 6
