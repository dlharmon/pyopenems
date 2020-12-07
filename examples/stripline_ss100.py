#!/usr/bin/env python3
import sys
from scipy.constants import pi, c, mil
from openems import OpenEMS, Box, Cylinder, Port, Metal, Dielectric, Polygon, arc
import numpy as np
use_PML_coax = True

em = OpenEMS(
    'sss_bpf',
    EndCriteria = 1e-6,
    fmin = 0e6,
    fmax = 50e9,
    fsteps = 1001,
    #boundaries = ['PEC', 'PEC', 'PML_8', 'PML_8', 'PEC', 'PEC'],
)
fc = 16.95e9
copper = Metal(em, 'copper')
sub = Dielectric(em, 'ro4350b', eps_r=3.2)
zport = 100

foil_thickness = 0.05e-3
substrate_thickness = 4*mil
port_length = 0.42e-3
box_width = 3e-3
box_length = 20e-3
ms_width = 0.56e-3

# dimensions Z
zair = 0.7e-3
z0 = 0
z1 = z0 + zair # bottom of bottom foil
z2 = z1 + foil_thickness # top of bottom foil
z3 = z2 + substrate_thickness # bottom of top foil
z4 = z3 + foil_thickness # top of top foil
z5 = z4 + zair

em.resolution = [50e-6, 50e-6, 50e-6]

em.mesh.AddLine('z', z0)
em.mesh.AddLine('z', z5)
em.mesh.AddLine('z', z4 + 50e-6)
#em.mesh.AddLine('z', z4 - 25e-6)
em.mesh.AddLine('z', (z3+z2)*0.5)
#em.mesh.AddLine('z', (3*z3+z2)*0.25)

# substrate
start = np.array([-0.5*box_length, 0.5*box_width, z2])
stop  = np.array([0.5*box_length, -0.5*box_width, z3])
Box(sub, 1, start, stop)

for m in [-1,1]:
    start = np.array([m*(0.5*box_length-port_length), 0.5*ms_width, z3])
    stop  = np.array([0, -0.5*ms_width, z4])
    Box(copper, 1, start, stop, padname = None)
    stop[0] = m*0.5*box_length
    Port(em, start, stop, direction='x', z=zport)

em.write_kicad(em.name)
command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
print(command)
em.run_openems(command, z=zport)
