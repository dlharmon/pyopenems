#!/usr/bin/env python
mm = 0.001
import openems
import numpy as np
import math

pi = math.pi
cat = np.concatenate
arc = openems.arc

def generate(em,
             substrate,
             z, # [bottom of substrate, top of substrate, top of metal]
             y1 = 5.5*mm,
             y2 = 0.9*mm,
             r = 0.5 * mm,
             rv = [200, 200, 200, 200],
             w = [0.127*mm, 0.152*mm, 0.19*mm, 0.23*mm],
             port_length = 0.2*mm,
             ms_width = 0.36*mm,
             endspace = 0.5 * mm,
             resistor_size='0402'
):
    alumina = openems.Dielectric(em, 'alumina', eps_r=9.8)
    metal = openems.Metal(em, 'pec_wilkinson')
    n = len(rv)

    # substrate
    start = np.array([(n*4 - 1)*r+endspace, y1+r+endspace, z[0]])
    stop  = np.array([-1.0*endspace, -1.0*start[1], z[1]])
    substrate.AddBox(start, stop, 1)

    # common port line (pad 1)
    start = np.array([-1.0*endspace + port_length,  0.5*ms_width, z[1]])
    stop  = np.array([0, -0.5*ms_width, z[2]])
    metal.AddBox(start, stop, priority=9, padname = '1')

    lo = arc(r, -y1, r+0.5*w[0], pi, 2*pi, 16)
    li = arc(r, -y1, r-0.5*w[0], pi, 2*pi, 16)
    lo = cat((lo, arc(3*r, -y2, r-0.5*w[0], pi, 0.55*pi, 16)))
    li = cat((li, arc(3*r, -y2, r+0.5*w[0], pi, 0.55*pi, 16)))
    for i in range(n-1):
        x = (4*i+3)*r
        w2 = w[1+i]
        em.mesh.AddLine('x', x + r - 0.5*w2)
        em.mesh.AddLine('x', x + r + 0.5*w2)
        em.mesh.AddLine('x', x + 3*r - 0.5*w2)
        em.mesh.AddLine('x', x + 3*r + 0.5*w2)
        lo = cat((lo, arc(x, -y2, r-0.5*w2, 0.45*pi, 0, 16)))
        li = cat((li, arc(x, -y2, r+0.5*w2, 0.45*pi, 0, 16)))
        lo = cat((lo, arc(2*r + x, -y1, r+0.5*w2, pi, 2*pi, 16)))
        li = cat((li, arc(2*r + x, -y1, r-0.5*w2, pi, 2*pi, 16)))
        lo = cat((lo, arc(4*r + x, -y2, r-0.5*w2, pi, 0.55*pi, 16)))
        li = cat((li, arc(4*r + x, -y2, r+0.5*w2, pi, 0.55*pi, 16)))
    l = cat((lo, li[::-1]))
    l = cat((l[::-1]*[1,-1], l))
    openems.Polygon(metal,
                    priority = 9,
                    points = l,
                    elevation = z[1:],
                    normal_direction = 'z',
                    pcb_layer = 'F.Cu',
                    pcb_width = 0.001)

    # x at 2 port side
    x0 = (n*4 - 1) * r + endspace
    x1 = x0 - port_length

    # output lines
    start = np.array([x1, 0.2*mm, z[1]])
    stop  = np.array([(n*4 - 1)*r-0.1*mm, 0.2*mm+ms_width, z[2]])
    lp2 = metal.AddBox(start, stop, priority=9, padname = '2')
    lp3 = lp2.duplicate("line_p3").mirror('y')
    lp3.padname = '3'

    # main line port
    start = [-1.0*endspace, -0.5*ms_width, z[1]]
    stop  = [-1.0*endspace + port_length,  0.5*ms_width, z[2]]
    openems.Port(em, start, stop, direction='x', z=50)

    # coupled line ports
    start = [x0 - port_length, 0.2*mm, z[1]]
    stop  = [x0,  0.2*mm+ms_width, z[2]]
    openems.Port(em, start, stop, direction='x', z=50).duplicate().mirror('y')

    for i in range(n):
        if not rv[i]:
            continue
        em.add_resistor('r{}'.format(i),
                        origin=np.array([4*r*i + 3*r,0,z[2]]),
                        direction='y',
                        value=rv[i], invert=False, priority=9, dielectric=alumina,
                        metal=metal,
                        element_down=False,
                        size = resistor_size)
