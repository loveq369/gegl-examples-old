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

    def __init__(self, length):
        GObject.GObject.__init__(self)

        self.idx = 0
        self.frames = []
        for idx in range(length):
            self.frames.append(Cel())

    def go_to_frame(self, idx):
        if idx < 0 or idx > len(self.frames)-1:
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
                self.idx = len(self.frames)-1
                return True

        self.idx -= 1

        self.emit("changed")
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

        self.emit("changed")
        return True

    def get_cel(self, idx=None):
        if idx is None:
            idx = self.idx

        if idx < 0 or idx > len(self.frames)-1:
            return False

        return self.frames[idx]

    @property
    def layers_length(self):
        return 3

    @property
    def frames_separation(self):
        return 6
