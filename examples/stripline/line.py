#!/usr/bin/env python3
import sys
from scipy.constants import pi, c, epsilon_0, mu_0, mil
mm = 0.001
import openems
import numpy as np

em = openems.OpenEMS('line', EndCriteria = 1e-6)
em.fmin = 1e6
em.fmax = 40e9
em.fsteps = 1601
fc = 40e9
pec = openems.Metal(em, 'pec')
sub = openems.Dielectric(em, 'fr4', eps_r=3.9, tand=0.0035, fc=fc)
foil_thickness = 0.6*mil
substrate_thickness = 0.2*mm
ms_air_above = 0.36*mm
port_length = 0.1*mm
box_length = 10*mm
box_width = 1*mm
ms_width = 0.2*mm
# dimensions Z
substrate_bottom = 0.0
substrate_top = substrate_bottom + substrate_thickness
foil_top = substrate_top + foil_thickness

from math import sqrt
em.resolution = c/(em.fmax*sqrt(3.0))/100.0

# substrate
start = np.array([0.5*box_length, 0.5*box_width, substrate_bottom])
stop  = openems.mirror(start, 'xy') + np.array([0, 0, substrate_top+ms_air_above])
sub.AddBox(start, stop, 1);

# line
start = np.array([0.5*box_length-port_length, 0.5*ms_width, substrate_top])
stop  = np.array([0, -0.5*ms_width, foil_top])
for m in [[1,1,1], [-1,1,1]]:
    pec.AddBox(start*m, stop*m, 2)

# ports
start = np.array([-0.5*box_length, ms_width/2.0, substrate_top])
stop  = np.array([-0.5*box_length + port_length, ms_width/-2.0, foil_top])
for m in [[1,1,1], [-1,-1,1]]:
    openems.Port(em, start*m, stop*m, direction='x', z=50)

em.write_kicad(em.name)
command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
print(command)
em.run_openems(command)
