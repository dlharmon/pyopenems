#!/usr/bin/env python
from scipy.constants import pi, c, epsilon_0, mu_0, mil, inch
mm = 0.001
import openems
import numpy as np

class Coupler():
    def __init__(self, em, metal_name, substrate_name, miter, z, port_length,
                 box_length, ms_width, coupler_gap, cpw_gap, box_y,
                 coupler_length, coupler_width, priority = 9,
                 pin_length = 0.2*mm, main_line_width = None,
                 feed_coupled=False,
                 dual=False): # if dual, coupler_width should = ms_width, cpw_gap = None
        self.em = em
        self.metal_name = metal_name
        self.substrate_name = substrate_name
        self.z = z # [bottom of substrate, top of substrate, top of metal]
        self.box_length = box_length
        self.box_y = box_y
        self.port_length = port_length
        self.priority = priority
        self.ms_width = ms_width
        self.coupler_gap = coupler_gap
        self.cpw_gap = cpw_gap
        self.coupler_length = coupler_length
        self.coupler_width = coupler_width
        self.miter = miter
        self.pin_length = pin_length
        if main_line_width == None:
            self.main_line_width = coupler_width
        else:
            self.main_line_width = main_line_width
        self.feed_coupled = feed_coupled
        self.dual = dual

    def generate(self):
        # substrate
        start = np.array([ 0.5*self.box_length, self.box_y[0], self.z[0]])
        stop  = np.array([-0.5*self.box_length, self.box_y[1], self.z[1]])
        openems.Box(self.em,
                    'coupler_sub',
                    self.substrate_name,
                    1,
                    start,
                    stop);
        # through line ends (pads)
        x0 = -0.5*self.box_length
        x1 = x0 + self.port_length
        start = np.array([x1,                    0.5*self.ms_width, self.z[1]])
        stop  = np.array([x1 + self.pin_length, -0.5*self.ms_width, self.z[2]])
        l1 = openems.Box(self.em,
                         'line_p1',
                         self.metal_name,
                         self.priority,
                         start,
                         stop,
                         padname = '1')
        l2 = l1.duplicate("line_p2")
        l2.mirror('x')
        l2.padname = '2'
        xc1 = -0.5*self.coupler_length - 0.5*self.ms_width
        xc2 = xc1 + self.ms_width
        xm = xc1 + self.miter
        # through line middle
        diff = 0.5 * np.abs(self.ms_width - self.main_line_width)
        ppoints = np.array(
            [[     x1,  0.5*self.ms_width],
             [-1.0*x1,  0.5*self.ms_width],
             [-1.0*x1, -0.5*self.ms_width],
             [-1.0*xm + diff, -0.5*self.ms_width],
             [-1.0*xm - diff,  0.5*self.ms_width - self.main_line_width],
             [ 1.0*xm + diff,  0.5*self.ms_width - self.main_line_width],
             [     xm - diff, -0.5*self.ms_width],
             [     x1,  -0.5*self.ms_width]])
        openems.Polygon(self.em, name = 'throughline',
                        material = self.metal_name,
                        priority = self.priority,
                        points = ppoints,
                        elevation = self.z[1:],
                        normal_direction = 'z',
                        pcb_layer = 'F.Cu',
                        pcb_width = 0.001*mm)
        # coupled line
        yc0 = 0.5*self.ms_width + self.coupler_gap
        yc1 = yc0 + self.coupler_width
        yc4 = self.box_y[1]
        yc3 = yc4 - self.port_length
        yc2 = yc3 - self.pin_length
        # pads
        start = np.array([xc1, yc2, self.z[1]])
        stop  = np.array([xc2, yc3, self.z[2]])
        l3 = openems.Box(self.em,
                         'line_p3',
                         self.metal_name,
                         self.priority,
                         start,
                         stop,
                         padname = '3')
        l4 = l3.duplicate("line_p4")
        l4.mirror('x')
        l4.padname = '4'
        if self.dual:
            l5 = l3.duplicate().mirror('y')
            l5.padname = '5'
            l6 = l4.duplicate().mirror('y')
            l6.padname = '6'

        p = openems.Polygon(self.em, name = 'coupledline',
                        material = self.metal_name,
                        priority = self.priority,
                        points = np.array([[xc1 + self.miter,  yc0],
                                           [xc1, yc0 + self.miter],
                                           [xc1, yc3],
                                           [xc2, yc3],
                                           [xc2, yc1],
                                           [-1.0*xc2, yc1],
                                           [-1.0*xc2, yc3],
                                           [-1.0*xc1, yc3],
                                           [-1.0*xc1, yc0 + self.miter],
                                           [-1.0*xc1 - self.miter, yc0]]),
                        elevation = self.z[1:],
                        normal_direction = 'z',
                        pcb_layer = 'F.Cu',
                        pcb_width = 0.001*mm)

        if self.dual:
            p.duplicate().mirror('y')

        if not self.feed_coupled:
            # main line ports
            start = [x0, -0.5*self.ms_width, self.z[1]]
            stop  = [x1,  0.5*self.ms_width, self.z[2]]
            openems.Port(self.em,
                         start,
                         stop,
                         direction='x',
                         z=50).duplicate().mirror('x')
        # coupled line ports
        start = [xc1, yc4, self.z[1]]
        stop  = [xc2, yc3, self.z[2]]
        cp1 = openems.Port(self.em,
                           start,
                           stop,
                           direction='y',
                           z=50)
        cp2 = cp1.duplicate().mirror('x')
        if self.dual:
            cp1.duplicate().mirror('y')
            cp2.duplicate().mirror('y')

        if self.feed_coupled:
            # main line ports
            start = [x0, -0.5*self.ms_width, self.z[1]]
            stop  = [x1,  0.5*self.ms_width, self.z[2]]
            openems.Port(self.em,
                         start,
                         stop,
                         direction='x',
                         z=50).duplicate().mirror('x')
        # ground via
        if self.cpw_gap != None:
            start = np.array([-0.5*self.box_length,
                              -0.5*self.ms_width - self.cpw_gap,
                              self.z[0]])
            stop  = np.array([ 0.5*self.box_length,
                               self.box_y[0],
                               self.z[2]])
            openems.Box(self.em,
                        'ground_lower_top',
                        self.metal_name,
                        self.priority,
                        start, stop,
                        padname = None)
            start = np.array([-0.5*self.box_length,
                              0.5*self.ms_width + self.cpw_gap,
                              self.z[0]])
            stop  = np.array([xc1 - self.cpw_gap, self.box_y[1], self.z[2]])
            openems.Box(
                self.em,
                'ground_upper_left',
                self.metal_name,
                self.priority,
                start,
                stop,
                padname = None).duplicate('ground_upper_right').mirror('x')
