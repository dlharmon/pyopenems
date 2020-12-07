#!/usr/bin/env python3
# Common SMA edge launch to OSHPark 4 layer
import sys
from scipy.constants import mil
import openems
import numpy as np

em = openems.OpenEMS('sma_el', EndCriteria = 1e-6,  fmin = 0, fmax = 20e9, fsteps = 1001)
em.resolution = 8e-5
copper = openems.Metal(em, 'copper')
copper_shield = openems.Metal(em, 'copper_shield')
sub = openems.Dielectric(em, 'ro4350b', eps_r=3.66, tand=0.0035, fc=em.fmax)
teflon = openems.Dielectric(em, 'teflon', eps_r=2.1, tand=0.0002, fc=em.fmax)

foil_thickness = 35e-6
substrate_thickness = 62*mil-7*mil
port_length = 300e-6
box_length = 10e-3
box_width = 6e-3
box_height = 6e-3
ms_width = 1.0e-3
board_gap = 0.0

# coax
coax_scale = 2.0
pin_diameter = 0.5e-3*coax_scale
dielectric_diameter = 1.67e-3*coax_scale
coax_port_length = 0.2e-3*coax_scale

# dimensions Z
foil_top = -0.5*pin_diameter
substrate_top = foil_top - foil_thickness
substrate_bottom = substrate_top - substrate_thickness

# substrate
start = np.array([-0.5*box_length, 0.5*box_width, substrate_bottom])
stop  = np.array([0.0, -0.5*box_width, substrate_top])
openems.Box(sub, 1, start, stop);

# line
start = np.array([-0.5*box_length+port_length, 0.5*ms_width, substrate_top])
stop  = np.array([0, -0.5*ms_width, foil_top])
openems.Box(copper, 1, start, stop, padname = '1')

# solder
start = np.array([-0.5e-3, 0.5*pin_diameter, foil_top+0.5*pin_diameter])
stop  = np.array([0, -0.5*pin_diameter, foil_top])
openems.Box(copper, 1, start, stop, padname = None)

# ground via
start = np.array([-0.5*box_length, -0.5*ms_width-0.2e-3, foil_top])
stop  = np.array([0.0, -0.5*box_width, substrate_top])
for m in [[1,1,1], [1,-1,1]]:
    openems.Box(copper, 10, start*m, stop*m, padname = '2')

# ground via
start = np.array([-0.5*box_length, -0.5*ms_width-0.3e-3, substrate_top])
stop  = np.array([0.0, -0.5*box_width, substrate_bottom])
for m in [[1,1,1], [1,-1,1]]:
    openems.Box(copper, 10, m*start, m*stop, padname = None)

# ground
start = np.array([-0.5*box_length, 0.5*box_width, substrate_bottom])
stop  = np.array([board_gap, -0.5*box_width, -0.5*box_height])
openems.Box(copper, 10, start, stop, padname = None)

# port (ms)
start = [-0.5*box_length, 0.5*ms_width, substrate_top]
stop  = [-0.5*box_length + port_length, -0.5*ms_width, foil_top]
openems.Port(em, start, stop, direction='x', z=50)

# shield
start = np.array([0.5*box_length, 0.5*box_width, 0.5*box_height])
stop  = np.array([board_gap, -0.5*box_width, -0.5*box_height])
openems.Box(copper_shield, 1, start, stop, padname = None)

# dielectric
start = np.array([0.5*box_length, 0, 0])
stop  = np.array([board_gap, 0, 0])
openems.Cylinder(teflon, 2, start, stop, 0.5*dielectric_diameter)

# pin
start = np.array([0.5*box_length - coax_port_length, 0, 0])
stop  = np.array([-0.5e-3, 0, 0])
openems.Cylinder(copper, 3, start, stop, 0.5*pin_diameter)

# port (coax)
start = [0.5*box_length, -0.25*coax_port_length, -0.25*coax_port_length]
stop  = [0.5*box_length - coax_port_length, 0.25*coax_port_length, 0.25*coax_port_length]
openems.Port(em, start, stop, direction='x', z=50)

em.write_kicad(em.name)
command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
em.run_openems(command)
