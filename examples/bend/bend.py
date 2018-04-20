#!/usr/bin/env python3
import sys
from scipy.constants import pi, c, epsilon_0, mu_0, mil, inch
mm = 0.001
import openems
import numpy as np

em = openems.OpenEMS('bend', fmin = 1e6, fmax = 110e9)
em.end_criteria = 1e-6
em.fsteps = 1601
fc = em.fmax
copper = openems.Metal(em, 'copper')
pec = openems.Metal(em, 'pec')
Alumina = openems.Dielectric(em, 'alumina', eps_r=9.8)
is680 = openems.Dielectric(em, 'is680', eps_r=3.0, tand=0.0035, fc=fc)

f_max = em.fmax
foil_thickness = 0.035*mm;
substrate_thickness = 20*mil/4;
ms_air_above = 2.0*mm/4;
port_length = 0.3*mm/4;
box_length = 4*mm/4
box_width = 4*mm/4
ms_width = 1.1*mm/4
notch = 0.9*mm/4
# dimensions Z
substrate_bottom = 0.0
substrate_top = substrate_bottom + substrate_thickness
foil_top = substrate_top + foil_thickness
em.mesh.AddLine('z', foil_top + ms_air_above)

from math import sqrt
em.resolution = c/(f_max*sqrt(3.0)) /130.0; #resolution of lambda/50

# substrate
start = np.array([0.5*box_length, 0.5*box_width, substrate_bottom])
stop  = openems.mirror(start, 'xy') + np.array([0, 0, substrate_top])
openems.Box(is680, 1, start, stop)

# line
start = np.array([-0.5*box_length+port_length, 0.5*ms_width, substrate_top])
stop  = np.array([0.5*ms_width-notch, -0.5*ms_width, foil_top])
openems.Box(copper, 1, start, stop)

# ground via
start = np.array([1.55*mm, 0.5*ms_width+0.15*mm, foil_top])
stop  = np.array([0.5*box_length, 0.5*box_width, 0.0])
#copper.AddBox(start, stop, 10)
start = np.array([-0.5*ms_width-0.15*mm, 0.5*ms_width+0.15*mm, foil_top])
stop  = np.array([-0.5*box_length, 0.5*box_width, 0.0])
#copper.AddBox(start, stop, 10)
start = np.array([-0.5*box_length, -0.5*ms_width-0.15*mm, foil_top])
stop  = np.array([0.5*box_length, -0.5*box_width, 0.0])
#copper.AddBox(start, stop, 10)

# line
start = np.array([0.5*ms_width, 0.5*box_width-port_length, substrate_top])
stop  = np.array([-0.5*ms_width, -0.5*ms_width+notch, foil_top])
openems.Box(copper, 1, start, stop)

# common port
start = [0.5*ms_width, 0.5*box_width, substrate_top]
stop  = [-0.5*ms_width, 0.5*box_width-port_length, foil_top]
openems.Port(em, start, stop, direction='y', z=50)

# ports
start = [-0.5*box_length, ms_width/2.0, substrate_top]
stop  = [-0.5*box_length + port_length, ms_width/-2.0, foil_top]
openems.Port(em,start, stop, direction='x', z=50)

em.write_kicad(em.name)
command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
print(command)
em.run_openems(command)
