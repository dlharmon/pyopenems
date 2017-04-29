#!/usr/bin/env python
mm = 0.001
import openems
import numpy as np

class IDBPF():
    def __init__(self,
                 em, # openems instance
                 metal_name = 'pec', # metal instance, define with openems.Metal()
                 z = [], # z position vector, z[0] = substrate bottom, z[1] = substrate top, z[2] = foil top
                 space = [], # space between resonator fingers
                 rl = [], # length of resonator fingers
                 rw = [], # width of resonator fingers
                 portlength = 0.2*mm, # length of the openems port
                 feedwidth = 0.85*mm, # width of the trace leaving the filter and port
                 tapoffset = 1.0*mm, # offset of tap from end of resonator
                 end_gap = 0.3*mm, # space between the end of a resonator and ground
                 viaoffset = [0.0, 0.0], # [x,y], shift the vias to simulate drill registration error
                 via_radius = 0.15*mm, # radius of the via drills
                 via_padradius = 0.3*mm, # radius of the via pads
                 mask_thickness = 0, # set to non-zero to enable solder mask over filter
    ):
        self.em = em
        self.metal_name = metal_name
        self.z = z
        self.space = space
        self.rl = rl
        self.rw = rw
        self.end_gap = end_gap
        self.ring_y_width = via_padradius * 2.0
        self.portlength = portlength
        self.priority = 9
        self.feedwidth = feedwidth
        self.viaoffset = viaoffset
        self.via_radius = via_radius
        self.via_padradius = via_padradius
        self.mask_thickness = mask_thickness
        self.tapoffset = tapoffset
    def generate(self):
        ring_ix = 0.5 * (np.max(self.rl) + self.end_gap)
        ring_ox = ring_ix + 2.0 * self.via_padradius
        via_z = [[self.z[0], self.z[2]], [self.z[1], self.z[2]]]
        # fingers
        y = -0.5*self.space[-1:][0]
        mirror = False
        mirrorstring = ['', 'x']
        for i in range(len(self.space))[::-1]: # reverse order
            x1 = 0.5 * (ring_ox + ring_ix)
            x2 = ring_ix - self.rl[i]
            y += self.space[i]
            start = [x1, y, self.z[1]];
            y += self.rw[i]
            stop  = [x2, y, self.z[2]];
            box = openems.Box(self.em, None, self.metal_name, self.priority, start, stop, padname = '2')
            box.mirror(mirrorstring[mirror])
            mirror = not mirror
            box2 = box.duplicate()
            box2.mirror('xy')
            v = openems.Via(self.em, None, 'pec', 2, x=ring_ix+self.via_padradius, y=y-0.5*self.rw[i], z=via_z,
                            drillradius=self.via_radius, padradius=self.via_padradius, padname='2')
            v.mirror(mirrorstring[not mirror])
            v2 = v.duplicate()
            v2.mirror('xy')
        mirror = not mirror
        # ports
        y1 = y
        y -= 0.5*self.rw[0] # center of line
        y2 = y + 0.5*self.feedwidth + self.ring_y_width # y outside
        px = ring_ix - self.tapoffset
        py = y2 - self.portlength
        start = [px + 0.5*self.feedwidth, y2, self.z[1]]
        stop  = [px - 0.5*self.feedwidth, py, self.z[2]]
        p = openems.Port(self.em, start, stop, direction='y', z=50)
        p.mirror(mirrorstring[mirror])
        p2 = p.duplicate().mirror('xy')
        # feed lines
        start = [px + 0.5*self.feedwidth, py, self.z[1]]
        stop  = [px - 0.5*self.feedwidth, py - self.feedwidth, self.z[2]]
        box = openems.Box(self.em, None, self.metal_name, self.priority, start, stop, padname = '1')
        box.mirror(mirrorstring[mirror])
        box2 = box.duplicate()
        box2.mirror('xy')
        box2.padname = '3'
        tie = openems.Polygon(self.em, points = [[-px+0.5*self.feedwidth, py],
                                                 [-px-0.5*self.feedwidth, py],
                                                 [-px-0.5*self.feedwidth, y1],
                                                 [-px+0.5*self.feedwidth, y1]],
                              elevation = [self.z[1], self.z[2]], priority=9)
        tie2 = tie.duplicate().mirror('xy')
        # substrate
        start = np.array([ring_ox, y2, self.z[0]])
        stop  = openems.mirror(start, 'xy')
        stop[2] = self.z[1]
        sub = openems.Box(self.em, None, 'sub', 1, start, stop);
        # mask
        if self.mask_thickness > 0.0:
            start = np.array([ring_ox, y2, self.z[1]])
            stop  = openems.mirror(start, 'xy')
            stop[2] += self.mask_thickness
            openems.Box(self.em, None, 'mask', 1, start, stop);
