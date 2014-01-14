#!/usr/bin/env python
from scipy.constants import pi, c, epsilon_0, mu_0, mil, inch
mm = 0.001
import openems
import openems.idbpf
import numpy as np

#!/usr/bin/env python
mm = 0.001
import numpy as np

class IDBPF():
    def __init__(self, em):
        self.em = em
        self.metal_name = 'pec'
        self.z = [] # [bottom of substrate, top of substrate, top of metal] 
        self.space = []
        self.rl = []
        self.rw = []
        self.ring_ix = 0.0
        self.ring_ox = 0.0
        self.ring_y_width = 1.0*mm
        self.portlength = 0.2*mm
        self.priority = 9
        self.feedwidth = 0.85*mm
        self.feedgap = 0.2*mm
        self.viaoffset = [0.0, 0.0]
        self.via_radius = 0.15*mm
        self.via_padradius = 0.3*mm
        self.mask_thickness = 0.0
        self.inner_metal = False
        self.inner_metal_z = [[]]
    def generate(self):
        # fingers
        y = -0.5*self.space[-1:][0]
        mirror = False
        mirrorstring = ['', 'x']
        for i in range(len(self.space))[::-1]: # reverse order
            x1 = 0.5 * (self.ring_ox + self.ring_ix)
            x2 = self.ring_ix - self.rl[i]
            fingername = 'r{}'.format(i)
            y += self.space[i]
            start = [x1, y, self.z[1]];
            y += self.rw[i]
            stop  = [x2, y, self.z[2]];
            box = self.em.add_box(fingername, self.metal_name, self.priority, start, stop, padname = '2')
            box.mirror(mirrorstring[mirror])
            mirror = not mirror
            box2 = box.duplicate(fingername + 'm')
            box2.mirror('xy')
            if i == 0:
                box.padname = '1'
                box2.padname = '3'
        # feed lines
        mirror = not mirror
        y -= 0.5*self.rw[0] # center of line
        start = [self.ring_ix, y + 0.5*self.feedwidth, self.z[1]]
        stop  = [self.ring_ox - self.portlength, y - 0.5*self.feedwidth, self.z[2]]
        box = self.em.add_box('pext1', self.metal_name, self.priority, start, stop, padname = '1')
        box.mirror(mirrorstring[mirror])
        box2 = box.duplicate('pext2')
        box2.mirror('xy')
        box2.padname = '3'
        # ports
        start = [self.ring_ox, y + 0.5*self.feedwidth, self.z[1]]
        stop  = [self.ring_ox - self.portlength, y - 0.5*self.feedwidth, self.z[2]]
        p = self.em.add_port(start, stop, direction='x', z=50)
        p.mirror(mirrorstring[mirror])
        p.duplicate().mirror('xy')
        # metal ring (sides)
        y1 = y + 0.5*self.feedwidth + self.feedgap
        y2 = y1 + self.ring_y_width
        start = [self.ring_ox, y1, self.z[1]]
        stop  = [-1.0 * self.ring_ox, y2, self.z[2]]
        box = self.em.add_box('ring1', self.metal_name, self.priority, start, stop, padname = '2')
        box.mirror(mirrorstring[mirror])
        box.duplicate('ring2').mirror('xy')
        # metal ring (sides)
        y3 = y - (0.5*self.feedwidth + self.feedgap)
        start = [self.ring_ox, y3, self.z[1]]
        stop  = [self.ring_ix, -1.0*y2, self.z[2]]
        box = self.em.add_box('ring3', self.metal_name, self.priority, start, stop, padname = '2')
        box.mirror(mirrorstring[mirror])
        box.duplicate('ring4').mirror('xy')
        # metal - inner ends
        if self.inner_metal:
            imname = 0
            for z in self.inner_metal_z:
                start = [self.ring_ox, y1, z[0]]
                stop  = [-1.0 * self.ring_ox, y2, z[1]]
                box = self.em.add_box('mi{}'.format(imname), self.metal_name, self.priority, start, stop, padname = None)
                box.duplicate('mi{}'.format(imname+1)).mirror('xy')
                start = [self.ring_ox, y2, z[0]]
                stop  = [self.ring_ix, -1.0*y2, z[1]]
                box = self.em.add_box('mi{}'.format(imname+2), self.metal_name, self.priority, start, stop, padname = None)
                box.duplicate('mi{}'.format(imname+3)).mirror('xy')
                imname += 4
        # substrate
        start = np.array([self.ring_ox, y2, self.z[0]])
        stop  = openems.mirror(start, 'xy') 
        stop[2] = self.z[1]
        self.em.add_box('sub1', 'sub', 1, start, stop);
        # mask
        if self.mask_thickness > 0.0:
            start = np.array([self.ring_ox, y2, self.z[1]])
            stop  = openems.mirror(start, 'xy') 
            stop[2] += self.mask_thickness
            self.em.add_box('mask', 'mask', 1, start, stop);
        # vias (along y)
        via_z = [[self.z[0], self.z[2]]]#, [self.z[1], self.z[2]]]
        y_start = y3 - self.via_padradius
        y_stop = -1.0* y1 - self.via_padradius
        x = self.ring_ix + self.via_padradius
        n_via = 0
        n_vias = 1 + np.floor(np.abs(y_start-y_stop)/(2.0*self.via_padradius))
        for y in np.linspace(y_start, y_stop, n_vias):
            v = self.em.add_via('via{}'.format(n_via), 'pec', 2, x=x, y=y, z=via_z, drillradius=self.via_radius, padradius=self.via_padradius, padname='2')
            v.mirror(mirrorstring[mirror])
            v.duplicate('via{}'.format(n_via+1)).mirror('xy')
            n_via += 2
        # vias (along x)
        y = y_stop
        x_start = self.ring_ix + self.via_padradius
        x_stop = self.via_padradius - self.ring_ox
        n_vias = 1 + np.floor(np.abs(x_start-x_stop)/(2.0*self.via_padradius))
        for x in np.linspace(x_start, x_stop, n_vias)[1:]:
            v = self.em.add_via('via{}'.format(n_via), 'pec', 2, x=x, y=y, z=via_z, drillradius=self.via_radius, padradius=self.via_padradius, padname='2')
            v.mirror(mirrorstring[mirror])
            v.duplicate('via{}'.format(n_via+1)).mirror('xy')
            n_via += 2
