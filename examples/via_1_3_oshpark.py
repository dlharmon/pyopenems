#!/usr/bin/env python3
import sys
mm = 0.001 # mm in meters
mil = 25.4e-6 # mil in meters
import openems
import openems.geometries
import numpy as np

em = openems.OpenEMS('via_1_3_oshpark', EndCriteria = 1e-4, fmin = 0e6, fmax = 40e9,
                     boundaries = ['PEC', 'PEC', 'PEC', 'PEC', 'PEC', 'PEC'],
                     fsteps=801)
copper = openems.Metal(em, 'copper')
pcopper = openems.Metal(em, 'pcopper')
sub1 = openems.Dielectric(em, 'substrate', eps_r=3.2)
sub2 = openems.Dielectric(em, 'substrate', eps_r=4)

sub1t = 0.166*mm
sub2t = 47*mil

ifoil = 0.0125*mm
ofoil = 0.035*mm
port_length = 0.1*mm
box_length = 5*mm
box_width = 2*mm
sl_width = 0.24*mm
ms_width = 0.35*mm
airspace = 1*mm

bt = sub1t + ofoil
bb = -1*(ofoil+sub2t+sub1t)

em.resolution = 50e-6

planar = openems.geometries.planar_full_box(
    x=[-0.5*box_length, 0.5*box_length],
    y=[-0.5*box_width, 0.5*box_width])

clearance_r = 0.86e-3 * 0.5

em.mesh.AddLine('z', sub1t+airspace)
em.mesh.AddLine('z', -1.0*(2*sub1t+sub2t+airspace))

planar.add(sub1, [0, sub1t]) # sub1 top
planar.add_center_hole(pcopper, [0, ifoil], clearance_r, priority=2) # inner 1 foil
planar.add(sub2, [0, -sub2t]) # core
planar.add(sub1, [-sub2t, -(sub2t+sub1t)]) # sub1 bot
planar.add_center_hole(pcopper, [bb, -(sub2t+sub1t)], clearance_r, priority=2) # bottom foil

# line (sl)
start = np.array([0, 0.5*sl_width, -sub2t])
stop  = np.array([0.5*box_length-port_length, -0.5*sl_width, -sub2t-ifoil])
copper.AddBox(start, stop, priority=9)

# line (ms)
start = np.array([-0.5*box_length+port_length, 0.5*ms_width, sub1t])
stop  = np.array([0, -0.5*ms_width, bt])
copper.AddBox(start, stop, priority=9)

# port (ms)
start = [-0.5*box_length, ms_width/2.0, sub1t]
stop  = [-0.5*box_length + port_length, ms_width/-2.0, bt]
openems.Port(em, start, stop, direction='x', z=50)

# port (sl)
start = [0.5*box_length, sl_width/2.0, -sub2t]
stop  = [0.5*box_length - port_length, sl_width/-2.0, -sub2t-ifoil]
openems.Port(em, start, stop, direction='x', z=50)

openems.Via(copper, priority=9, x=0, y=0,
            z=[[bb, bt], [bt, bt-ofoil], [0, ifoil], [-sub2t, -sub2t-ifoil], [bb+ofoil, bb]],
            drillradius = 0.5*0.25e-3,
            wall_thickness = 25e-6,
            padradius = 0.46e-3*0.5,
            padname = '1')

for x in range(-3,4):
    x *= 0.5*mm
    for y in [-0.75*mm, 0.75*mm]:
        copper.AddCylinder([x, y, bb], [x, y, bt], 0.3*mm*0.5, priority=9)
        copper.AddCylinder([x, y, bt], [x, y, bt-ofoil], 0.46*mm*0.5, priority=9)

command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
em.run_openems(command)
