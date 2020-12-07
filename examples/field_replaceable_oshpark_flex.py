#!/usr/bin/env python3
# 0.020" pin to OSHPark flex
import sys
from scipy.constants import pi, c, epsilon_0, mu_0, mil, inch
mm = 0.001
from openems import OpenEMS, Box, Cylinder, Port, Metal, Dielectric, Polygon, arc
import numpy as np
use_PML_coax = True

em = OpenEMS(
    'field_replaceable_to_oshpark_flex',
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

foil_thickness = 0.035*mm
substrate_thickness = 4*mil
port_length = 0.15*mm
box_length = 3*mm
box_width = 2*mm
ms_width = 0.21*mm
board_gap = 0.1*mm

# coax
pin_radius = 254e-6
dielectric_radius = 0.5*67*mil
coax_port_length = 0.2*mm

box_height = dielectric_radius

# dimensions Z
foil_top = -(pin_radius)
substrate_top = foil_top - foil_thickness
substrate_bottom = substrate_top - substrate_thickness

em.resolution = [50e-6, 15e-6, 15e-6]

# substrate
start = np.array([-0.5*box_length, 0.5*box_width, substrate_bottom])
stop  = np.array([0.0, -0.5*box_width, substrate_top])
Box(sub, 1, start, stop);

# line
port_length = 0.065*mm
start = np.array([-0.5*box_length+port_length, 0.5*ms_width, substrate_top])
stop  = np.array([0, -0.5*ms_width, foil_top])
Box(copper_ms, 1, start, stop, padname = None)

# port (ms)
stop[0] = -0.5*box_length
Port(em, start, stop, direction='x', z=50)

# pad
ypad = 0.38e-3
xpad = -0.62e-3
xpad2 = -0.8e-3

points = np.array([
    [0, ypad], [xpad, ypad], [xpad2, 0], [xpad, -ypad], [0, -ypad]])
Polygon(copper, points, [substrate_top, foil_top], is_custom_pad=True, pad_name='1', x=0.5*xpad, y=0)

# solder
start = np.array([-0.5*mm, pin_radius, 0])
stop  = np.array([0, -pin_radius, foil_top])
Box(Metal(em, 'solder'), 1, start, stop, padname = None)

z1 = substrate_bottom - foil_thickness
z2 = -(dielectric_radius + 1e-4)

gp = Metal(em, 'groundplane')
y1 = ypad+20e-6
x1 = xpad2-00e-6
points = np.array([
    [x1,y1], [0, y1], [0, 0.5*box_width], [-0.5*box_length, 0.5*box_width]])
Polygon(
    copper,
    np.concatenate((points, points[::-1]*[1,-1])),
    [z1, substrate_bottom], is_custom_pad=True, pcb_layer='B.Cu', pad_name='2', x=x1-0.3e-3, y=0)

angle = np.arccos(-z1/dielectric_radius)
# in yz plane
points = np.array([
    [0.5*box_width,z1],
    [0.5*box_width,z2],
    [-0.5*box_width,z2],
    [-0.5*box_width,z1]])
pin_arc = arc(0,0, dielectric_radius, 1.5*pi-angle, 1.5*pi+angle)
Polygon(copper_shield,
	points = np.concatenate((points, pin_arc)),
        elevation = [board_gap, -0.5*box_length],
        normal_direction = 'x',
        pcb_layer=None
)

# shield
start = np.array([0.5*box_length, 0.5*box_width, dielectric_radius])
stop  = np.array([board_gap, -0.5*box_width, -dielectric_radius])
Box(copper_shield, 1, start, stop, padname = None)

# dielectric
start = np.array([0.5*box_length, 0, 0])
stop  = np.array([board_gap, 0, 0])
Cylinder(teflon, 2, start, stop, dielectric_radius)

# pin
start = np.array([0.5*box_length - coax_port_length, 0, 0])
if use_PML_coax:
    start = np.array([0.5*box_length, 0, 0])
stop  = np.array([-0.5*mm, 0, 0])
Cylinder(copper, 3, start, stop, pin_radius)

# port (coax)
start = [0.5*box_length, -0.5*coax_port_length, -0.5*coax_port_length]
stop  = [0.5*box_length - coax_port_length, 0.5*coax_port_length, 0.5*coax_port_length]
if not use_PML_coax:
    Port(em, start, stop, direction='x', z=50)

em.write_kicad(em.name)
command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
print(command)
em.run_openems(command)
