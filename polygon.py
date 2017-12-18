import numpy as np
import openems

class Polygon(openems.Object):
    def __init__(self,
                 material,
                 points,
                 elevation,
                 priority=1,
                 normal_direction = 'z',
                 pcb_layer = 'F.Cu',
                 pcb_width = 0.0):
        """
        Add a polygon, generally assumed to be in xy plane, but can be changed to yz or xz
        name: any unique name
        material: the name of a previously defined material
        priority: in the case of overlapping materials, the one with higher priority will be used
        points: pairs of points (xy, yz or xz) [[x1, y1], [x2, y2], ...]
        elevation: start and stop points in the normal direction
        normal_direction: optional, default = z, direction normal to the polygon - 'x', 'y' or 'z'
        """
        self.points = np.array(points)
        self.priority = priority
        self.material = material
        self.elevation = elevation
        self.pcb_layer = pcb_layer
        self.pcb_width = pcb_width
        self.normal_direction = normal_direction
        self.em = material.em
        name = self.em.get_name(None)
        self.em.objects[name] = self

    def mirror(self, axes):
        """ only correct for xy plane """
        if 'x' in axes:
            self.points[:,0] *= -1.0
        if 'y' in axes:
            self.points[:,1] *= -1.0
        return self

    def rotate_ccw_90(self):
        print("rotate_ccw_90() not supported for Polygon, ignoring")

    def offset(self, val):
        """ only correct for xy plane, 2d """
        self.points = np.array(self.points) + val[:2]
        return self

    def generate_kicad(self, g):
        if self.material.__class__.__name__ == 'Dielectric':
            return
        if self.pcb_layer == None:
            return
        g.add_polygon(points = 1000.0 * self.points, layer = self.pcb_layer, width = self.pcb_width)

    def generate_octave(self):
        height = self.elevation[1] - self.elevation[0]
        self.material.material.AddLinPoly(np.swapaxes(self.points, 0, 1),
                                          self.normal_direction,
                                          self.elevation[0],
                                          height)

    def duplicate(self):
        return Polygon(material = self.material,
                       points = self.points,
                       elevation = self.elevation,
                       priority = self.priority,
                       normal_direction = self.normal_direction,
                       pcb_layer = self.pcb_layer,
                       pcb_width = self.pcb_width)
