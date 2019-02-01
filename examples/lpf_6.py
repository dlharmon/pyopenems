#!/usr/bin/env python3
import sys
from scipy.constants import pi, c, epsilon_0, mu_0, mil, inch
mm = 0.001
import openems
import openems.lpf
import numpy as np

em = openems.OpenEMS('lpf_6')
em.end_criteria = 1e-6
em.fmin = 1e6
em.fmax = 20e9
em.fsteps = 1601
fc = 6e9;
sub = openems.Dielectric(em, 'fr408', eps_r=3.66, tand=0.012, fc=fc)

foil_thickness = 0.035*mm
substrate_thickness = 6.6*mil
ms_air_above = 1.0*mm
z = [0.0, substrate_thickness, substrate_thickness + foil_thickness]
em.mesh.AddLine('z', z[2] + ms_air_above)

from math import sqrt
em.resolution = c/(em.fmax*sqrt(3.0))/100.0

lpf = openems.lpf.generate(
    em,
    sub = sub,
    z = z,
    port_length = 0.1*mm,
    ms_width = 0.36*mm,
    section = np.array([[1.5*mm, 0.127*mm],
                        [1.3*mm, 1.5*mm],
                        [4.0*mm, 0.127*mm],
                        [1.7*mm, 1.5*mm],
                        [4.0*mm, 0.127*mm],
                        [1.3*mm, 1.5*mm],
                        [1.5*mm, 0.127*mm]]),
    box_width = 1.8*mm)

em.write_kicad(em.name)
command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
em.run_openems(command)
