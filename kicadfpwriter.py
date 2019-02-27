# Copyright (C) 2005-2019 Darrell Harmon, David Carr, Peter Baxendale, Stephen Ecob, Larry Doolittle
# GPLv3+

class Generator():
    def __init__(self, part):
        self.mirror = ""
        self.fp = "(module {} (layer F.Cu)\n".format(part)
        self.fp += "  (at 0 0)\n"
        self.fp += "  (attr smd)"
        self.fp += "  (fp_text reference U1 (at 0 -1.27) (layer F.SilkS) hide (effects (font (size 0.7 0.7) (thickness 0.127))))\n"
        self.fp += "  (fp_text value value (at 0 1.27) (layer F.SilkS) hide (effects (font (size 0.7 0.7) (thickness 0.127))))\n"

    # mm, degrees
    def add_pad(self,
                name,
                x,
                y,
                xsize=None,
                ysize=None,
                diameter=None,
                drill = 0,
                layer='F.Cu',
                mirror = "",
                shape="rect"):
        if "x" in self.mirror:
            x *= -1.0
        if "y" in self.mirror:
            y *= -1.0
        if "cir" in shape:
            shape = "circle"
            xsize = diameter
            ysize = diameter
        if "round" in shape:
            shape = "oval"
        atstring = "(at {:.6f} {:.6f})".format(x, y)
        padtype = "smd"
        layers = " (layers {})".format(layer)
        drillstring = ""
        if drill > 0:
            drillstring = " (drill {:.6f})".format(drill)
            padtype = "thru_hole"
            layers = " (layers *.Cu *.Mask)"
        self.fp += "  (pad {} {} {} {} (size {:.6f} {:.6f}){}".format(
            name, padtype, shape, atstring, xsize, ysize, drillstring)
        self.fp += layers
        self.fp += ")\n"

    def add_polygon(self, points, layer="F.Cu", width = 0.0):
        polystring = "(fp_poly (pts\n"
        for p in points:
            if "x" in self.mirror:
                p[0] *= -1.0
            if "y" in self.mirror:
                p[1] *= -1.0
            polystring += "\t(xy {:.6f} {:.6f})\n".format(p[0], p[1])
        polystring += ") (layer {}) (width {:.6f}) )\n".format(layer, width)
        self.fp += polystring

    def add_custom_pad(self, name, x, y, polygons, layer="F.Cu"):
        self.fp += "(pad {} connect custom (at {} {}) (size 0.1 0.1) (layers {})\n".format(
            name, x, y, layer)
        self.fp += "(options (clearance outline) (anchor circle))\n"
        self.fp += "(primitives\n"
        for polygon in polygons:
            polygon -= [x,y]
            self.fp += "(gr_poly (pts\n"
            for p in polygon:
                if "x" in self.mirror:
                    p[0] *= -1.0
                if "y" in self.mirror:
                    p[1] *= -1.0
                self.fp += "\t(xy {:.6f} {:.6f})\n".format(p[0], p[1])
            self.fp += ") (width 0))\n"
        self.fp += "))\n"

    def finish(self):
        self.fp += ")\n"
        return self.fp
