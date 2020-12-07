#!/usr/bin/env python3
import sys
from scipy.constants import pi, c, mil
mm = 0.001
from openems import OpenEMS, Box, Cylinder, Via, Port, Metal, Dielectric, geometries
import numpy as np

em = OpenEMS('via_1_4_oshpark', EndCriteria = 1e-4, fmin = 0e6, fmax = 40e9,
                     boundaries = ['PEC', 'PEC', 'PEC', 'PEC', 'PEC', 'PEC'])
em.fsteps = 1601
copper = Metal(em, 'copper')
pcopper = Metal(em, 'pcopper')
sub1 = Dielectric(em, 'substrate', eps_r=3.2)
sub2 = Dielectric(em, 'substrate', eps_r=4)
air = Dielectric(em, 'substrate', eps_r=1)

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

planar = geometries.planar_full_box(x=[-0.5*box_length, 0.5*box_length],
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
Box(copper, 9, start, stop)

# line
start = np.array([-0.5*box_length+port_length, 0.5*ms_width, sub1t])
stop  = np.array([0, -0.5*ms_width, bt])
Box(copper, 9, start, stop)

# ports
start = [-0.5*box_length, ms_width/2.0, sub1t]
stop  = [-0.5*box_length + port_length, ms_width/-2.0, bt]
Port(em, start, stop, direction='x', z=50)
start = [0.5*box_length, ms_width/2.0, bb]
stop  = [0.5*box_length - port_length, ms_width/-2.0, bb+ofoil]
Port(em, start, stop, direction='x', z=50)

Via(copper, priority=9, x=0, y=0,
            z=[[bb, bt], [bt, bt-ofoil], [0, ifoil], [-sub2t, -sub2t-ifoil], [bb+ofoil, bb]],
            drillradius = 0.5*0.25e-3,
            wall_thickness = 25e-6,
            padradius = 0.46e-3*0.5,
            padname = '1')

for x in range(-2,3):
    for y in [-0.75*mm, 0.75*mm]:
        Cylinder(copper, 9, [x*mm, y, bb], [x*mm, y, bt], 0.3*mm*0.5)
        Cylinder(copper, 9, [x*mm, y, bt], [x*mm, y, bt-ofoil], 0.46*mm*0.5)
        Cylinder(copper, 9, [x*mm, y, bb], [x*mm, y, bb+ofoil], 0.46*mm*0.5)

command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
em.run_openems(command)
