#!/usr/bin/env python3
import sys
from scipy.constants import mil
from openems import OpenEMS, Box, Cylinder, Port, Metal, Dielectric
import numpy as np

em = OpenEMS('sma_th', EndCriteria = 1e-6, fmin = 0, fmax = 20e9, fsteps = 1601)
em.resolution = 8e-5
copper = Metal(em, 'copper')
copper_shield = Metal(em, 'copper_shield')
ro4350b = Dielectric(em, 'ro4350b', eps_r=3.66, tand=0.0035, fc=em.fmax)
teflon = Dielectric(em, 'teflon', eps_r=2.1, tand=0.0002, fc=em.fmax)

foil_thickness = 0.035e-3
substrate_thickness = 62*mil
port_length = 1.0e-3
box_length = 6e-3
box_width = 6e-3
box_height = 7e-3
ms_width = 2.5e-3

# coax
pin_diameter = 1.27e-3
dielectric_diameter = 4.2e-3
coax_port_length = 0.4e-3

# dimensions Z
foil_top = -0.5*pin_diameter
substrate_top = foil_top - foil_thickness
substrate_bottom = substrate_top - substrate_thickness

em.mesh.AddLine('z', 0.5*box_height)

# substrate
Box(ro4350b, 1,
    [-0.5*box_length, 0.5*box_width, substrate_bottom],
    [0.5*box_length, -0.5*box_width, substrate_top]
)

# line
start = np.array([-0.5*box_length+port_length, 0.5*ms_width, substrate_top])
stop  = np.array([0, -0.5*ms_width, foil_top])
Box(copper, 1, start, stop, padname = '1')

# via top
Cylinder(copper, 2, [0, 0, substrate_top], [0, 0, foil_top], 0.5*ms_width)

# ground top
start = np.array([-0.5*box_length, -0.5*ms_width-0.5e-3, foil_top])
stop  = np.array([0.5*box_length, -0.5*box_width, substrate_top])
for m in ['', 'y']:
    Box(copper, 10, start, stop, padname = '2', mirror=m)

# ground via
start = np.array([-0.5*box_length, -0.5*ms_width-1.0e-3, substrate_top])
stop  = np.array([0.5*box_length, -0.5*box_width, substrate_bottom])
for m in ['', 'y']:
    Box(copper, 10, start, stop, padname = None, mirror=m)

# port (ms)
start = [-0.5*box_length, ms_width/2.0, substrate_top]
stop  = [-0.5*box_length + port_length, ms_width/-2.0, foil_top]
Port(em, start, stop, direction='x', z=50)

# shield
start = np.array([0.5*box_length, 0.5*box_width, substrate_bottom])
stop  = np.array([-0.5*box_length, -0.5*box_width, -0.5*box_height])
Box(copper_shield, 1, start, stop, padname = None)

# dielectric
start = np.array([0, 0, substrate_bottom])
stop  = np.array([0, 0, -0.5*box_height])
Cylinder(teflon, 2, start, stop, 0.5*dielectric_diameter)

# pin
start = np.array([0, 0, substrate_top + 0.5e-3])
stop  = np.array([0, 0, -0.5*box_height + coax_port_length])
Cylinder(copper, 3, start, stop, 0.5*pin_diameter)

# port (coax)
start = [0.5*coax_port_length, 0.5*coax_port_length, -0.5*box_height + coax_port_length]
stop  = [-0.5*coax_port_length, -0.5*coax_port_length, -0.5*box_height]
Port(em, start, stop, direction='z', z=50)

em.write_kicad(em.name)
command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
print(command)
em.run_openems(command)
