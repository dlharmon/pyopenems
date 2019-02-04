#!/usr/bin/env python3
import sys
mm = 0.001
import openems
import numpy as np

def arc(x, y, r, a0, a1):
    angles = np.linspace(a0,a1,32)
    return r*np.exp(1j*angles) + x + 1j*y

def complex_to_xy(a):
    rv = np.zeros((len(a),2))
    for i in range(len(a)):
        rv[i][0] = a[i].real
        rv[i][1] = a[i].imag
    return rv

cat = np.concatenate

em = openems.OpenEMS('vert_connector_ms_oshpark', EndCriteria = 1e-5, fmin = 0e6, fmax = 50e9,
                     boundaries = ['PEC', 'PEC', 'PEC', 'PEC', 'PEC', 'PEC'])
em.fsteps = 1601
copper = openems.Metal(em, 'copper')
pcopper = openems.Metal(em, 'pcopper')
sub1 = openems.Dielectric(em, 'substrate', eps_r=3.2)
sub2 = openems.Dielectric(em, 'substrate', eps_r=4.0)

sub1t = 0.19*mm
sub2t = 1.0*mm

ifoil = 0.0125*mm
ofoil = 0.035*mm
port_length = 0.1*mm
box_length = 3*mm
box_width = 2*mm
ms_width = 0.42*mm
airspace = 1*mm
via_pad = 0.46*mm
via_clearance = 0.25*mm

bt = sub1t + ofoil
bb = -1*(ofoil+sub2t+sub1t)

em.resolution = 25e-6

em.mesh.AddLine('z', sub1t+airspace)
zmin = bb - 1*mm
em.mesh.AddLine('z', zmin)

def planar_fullbox(sub, z, priority=1):
    start = np.array([-0.5*box_length, 0.5*box_width, z[0]])
    stop  = np.array([0.5*box_length, -0.5*box_width, z[1]])
    sub.AddBox(start, stop, priority=priority)

def planar_fullbox_center_hole(subs, z, r, priority=1):
    x = 0.5*box_length
    y = 0.5*box_width * 1.0j
    outside = np.array([0+y, x+y, x-y, 0-y])
    inside = arc(0,0, r, -np.pi*0.5, np.pi*0.5)
    openems.Polygon(subs,
                    priority=priority,
                    pcb_layer=None,
                    points = complex_to_xy(cat((inside, outside))),
                    elevation = z,
                    normal_direction = 'z').duplicate().mirror('x')

clearance_r = via_pad*0.5 + via_clearance
planar_fullbox(sub1, [0, sub1t], priority=1) # sub1 top
planar_fullbox_center_hole(pcopper, [0, ifoil], clearance_r, priority=2) # inner 1 foil
planar_fullbox(sub2, [0, -sub2t], priority=1) # sub2
planar_fullbox(sub1, [-sub2t, -(sub2t+sub1t)], priority=1) # sub1 bottom
planar_fullbox_center_hole(pcopper, [-sub2t, -(sub2t+ifoil)], clearance_r, priority=2) # inner2 foil
planar_fullbox_center_hole(pcopper, [bb, bb+ofoil], 0.67*mm, priority=1) # bottom foil

# ms line
start = np.array([-0.5*box_length+port_length, 0.5*ms_width, sub1t])
stop  = np.array([0, -0.5*ms_width, bt])
copper.AddBox(start, stop, priority=9)

# ms port
start = [-0.5*box_length, ms_width/2.0, sub1t]
stop  = [-0.5*box_length + port_length, ms_width/-2.0, bt]
openems.Port(em, start, stop, direction='x', z=50)

# ground vias
for n in range(-3,4):
    r = 0.9 * mm
    c = np.exp(1j*2*np.pi*n*22.0/180.0) * r
    x = np.real(c)
    y = np.imag(c)
    copper.AddCylinder([x, y, bb], [x, y, bt], 0.3*mm*0.5, priority=9)
    copper.AddCylinder([x, y, bt], [x, y, bt-ofoil], via_pad*0.5, priority=9)

# signal via
copper.AddCylinder([0, 0, bb], [0, 0, bt], 0.3*mm*0.5, priority=9)
for z in [[bt, bt-ofoil], [0, ifoil], [-sub2t, -sub2t-ifoil], [bb+ofoil, bb]]:
    start = [0, 0, z[0]]
    stop  = [0, 0, z[1]]
    copper.AddCylinder(start, stop, via_pad*0.5, priority=9)

# coax shield
planar_fullbox_center_hole(copper, [bb, zmin], r=1.5*mm/2.0, priority=1)

pin_diameter = 0.695*mm
coax_port_length = 0.2*mm

# pin
start = np.array([0, 0, bb-0.2*mm])
stop  = np.array([0, 0, zmin+coax_port_length])
copper.AddCylinder(start, stop, 0.5*pin_diameter, priority=9)

# smaller part of pin
start = np.array([0, 0, bb])
stop  = np.array([0, 0, zmin + coax_port_length])
copper.AddCylinder(start, stop, 0.5*0.5*mm, priority=9)

# port (coax)
start = [0.5*coax_port_length, 0.5*coax_port_length, zmin]
stop  = [-0.5*coax_port_length, -0.5*coax_port_length, zmin + coax_port_length]
openems.Port(em, start, stop, direction='z', z=50)

command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
em.run_openems(command)
