#!/usr/bin/env python
from scipy.constants import pi, c, epsilon_0, mu_0, mil, inch
mm = 0.001
import openems
import numpy as np
import math

pi = math.pi
cat = np.concatenate

def arc(x, y, r, a0, a1):
    angles = np.linspace(a0,a1,16)
    return r*np.exp(1j*angles) + x + 1j*y

def complex_to_xy(a):
    rv = np.zeros((len(a),2))
    for i in range(len(a)):
        rv[i][0] = a[i].real
        rv[i][1] = a[i].imag
    return rv

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
             endspace = 0.5 * mm):
    alumina = openems.Dielectric(em, 'alumina', eps_r=9.8)
    metal = openems.Metal(em, 'pec_wilkinson')
    n = len(rv)
    priority = 9

    # substrate
    start = np.array([(n*4 - 1)*r+endspace, y1+r+endspace, z[0]])
    stop  = np.array([-1.0*endspace, -1.0*start[1], z[1]])
    substrate.AddBox(start, stop, 1)

    # common port line (pad 1)
    start = np.array([-1.0*endspace + port_length,  0.5*ms_width, z[1]])
    stop  = np.array([0, -0.5*ms_width, z[2]])
    metal.AddBox(start, stop, priority=priority, padname = '1')

    lo = arc(r, -y1, r+0.5*w[0], pi, 2*pi)
    li = arc(r, -y1, r-0.5*w[0], pi, 2*pi)
    lo = cat((lo, arc(3*r, -y2, r-0.5*w[0], pi, 0.55*pi)))
    li = cat((li, arc(3*r, -y2, r+0.5*w[0], pi, 0.55*pi)))
    for i in range(n-1):
        x = (4*i+3)*r
        w2 = w[1+i]
        em.mesh.AddLine('x', x + r - 0.5*w2)
        em.mesh.AddLine('x', x + r + 0.5*w2)
        em.mesh.AddLine('x', x + 3*r - 0.5*w2)
        em.mesh.AddLine('x', x + 3*r + 0.5*w2)
        lo = cat((lo, arc(x, -y2, r-0.5*w2, 0.45*pi, 0)))
        li = cat((li, arc(x, -y2, r+0.5*w2, 0.45*pi, 0)))
        lo = cat((lo, arc(2*r + x, -y1, r+0.5*w2, pi, 2*pi)))
        li = cat((li, arc(2*r + x, -y1, r-0.5*w2, pi, 2*pi)))
        lo = cat((lo, arc(4*r + x, -y2, r-0.5*w2, pi, 0.55*pi)))
        li = cat((li, arc(4*r + x, -y2, r+0.5*w2, pi, 0.55*pi)))
    l = cat((lo, li[::-1]))
    l = cat((l[::-1].conj(), l))
    openems.Polygon(metal,
                    priority = priority,
                    points = complex_to_xy(l),
                    elevation = z[1:],
                    normal_direction = 'z',
                    pcb_layer = 'F.Cu',
                    pcb_width = 0.001)

    # output lines
    start = np.array([(n*4 - 1)*r+endspace - port_length, 0.25*mm, z[1]])
    stop  = np.array([(n*4 - 1)*r-0.25*mm, 0.25*mm+ms_width, z[2]])
    lp2 = metal.AddBox(start, stop, priority=priority, padname = '2')
    lp3 = lp2.duplicate("line_p3").mirror('y')
    lp3.padname = '3'

    # coupled line ports
    start = [(n*4 - 1)*r+endspace - port_length, 0.25*mm, z[1]]
    stop  = [(n*4 - 1)*r+endspace,  0.25*mm+ms_width, z[2]]
    openems.Port(em, start, stop, direction='x', z=50).duplicate().mirror('y')

    # main line port
    start = [-1.0*endspace, -0.5*ms_width, z[1]]
    stop  = [-1.0*endspace + port_length,  0.5*ms_width, z[2]]
    openems.Port(em, start, stop, direction='x', z=50)

    for i in range(n):
        if not rv[i]:
            continue
        em.add_resistor('r{}'.format(i),
                        origin=np.array([4*r*i + 3*r,0,z[2]]),
                        direction='y',
                        value=rv[i], invert=False, priority=9, dielectric=alumina,
                        metal=metal,
                        element_down=False,
                        size = '0402')
