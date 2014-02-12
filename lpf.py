#!/usr/bin/env python
from scipy.constants import pi, c, epsilon_0, mu_0
mm = 0.001
import openems
import numpy as np

class LPF():
    def __init__(self, em, metal_name, substrate_name, z, port_length, 
                 ms_width, section, box_width,
                 priority = 9):
        self.em = em
        self.metal_name = metal_name
        self.substrate_name = substrate_name
        self.z = z # [bottom of substrate, top of substrate, top of metal] 
        self.box_length = 2.0*(port_length) + np.sum(section[:,0])
        self.box_width = box_width
        self.port_length = port_length
        self.priority = priority
        self.ms_width = ms_width
        self.section = section # pairs of x and y size of a segment
    def generate(self):
        # substrate
        start = np.array([ 0.5*self.box_length, 0.5*self.box_width, self.z[0]])
        stop  = np.array([-0.5*self.box_length, -0.5*self.box_width, self.z[1]])
        openems.Box(self.em, 'sub', self.substrate_name, 1, start, stop);

        # pads
        x0 = -0.5*self.box_length
        x1 = x0 + self.port_length
        x2 = x1 + self.ms_width
        start = np.array([x1,  0.5*self.ms_width, self.z[1]])
        stop  = np.array([x2, -0.5*self.ms_width, self.z[2]])
        l1 = openems.Box(self.em, 'line_p1', self.metal_name, self.priority, start, stop, padname = '1')
        l2 = l1.duplicate("line_p2")
        l2.mirror('x')
        l2.padname = '2'
        x = x1
        points = np.zeros((2*len(self.section),2))
        i = 0
        for s in self.section:
            points[i,0] = x
            x += s[0]
            points[i+1,0] = x
            points[i,1] = 0.5*s[1]
            points[i+1,1] = 0.5*s[1]
            i += 2
        print points
        points = np.concatenate((points, points[::-1]*[1,-1.0]))
        print points
        openems.Polygon(self.em, name = 'f',
                        material = self.metal_name,
                        priority = self.priority, 
                        points = points,
                        elevation = self.z[1:],
                        normal_direction = 'z',
                        pcb_layer = 'F.Cu',
                        pcb_width = 0.001*mm)

        # main line ports
        start = [x0, -0.5*self.ms_width, self.z[1]]
        stop  = [x1,  0.5*self.ms_width, self.z[2]]
        openems.Port(self.em, start, stop, direction='x', z=50).duplicate().mirror('x')
