#!/usr/bin/env python3
import sys
import openems
import numpy as np

mm = 1e-3 # default unit is the meter
em = openems.OpenEMS(sys.argv[1], EndCriteria = 1e-6, fmin = 0e6, fmax = 60e9)
em.fsteps = 801
copper = openems.Metal(em, 'copper')
sub = openems.Dielectric(em, 'substrate', eps_r=3.2)
mask = openems.Dielectric(em, 'mask', eps_r=3.3)
air = openems.Dielectric(em, 'air', eps_r=1.0006)

foil_thickness = 0.035*mm
port_length = 0.05*mm
box_length = 5*mm
box_width = 1.5*mm
ms_width = 0.190*mm
box_top = 1.5*mm

# dimensions Z
substrate_top = 0.102*mm
foil_top = substrate_top + foil_thickness
em.resolution = 50e-6

em.mesh.AddLine('z', foil_top + box_top)
em.mesh.AddLine('z', -0.5*mm)

# substrate
start = np.array([-0.5*box_length, 0.5*box_width, 0])
stop  = np.array([0.5*box_length, -0.5*box_width, substrate_top])
sub.AddBox(start, stop, priority=2)
start[2] = stop[2] + 25.4e-6
mask.AddBox(start, stop, priority=0)

# bottom foil
start = np.array([-0.5*box_length, 0.5*box_width, 0])
stop  = np.array([0.5*box_length, -0.5*box_width, -foil_thickness])
copper.AddBox(start, stop, priority=2)

if sys.argv[1] == '0201':
    pad_y = 0.5 * 0.3*mm
    pad_x1 = 0.125*mm
    pad_x2 = 0.35*mm
    body_y = 0.15*mm
    body_x = 0.3*mm
    body_z = 0.3*mm
    cutout_x = 0.5 * 0.6*mm
    cutout_y = 0.5 * 0.42*mm

elif sys.argv[1] == '0402':
    pad_y = 0.25*mm
    pad_x1 = 0.25*mm
    pad_x2 = 0.65*mm
    body_y = 0.25*mm
    body_x = 0.5*mm
    body_z = 0.5*mm
    cutout_x = 0.5 * 1.6*mm
    cutout_y = 0.5 * 0.6*mm
else:
    exit()

for xm in [-1,1]:
    # line
    start = np.array([xm*pad_x1, 0.5*ms_width, substrate_top])
    stop  = np.array([xm*0.5*box_length-port_length, -0.5*ms_width, foil_top])
    copper.AddBox(start, stop, priority=9)

    # 0201 pads
    start = np.array([xm*pad_x1,  pad_y, substrate_top])
    stop  = np.array([xm*pad_x2, -pad_y, foil_top])
    copper.AddBox(start, stop, priority=9)

# 0201 body
start = np.array([-body_x, -body_y, foil_top + body_z])
stop  = np.array([ body_x,  body_y, foil_top])
copper.AddBox(start, stop, padname = '1', priority=9)

# ground plane cutout
start = np.array([-cutout_x, -cutout_y, 0])
stop  = np.array([ cutout_x,  cutout_y, -foil_thickness])
air.AddBox(start, stop, priority=9)

# port (ms)
start = [-0.5*box_length, ms_width/2.0, substrate_top]
stop  = [-0.5*box_length + port_length, ms_width/-2.0, foil_top]
openems.Port(em, start, stop, direction='x', z=50)

# port (ms)
start = [0.5*box_length, ms_width/2.0, substrate_top]
stop  = [0.5*box_length - port_length, ms_width/-2.0, foil_top]
openems.Port(em, start, stop, direction='x', z=50)

command = 'view solve'
if len(sys.argv) > 2:
    command = sys.argv[2]
em.run_openems(command)
