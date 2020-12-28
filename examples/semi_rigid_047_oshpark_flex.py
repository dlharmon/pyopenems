#!/usr/bin/env python3
# UT-047 to OSHPark flex
import sys
from scipy.constants import pi, c, mil
mm = 0.001
from openems import OpenEMS, Box, Cylinder, Port, Metal, Dielectric, Polygon, arc
import numpy as np

em = OpenEMS(
    'semi_rigid_047_oshpark_flex',
    EndCriteria = 1e-6,
    fmin = 0e6,
    fmax = 60e9,
    fsteps = 1001,
    boundaries = ['PEC', 'PML_16', 'PEC', 'PEC', 'PEC', 'PEC'],
)
copper = Metal(em, 'copper')
copper_shield = Metal(em, 'copper_shield')
copper_ms = Metal(em, 'copper_ms')
sub = Dielectric(em, 'ro4350b', eps_r=3.2, tand=0.0035, fc=em.fmax)
teflon = Dielectric(em, 'teflon', eps_r=2.1, tand=0.0002, fc=em.fmax)

foil_thickness = 0.05*mm
substrate_thickness = 4*mil
box_length = 4*mm
box_width = 2.2*mm
ms_width = 0.19*mm
board_gap = 0

# coax
pin_radius = 0.5*11.3*mil
dielectric_radius = 0.5*37*mil

box_height = dielectric_radius

# dimensions Z
foil_top = -(pin_radius)
substrate_top = foil_top - foil_thickness
substrate_bottom = substrate_top - substrate_thickness

em.resolution = [50e-6, 25e-6, 25e-6]

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
ypad = 0.3e-3
xpad = -0.62e-3
xpad2 = -0.8e-3
xpad1 = -0.1e-3
points = np.array([
    [0,0], [xpad1, ypad], [xpad, ypad], [xpad2, 0], [xpad, -ypad], [xpad1, -ypad]])
Polygon(copper, points, [substrate_top, foil_top], is_custom_pad=True, pad_name='1', x=0.5*xpad, y=0)

# solder
start = np.array([-0.5*mm, pin_radius, 0])
stop  = np.array([0, -pin_radius, foil_top])
Box(Metal(em, 'solder'), 1, start, stop, padname = None)

z1 = substrate_bottom - foil_thickness
z2 = -(dielectric_radius + 1e-4)

gp = Metal(em, 'groundplane')
y1 = ypad-20e-6
x1 = xpad2-00e-6
points = np.array([
    [x1,y1], [0, y1], [0, 0.5*box_width], [-0.5*box_length, 0.5*box_width]])
Polygon(
    copper,
    np.concatenate((points, points[::-1]*[1,-1])),
    [z1, substrate_bottom], is_custom_pad=True, pcb_layer='B.Cu', pad_name='2', x=x1-0.3e-3, y=0)

angle = np.arccos(-z1/dielectric_radius)

# shield
start = np.array([0.5*box_length, 0.5*box_width, 1*mm])
stop  = np.array([board_gap, -0.5*box_width, -1*mm])
Box(copper_shield, 1, start, stop, padname = None)

# dielectric
start = np.array([0.5*box_length, 0, 0])
stop  = np.array([board_gap, 0, 0])
Cylinder(teflon, 2, start, stop, dielectric_radius)

# pin
start = np.array([0.5*box_length, 0, 0])
stop  = np.array([-0.5*mm, 0, 0])
Cylinder(copper, 3, start, stop, pin_radius)

em.write_kicad(em.name)
command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
print(command)
em.run_openems(command)
