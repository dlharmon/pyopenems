#!/usr/bin/env python
from scipy.constants import pi, c, epsilon_0, mu_0, mil, inch
mm = 0.001
import openems
import numpy as np

class Miter():
    def __init__(self, em, metal_name, substrate_name, miter, z, port_length,
                 ms_width, box_size, priority = 9):
        self.em = em
        self.metal_name = metal_name
        self.substrate_name = substrate_name
        self.z = z # [bottom of substrate, top of substrate, top of metal] 
        self.port_length = port_length
        self.priority = priority
        self.ms_width = ms_width
        self.box_size = box_size
        self.miter = miter
    def generate(self):
        d1 = 0.5 * self.box_size
        d2 = d1 - self.port_length
        d3 = d2 - 0.2*mm
        d4 = -0.5*self.ms_width + self.miter

        # substrate
        start = np.array([ 0.5*self.box_size,  0.5*self.box_size, self.z[0]])
        stop  = np.array([-0.5*self.box_size, -0.5*self.box_size, self.z[1]])
        openems.Box(self.em, 'substrate', self.substrate_name, 1, start, stop);

        # port pads
        start = np.array([ 0.5*self.ms_width, d2, self.z[1]])
        stop  = np.array([-0.5*self.ms_width, d3, self.z[2]])
        openems.Box(self.em, 'pad_1', self.metal_name, self.priority, start, stop, padname = '1')
        start = np.array([d2,  0.5*self.ms_width, self.z[1]])
        stop  = np.array([d3, -0.5*self.ms_width, self.z[2]])
        openems.Box(self.em, 'pad_2', self.metal_name, self.priority, start, stop, padname = '2')
        
        # line
        openems.Polygon(self.em, name = 'miter_line',
                        material = self.metal_name,
                        priority = self.priority, 
                        points = np.array([[-0.5*self.ms_width, d2],
                                           [ 0.5*self.ms_width, d2],
                                           [ 0.5*self.ms_width, 0.5*self.ms_width],
                                           [ d2,  0.5*self.ms_width],
                                           [ d2, -0.5*self.ms_width],
                                           [ d4, -0.5*self.ms_width],
                                           [ -0.5*self.ms_width, d4]]),
                        elevation = self.z[1:],
                        normal_direction = 'z',
                        pcb_layer = 'F.Cu',
                        pcb_width = 0.001)
        
        # ports
        start = np.array([ 0.5*self.ms_width, d1, self.z[1]])
        stop  = np.array([-0.5*self.ms_width, d2, self.z[2]])
        openems.Port(self.em, start, stop, direction='y', z=50)
        start = np.array([d1,  0.5*self.ms_width, self.z[1]])
        stop  = np.array([d2, -0.5*self.ms_width, self.z[2]])
        openems.Port(self.em, start, stop, direction='x', z=50)
