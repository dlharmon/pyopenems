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
                 priority = 9, # openems priority of all filter metal
                 portlength = 0.2*mm, # length of the openems port
                 feedwidth = 0.85*mm, # width of the trace leaving the filter and port
                 feedgap = 0.2*mm, # space from trace leaving the filter to via ring
                 end_gap = 0.3*mm, # space between the end of a resonator and ground
                 viaoffset = [0.0, 0.0], # [x,y], shift the vias to simulate drill registration error
                 via_radius = 0.15*mm, # radius of the via drills
                 via_padradius = 0.3*mm, # radius of the via pads
                 mask_thickness = 0, # set to non-zero to enable solder mask over filter
                 inner_metal = False, # set to True to enable inner metal layers in via ring
                 inner_metal_z = [[]],
                 offset = np.array([0.0, 0.0, 0.0]) # offset
    ):
        self.em = em
        self.metal_name = metal_name
        self.z = z
        self.space = space
        self.rl = rl
        self.rw = rw
        self.ring_ix = 0.5 * (np.max(self.rl) + end_gap)
        self.ring_ox = self.ring_ix + 2.0 * via_padradius
        self.ring_y_width = via_padradius * 2.0
        self.portlength = portlength
        self.priority = priority
        self.feedwidth = feedwidth
        self.feedgap = feedgap
        self.viaoffset = viaoffset
        self.via_radius = via_radius
        self.via_padradius = via_padradius
        self.mask_thickness = mask_thickness
        self.inner_metal = inner_metal
        self.inner_metal_z = inner_metal_z
        self.offset = offset
    def generate(self):
        # fingers
        y = -0.5*self.space[-1:][0]
        mirror = False
        mirrorstring = ['', 'x']
        for i in range(len(self.space))[::-1]: # reverse order
            x1 = 0.5 * (self.ring_ox + self.ring_ix)
            x2 = self.ring_ix - self.rl[i]
            y += self.space[i]
            start = [x1, y, self.z[1]];
            y += self.rw[i]
            stop  = [x2, y, self.z[2]];
            box = openems.Box(self.em, None, self.metal_name, self.priority, start, stop, padname = '2')
            box.mirror(mirrorstring[mirror])
            mirror = not mirror
            box2 = box.duplicate()
            box2.mirror('xy')
            if i == 0:
                box.padname = '1'
                box2.padname = '3'
            box.offset(self.offset)
            box2.offset(self.offset)
        # feed lines
        mirror = not mirror
        y -= 0.5*self.rw[0] # center of line
        start = [self.ring_ix, y + 0.5*self.feedwidth, self.z[1]]
        stop  = [self.ring_ox - self.portlength, y - 0.5*self.feedwidth, self.z[2]]
        box = openems.Box(self.em, None, self.metal_name, self.priority, start, stop, padname = '1')
        box.mirror(mirrorstring[mirror])
        box2 = box.duplicate()
        box2.mirror('xy')
        box2.padname = '3'
        box.offset(self.offset)
        box2.offset(self.offset)
        # ports
        start = [self.ring_ox, y + 0.5*self.feedwidth, self.z[1]]
        stop  = [self.ring_ox - self.portlength, y - 0.5*self.feedwidth, self.z[2]]
        p = openems.Port(self.em, start, stop, direction='x', z=50)
        p.mirror(mirrorstring[mirror])
        p2 = p.duplicate().mirror('xy')
        p.offset(self.offset)
        p2.offset(self.offset)
        # metal ring (sides)
        y1 = y + 0.5*self.feedwidth + self.feedgap
        y2 = y1 + self.ring_y_width
        start = [self.ring_ox, y1, self.z[1]]
        stop  = [-1.0 * self.ring_ox, y2, self.z[2]]
        box = openems.Box(self.em, None, self.metal_name, self.priority, start, stop, padname = '2')
        box.mirror(mirrorstring[mirror])
        box2 = box.duplicate().mirror('xy')
        box.offset(self.offset)
        box2.offset(self.offset)
        # metal ring (sides)
        y3 = y - (0.5*self.feedwidth + self.feedgap)
        start = [self.ring_ox, y3, self.z[1]]
        stop  = [self.ring_ix, -1.0*y2, self.z[2]]
        box = openems.Box(self.em, None, self.metal_name, self.priority, start, stop, padname = '2')
        box.mirror(mirrorstring[mirror])
        box2 = box.duplicate().mirror('xy')
        box.offset(self.offset)
        box2.offset(self.offset)
        # metal - inner ends
        if self.inner_metal:
            for z in self.inner_metal_z:
                start = [self.ring_ox, y1, z[0]]
                stop  = [-1.0 * self.ring_ox, y2, z[1]]
                box = openems.Box(self.em, None, self.metal_name, self.priority, start, stop, padname = None)
                box2 = box.duplicate().mirror('xy')
                box.offset(self.offset)
                box2.offset(self.offset)
                start = [self.ring_ox, y2, z[0]]
                stop  = [self.ring_ix, -1.0*y2, z[1]]
                box = openems.Box(self.em, None, self.metal_name, self.priority, start, stop, padname = None)
                box2 = box.duplicate().mirror('xy')
                box.offset(self.offset)
                box2.offset(self.offset)
        # substrate
        start = np.array([self.ring_ox, y2, self.z[0]])
        stop  = openems.mirror(start, 'xy')
        stop[2] = self.z[1]
        sub = openems.Box(self.em, None, 'sub', 1, start, stop);
        sub.offset(self.offset)
        # mask
        if self.mask_thickness > 0.0:
            start = np.array([self.ring_ox, y2, self.z[1]])
            stop  = openems.mirror(start, 'xy')
            stop[2] += self.mask_thickness
            openems.Box(self.em, None, 'mask', 1, start, stop);
        # vias (along y)
        via_z = [[self.z[0], self.z[2]]]#, [self.z[1], self.z[2]]]
        y_start = y3 - self.via_padradius
        y_stop = -1.0* y1 - self.via_padradius
        x = self.ring_ix + self.via_padradius
        if not self.via_radius:
            return
        n_via = 0
        n_vias = 1 + np.floor(np.abs(y_start-y_stop)/(2.0*self.via_padradius))
        for y in np.linspace(y_start, y_stop, n_vias):
            v = openems.Via(self.em, None, 'pec', 2, x=x, y=y, z=via_z, drillradius=self.via_radius, padradius=self.via_padradius, padname='2')
            v.mirror(mirrorstring[mirror])
            v2 = v.duplicate().mirror('xy')
            n_via += 2
            v.offset(self.offset)
            v2.offset(self.offset)
        # vias (along x)
        y = y_stop
        x_start = self.ring_ix + self.via_padradius
        x_stop = self.via_padradius - self.ring_ox
        n_vias = 1 + np.floor(np.abs(x_start-x_stop)/(2.0*self.via_padradius))
        for x in np.linspace(x_start, x_stop, n_vias)[1:]:
            v = openems.Via(self.em, None, 'pec', 2, x=x, y=y, z=via_z, drillradius=self.via_radius, padradius=self.via_padradius, padname='2')
            v.mirror(mirrorstring[mirror])
            v2 = v.duplicate().mirror('xy')
            n_via += 2
            v.offset(self.offset)
            v2.offset(self.offset)
