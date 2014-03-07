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

        self.idx = 0
        self.layer_idx = 0
        self.frames = [[] for x in range(layers_length)]
        for idx in range(frames_length):
            self.frames[0].append(Cel())

    def go_to_frame(self, idx):
        if idx < 0 or idx > self.frames_length-1 or idx == self.idx:
            return False

        self.idx = idx

        self.emit("changed")
        return True

    def go_previous(self, loop=False):
        if not loop:
            if self.idx == 0:
                return False
        else:
            if self.idx == 0:
                self.idx = self.frames_length-1
                return True

        self.idx -= 1

        self.emit("changed")
        return True

    def go_next(self, loop=False):
        if not loop:
            if self.idx == -1:
                return False
        else:
            if self.idx == self.frames_length-1:
                self.idx = 0
                return True

        self.idx += 1

        self.emit("changed")
        return True

    def get_cel(self, idx=None):
        if idx is None:
            idx = self.idx

        if idx < 0 or idx > self.frames_length-1:
            return False

        return self.frames[self.layer_idx][idx]

    @property
    def frames_length(self):
        return len(self.frames[0])

    @property
    def layers_length(self):
        return len(self.frames)

    @property
    def frames_separation(self):
        return 6
