#!/usr/bin/env python3
import sys
from scipy.constants import pi, c, mil
from openems import OpenEMS, Box, Cylinder, Port, Metal, Dielectric, Polygon, arc
import numpy as np

em = OpenEMS(
    'sss_idbpf',
    EndCriteria = 1e-6,
    fmin = 0e6,
    fmax = 40e9,
    fsteps = 1001,
    boundaries = ['PEC', 'PEC', 'PEC', 'PEC', 'PEC', 'PEC'],
)
copper = Metal(em, 'copper')
sub = Dielectric(em, 'polyimide', eps_r=3.2, tand=0.0035, fc=em.fmax)

foil_thickness = 35e-6
substrate_thickness = 4*mil
port_length = 0.065e-3
box_length = 14e-3
ms_width = 0.6e-3
port_length = 0.065e-3

lengths = 3.0e-3*np.ones(4)
gaps = [0.2e-3, 0.68e-3, 0.85e-3, 0.9e-3]
rw = 1e-3

# dimensions Z
zair = 1e-3
z0 = 0
z1 = z0 + 1e-3 # bottom of bottom foil
z2 = z1 + foil_thickness # top of bottom foil
z3 = z2 + substrate_thickness # bottom of top foil
z4 = z3 + foil_thickness # top of top foil
z5 = z4 + zair

em.resolution = [100e-6, 100e-6, 100e-6]

em.mesh.AddLine('z', z0)
em.mesh.AddLine('z', z5)
em.mesh.AddLine('z', (2*z2+z3)*0.33)
em.mesh.AddLine('z', (2*z3+z2)*0.33)

endgap = 0.3e-3

y = -0.5*(np.max(lengths)+endgap)

# resonators
x = -0.5*gaps[-1]
ym = -1

for i in range(len(lengths))[::-1]:
    ym *= -1
    x += gaps[i]
    l = lengths[i]
    x1 = x + rw
    yr = y+endgap if i==0 else y
    for m in [-1,1]:
        start = np.array([x*m, m*ym*yr, z3])
        stop = np.array([x1*m, m*ym*(y+l), z4])
        Box(copper, 1, start, stop, padname='poly')
    x = x1

ymin = y
ymax = -y
ledge = 0.5e-3
yshift = 0e-3

# port (ms), port line
for m in [-1,1]:
    start = np.array([m*(0.5*box_length-port_length), ym*(y+endgap)*m, z3])
    stop  = np.array([m*x, ym*(y+endgap+ms_width)*m, z4])
    Box(copper, 1, start, stop, padname = None)
    stop[0] = m*0.5*box_length
    Port(em, start, stop, direction='x', z=50)
    # end grounds
    start = np.array([m*0.5*box_length, ymin, z1])
    stop  = np.array([m*(x+0.3e-3), ymax, z2])
    Box(copper, 1, start, stop, padname = None)

# top and bottom grounds
for y in [[ymin, ymin-ledge+yshift], [ymax, ymax+ledge+yshift]]:
    for z in [[z3, z4], [z1, z2]]:
        start = np.array([m*0.5*box_length, y[0], z[0]])
        stop  = np.array([m*-0.5*box_length, y[1], z[1]])
        Box(copper, 1, start, stop, padname = None)

# substrate
start = np.array([-0.5*box_length, ymin, z2])
stop  = np.array([0.5*box_length, ymax, z3])
Box(sub, 1, start, stop)

em.write_kicad(em.name)
command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
print(command)
em.run_openems(command)
