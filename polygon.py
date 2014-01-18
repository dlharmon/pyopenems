#!/usr/bin/env python

import numpy as np
import openems

np.set_printoptions(precision=8)

class Polygon(openems.Object):
    def __init__(self, em, name, material, priority, points, elevation, normal_direction = 'z', pcb_layer = 'F.Cu', pcb_width = 0.0): 
        """
        Add a polygon, generally assumed to be in xy plane, but can be changed to yz or xz
        name: any unique name
        material: the name of a previously defined material
        priority: in the case of overlapping materials, the one with higher priority will be used
        points: pairs of points (xy, yz or xz) [[x1, y1], [x2, y2], ...]
        elevation: start and stop points in the normal direction
        normal_direction: optional, default = z, direction normal to the polygon - 'x', 'y' or 'z'
        """
        self.points = points
        self.priority = priority
        self.material = material
        self.elevation = elevation
        self.pcb_layer = pcb_layer
        self.pcb_width = pcb_width
        self.normal_direction = normal_direction
        self.em = em
        em.objects[name] = self

    def mirror(self, axes):
        """ only correct for xy plane """
        if 'x' in axes:
            self.points = np.array(self.points) * [-1.0, 1.0]
        if 'y' in axes:
            self.points = np.array(self.points) * [1.0, -1.0]
    
    def rotate_ccw_90(self):
        print "rotate_ccw_90() not supported for Polygon, ignoring"
        
    def offset(self, val):
        """ only correct for xy plane, 2d """
        self.points = np.array(self.points) + val[:2]

    def generate_kicad(self, g):
        print "gen kicad for poly called"
        if self.em.materials[self.material].__class__.__name__ == 'Dielectric':
            return
        if self.pcb_layer == None:
            return
        print "gen kicad for poly running"
        g.add_polygon(points = 1000.0 * self.points, layer = self.pcb_layer, width = self.pcb_width)

    def generate_octave(self):
        octave = ""
        n = 1
        for p in self.points:
            octave += "p(1,{}) = {}; p(2,{}) = {};\n".format(n, p[0], n, p[1])
            n += 1
        height = self.elevation[1] - self.elevation[0]
        octave += "CSX = AddLinPoly( CSX, '{}', {}, '{}', {}, p, {});\n".format(self.material, self.priority, self.normal_direction, round(self.elevation[0],8), 0.8*round(height, 8))
        return octave
