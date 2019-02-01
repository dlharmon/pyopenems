#!/usr/bin/env python3
import sys
from scipy.constants import pi, c, epsilon_0, mu_0, mil, inch
mm = 0.001
import openems
import openems.lpf
import numpy as np

em = openems.OpenEMS('lpf_13')
em.end_criteria = 1e-6
em.fmin = 1e6
em.fmax = 30e9
em.fsteps = 1601
fc = 13e9;
sub = openems.Dielectric(em, 'fr408', eps_r=3.66, tand=0.012, fc=fc)

foil_thickness = 0.035*mm
substrate_thickness = 6.6*mil
ms_air_above = 1.0*mm
z = [0.0, substrate_thickness, substrate_thickness + foil_thickness]
em.mesh.AddLine('z', z[2] + ms_air_above)

em.resolution = 50e-6
wide = 1.1*mm
narrow = 0.11*mm

lpf = openems.lpf.generate(
    em,
    sub = sub,
    z = z,
    port_length = 0.1*mm,
    ms_width = 0.36*mm,
    section = np.array([[0.75*mm, narrow],
                        [0.65*mm, wide],
                        [2.0*mm, narrow],
                        [0.75*mm, wide],
                        [2.0*mm, narrow],
                        [0.65*mm, wide],
                        [0.75*mm, narrow]]),
    box_width = 1.8*mm)

em.write_kicad(em.name)
command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
em.run_openems(command)
