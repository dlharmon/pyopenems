#!/usr/bin/env python
import sys
from scipy.constants import pi, c, epsilon_0, mu_0, mil, inch
mm = 0.001
import openems
import numpy as np

em = openems.OpenEMS('bend', fmin = 1e6, fmax = 110e9)
em.end_criteria = 1e-6
em.fsteps = 1601
em.boundaries = "'PEC' 'PEC' 'PEC' 'PEC' 'PEC' 'PEC'"
fc = em.fmax
#em.add_lossy_metal('copper', frequency=fc)
em.add_metal('copper')
em.add_metal('pec')
em.add_dielectric('alumina', eps_r=9.8)
em.add_dielectric('is680', eps_r=3.0).set_tanD(0.0035, freq=fc)
        
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
em.mesh.add_z(foil_top + ms_air_above)

from math import sqrt
em.resolution = c/(f_max*sqrt(3.0)) /130.0; #resolution of lambda/50

# substrate
start = np.array([0.5*box_length, 0.5*box_width, substrate_bottom])
stop  = openems.mirror(start, 'xy') + np.array([0, 0, substrate_top])
em.add_box('sub', 'is680', 1, start, stop);

# line
start = np.array([-0.5*box_length+port_length, 0.5*ms_width, substrate_top])
stop  = np.array([0.5*ms_width-notch, -0.5*ms_width, foil_top])
em.add_box('line', 'copper', 1, start, stop)

# ground via
start = np.array([1.55*mm, 0.5*ms_width+0.15*mm, foil_top])
stop  = np.array([0.5*box_length, 0.5*box_width, 0.0])
#em.add_box('via', 'copper', 10, start, stop)
start = np.array([-0.5*ms_width-0.15*mm, 0.5*ms_width+0.15*mm, foil_top])
stop  = np.array([-0.5*box_length, 0.5*box_width, 0.0])
#em.add_box('via2', 'copper', 10, start, stop)
start = np.array([-0.5*box_length, -0.5*ms_width-0.15*mm, foil_top])
stop  = np.array([0.5*box_length, -0.5*box_width, 0.0])
#em.add_box('via3', 'copper', 10, start, stop)

# line
start = np.array([0.5*ms_width, 0.5*box_width-port_length, substrate_top])
stop  = np.array([-0.5*ms_width, -0.5*ms_width+notch, foil_top])
em.add_box('line2', 'copper', 1, start, stop)

# common port
start = [0.5*ms_width, 0.5*box_width, substrate_top]
stop  = [-0.5*ms_width, 0.5*box_width-port_length, foil_top]
em.add_port(start, stop, direction='y', z=50)

# ports
start = [-0.5*box_length, ms_width/2.0, substrate_top]
stop  = [-0.5*box_length + port_length, ms_width/-2.0, foil_top]
em.add_port(start, stop, direction='x', z=50)

em.write_kicad(em.name)
command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
print command
em.run_openems(command)
