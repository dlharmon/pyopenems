#!/usr/bin/env python3
import sys
from scipy.constants import pi, c, mil
from openems import OpenEMS, Box, Cylinder, Port, Metal, Dielectric, Polygon, arc
import numpy as np
use_PML_coax = True

em = OpenEMS(
    'suspended_substrate_stripline',
    EndCriteria = 1e-6,
    fmin = 0e6,
    fmax = 60e9,
    fsteps = 1001,
    boundaries = ['PEC', 'PML_16' if use_PML_coax else 'PEC', 'PEC', 'PEC', 'PEC', 'PEC'],
)
copper = Metal(em, 'copper')
copper_shield = Metal(em, 'copper_shield')
copper_ms = Metal(em, 'copper_ms')
sub = Dielectric(em, 'ro4350b', eps_r=3.2, tand=0.0035, fc=em.fmax)
teflon = Dielectric(em, 'teflon', eps_r=2.1, tand=0.0002, fc=em.fmax)

foil_thickness = 0.035e-3
substrate_thickness = 4*mil
port_length = 0.15e-3
box_width = 2e-3
box_length = 5e-3
ms_width = 0.21e-3
3
# coax
pin_radius = 254e-6
dielectric_radius = 0.5*67*mil
coax_port_length = 0.2e-3

# dimensions Z
foil_top = 0
substrate_top = foil_top - foil_thickness
substrate_bottom = substrate_top - substrate_thickness

em.resolution = [50e-6, 25e-6, 25e-6]

em.mesh.AddLine('z', substrate_bottom - 1e-3)
em.mesh.AddLine('z', substrate_top + 1e-3)

# substrate
start = np.array([-0.5*box_length, 0.5*box_width, substrate_bottom])
stop  = np.array([0.0, -0.5*box_width, substrate_top])
Box(sub, 1, start, stop);

# line
port_length = 0.065e-3
start = np.array([-0.5*box_length+port_length, 0.5*ms_width, substrate_top])
stop  = np.array([0, -0.5*ms_width, foil_top])
Box(copper_ms, 1, start, stop, padname = None)

# port (ms)
stop[0] = -0.5*box_length
Port(em, start, stop, direction='x', z=50)

# pad
ypad = 0.6e-3
xpad = -0.62e-3
xpad2 = -0.8e-3

points = np.array([
    [0, ypad], [xpad, ypad], [xpad2, 0], [xpad, -ypad], [0, -ypad]])
Polygon(copper, points, [substrate_top, foil_top], is_custom_pad=True, pad_name='1', x=0.5*xpad, y=0)

z1 = substrate_bottom - foil_thickness

gp = Metal(em, 'groundplane')
y1 = ypad+200e-6
x1 = xpad2-00e-6
points = np.array([
    [x1,y1], [0, y1], [0, 0.5*box_width], [-0.5*box_length, 0.5*box_width]])
Polygon(
    copper,
    np.concatenate((points, points[::-1]*[1,-1])),
    [z1, substrate_bottom], is_custom_pad=True, pcb_layer='B.Cu', pad_name='2', x=x1-0.3e-3, y=0)

em.write_kicad(em.name)
command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
print(command)
em.run_openems(command)
