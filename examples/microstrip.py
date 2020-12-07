#!/usr/bin/env python3
import sys
mm = 0.001
from openems import OpenEMS, Box, Cylinder, Port, Metal, Dielectric
import numpy as np

em = OpenEMS('microstrip', EndCriteria = 1e-5, fmin = 0e6, fmax = 60e9, fsteps = 1601)
copper = Metal(em, 'copper')
sub = Dielectric(em, 'substrate', eps_r=3.2)

foil_thickness = 0.036*mm
box_length = 5*mm
box_width = 2.5*mm
box_top = 1.5*mm

port_length = 0.1*mm
substrate_top = 0.166*mm
ms_width = 0.35*mm

# oshpark flex
port_length = 0.065*mm
substrate_top = 4*25.4e-6
ms_width = 0.21*mm
box_width = 1.5*mm
box_top = 1*mm

foil_top = substrate_top + foil_thickness

em.resolution = 10e-6

em.mesh.AddLine('z', foil_top + box_top)

# substrate
start = np.array([-0.5*box_length, 0.5*box_width, 0])
stop  = np.array([0.5*box_length, -0.5*box_width, substrate_top])
sub.AddBox(start, stop, priority=2)

# line
start = np.array([-0.5*box_length+port_length, 0.5*ms_width, substrate_top])
stop  = np.array([0.5*box_length-port_length, -0.5*ms_width, foil_top])
copper.AddBox(start, stop, padname = '1', priority=9)

# port (ms)
start = [-0.5*box_length, ms_width/2.0, substrate_top]
stop  = [-0.5*box_length + port_length, ms_width/-2.0, foil_top]
Port(em, start, stop, direction='x', z=50)

# port (ms)
start = [0.5*box_length, ms_width/2.0, substrate_top]
stop  = [0.5*box_length - port_length, ms_width/-2.0, foil_top]
Port(em, start, stop, direction='x', z=50)

command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
em.run_openems(command)
