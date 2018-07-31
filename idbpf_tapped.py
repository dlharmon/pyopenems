mm = 0.001
import openems
import numpy as np

class IDBPF():
    def __init__(self,
                 em, # openems instance
                 sub, # substrate, define with openems.Dielectric()
                 lidz = 0.0,
                 z = [], # z position, z[0] = sub bottom, z[1] = sub top, z[2] = foil top
                 space = [], # space between resonator fingers
                 rl = [], # length of resonator fingers
                 rw = [], # width of resonator fingers
                 portlength = 0.2*mm, # length of the openems port
                 feedwidth = 0.85*mm, # width of the trace leaving the filter and port
                 tapoffset = 1.0*mm, # offset of tap from end of resonator
                 end_gap = 0.3*mm, # space between the end of a resonator and ground
                 via_radius = 0.15*mm, # radius of the via drills
                 via_padradius = 0.3*mm, # radius of the via pads
                 pcb_layer = 'F.Cu', # Kicad layer
                 mask_thickness = 0, # set to non-zero to enable solder mask over filter
                 mask = None, # mask, define with openems.Dielectric()
                 endmetal = True, # add metal to filter ends
    ):
        self.em = em
        self.sub = sub
        self.z = z
        self.space = space
        self.rl = rl
        self.rw = rw
        self.end_gap = end_gap
        self.ring_y_width = via_padradius * 2.0
        self.portlength = portlength
        self.feedwidth = feedwidth
        self.via_radius = via_radius
        self.via_padradius = via_padradius
        self.pcb_layer = pcb_layer
        self.mask_thickness = mask_thickness
        self.tapoffset = tapoffset
        self.mask = mask
        self.lidz = lidz
        self.endmetal = endmetal
    def generate(self):
        pec = openems.Metal(self.em, 'pec_filter')
        ring_ix = 0.5 * (np.max(self.rl) + self.end_gap)
        ring_ox = ring_ix + 2.0 * self.via_padradius
        via_z = [[self.z[0], self.z[1]+self.lidz], [self.z[1], self.z[2]]]
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
            box = openems.Box(pec, 9, start, stop, padname = 'poly', pcb_layer=self.pcb_layer)
            box.mirror(mirrorstring[mirror])
            mirror = not mirror
            box2 = box.duplicate()
            box2.mirror('xy')
            v = openems.Via(pec, priority=2,
                            x=ring_ix+self.via_padradius,
                            y=y-0.5*self.rw[i], z=via_z,
                            drillradius=self.via_radius,
                            padradius=self.via_padradius, padname='2')
            if not mirror:
                v.mirror('x')
            v.duplicate().mirror('xy')
            if self.endmetal:
                v.duplicate().mirror('y')
                v.duplicate().mirror('x')

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
        stop  = [px - 0.5*self.feedwidth, y-0.5*self.rw[0], self.z[2]]
        box = openems.Box(pec, 9, start, stop, padname = '1', pcb_layer=self.pcb_layer)
        box.mirror(mirrorstring[mirror])
        box2 = box.duplicate()
        box2.mirror('xy')
        box2.padname = '3'
        # substrate
        start = np.array([ring_ox, y2, self.z[0]])
        stop  = openems.mirror(start, 'xy')
        stop[2] = self.z[1]+self.lidz
        sub = openems.Box(self.sub, 1, start, stop)
        # mask
        if self.mask_thickness > 0.0:
            start = np.array([ring_ox, y2, self.z[1]])
            stop  = openems.mirror(start, 'xy')
            stop[2] += self.mask_thickness
            openems.Box(mask, 1, start, stop)
        # grounded end metal
        if self.endmetal:
            em1 = openems.Box(pec, 9, start = [ring_ix, y2, self.z[1]],
                              stop = [ring_ix + 2.0*self.via_padradius, -y2, self.z[2]],
                              padname = '2', pcb_layer=self.pcb_layer)
            em1.duplicate().mirror('x')
