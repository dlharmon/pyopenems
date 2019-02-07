#!/usr/bin/env python3
import sys
from scipy.constants import pi, c, epsilon_0, mu_0, mil
mm = 0.001
import openems
import openems.geometries
import numpy as np

em = openems.OpenEMS('via_1_4_oshpark', EndCriteria = 1e-4, fmin = 0e6, fmax = 40e9,
                     boundaries = ['PEC', 'PEC', 'PEC', 'PEC', 'PEC', 'PEC'])
em.fsteps = 1601
copper = openems.Metal(em, 'copper')
pcopper = openems.Metal(em, 'pcopper')
sub1 = openems.Dielectric(em, 'substrate', eps_r=3.2)
sub2 = openems.Dielectric(em, 'substrate', eps_r=4)
air = openems.Dielectric(em, 'substrate', eps_r=1)

sub1t = 0.166*mm
sub2t = 47*mil

ifoil = 0.0125*mm
ofoil = 0.035*mm
port_length = 0.1*mm
box_length = 5*mm
box_width = 2*mm
ms_width = 0.35*mm
airspace = 1*mm

bt = sub1t + ofoil
bb = -1*(ofoil+sub2t+sub1t)

em.resolution = 50e-6

planar = openems.geometries.planar_full_box(x=[-0.5*box_length, 0.5*box_length],
                                            y=[-0.5*box_width, 0.5*box_width])

em.mesh.AddLine('z', sub1t+airspace)
em.mesh.AddLine('z', -1.0*(2*sub1t+sub2t+airspace))

clearance_r = 0.86e-3 * 0.5

planar.add(sub1, [0, sub1t]) # sub1 top
planar.add_center_hole(pcopper, [0, ifoil], clearance_r, priority=2) # inner 1 foil
planar.add(sub2, [0, -sub2t]) # core
planar.add_center_hole(pcopper, [-sub2t, -(sub2t+ifoil)], clearance_r, priority=2) # inner 2 foil
planar.add(sub1, [-sub2t, -(sub2t+sub1t)]) # sub1 bot

# line
start = np.array([0, 0.5*ms_width, bb])
stop  = np.array([0.5*box_length-port_length, -0.5*ms_width, bb+ofoil])
copper.AddBox(start, stop, priority=9)

# line
start = np.array([-0.5*box_length+port_length, 0.5*ms_width, sub1t])
stop  = np.array([0, -0.5*ms_width, bt])
copper.AddBox(start, stop, priority=9)

# ports
start = [-0.5*box_length, ms_width/2.0, sub1t]
stop  = [-0.5*box_length + port_length, ms_width/-2.0, bt]
openems.Port(em, start, stop, direction='x', z=50)
start = [0.5*box_length, ms_width/2.0, bb]
stop  = [0.5*box_length - port_length, ms_width/-2.0, bb+ofoil]
openems.Port(em, start, stop, direction='x', z=50)

copper.AddCylinder([0, 0, bb], [0, 0, bt], 0.3*mm*0.5, priority=9)

for x in range(-2,3):
    for y in [-0.75*mm, 0.75*mm]:
        copper.AddCylinder([x*mm, y, bb], [x*mm, y, bt], 0.3*mm*0.5, priority=9)
        copper.AddCylinder([x*mm, y, bt], [x*mm, y, bt-ofoil], 0.46*mm*0.5, priority=9)
        copper.AddCylinder([x*mm, y, bb], [x*mm, y, bb+ofoil], 0.46*mm*0.5, priority=9)

# via pads
for z in [[bt, bt-ofoil], [0,ifoil], [-sub2t, -sub2t-ifoil], [bb+ofoil, bb]]:
    start = [0, 0, z[0]]
    stop  = [0, 0, z[1]]
    copper.AddCylinder(start, stop, 0.46*mm*0.5, priority=9)

command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
em.run_openems(command)
