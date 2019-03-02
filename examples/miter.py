#!/usr/bin/env python3
import sys
from scipy.constants import pi, c, epsilon_0, mu_0, mil, inch
mm = 0.001
import openems
import openems.miter
import numpy as np

em = openems.OpenEMS('miter_6.6')
em.end_criteria = 1e-6
em.fmin = 0
em.fmax = 40e9
em.fsteps = 1601
fc = 40e9
pec = openems.Metal(em, 'pec')
sub = openems.Dielectric(em, 'ro4350b', eps_r=3.66, tand=0.0035, fc=fc)

foil_thickness = 0.033*mm
substrate_thickness = 6.6*mil
ms_air_above = 1.0*mm
z = [0.0, substrate_thickness, substrate_thickness + foil_thickness]
em.mesh.AddLine('z', z[2] + ms_air_above)

em.resolution = 50e-6

openems.miter.generate(
    em,
    pec,
    sub,
    miter = 0.35 * mm,
    z = z,
    port_length = 0.1 * mm,
    ms_width = 0.3 *mm,
    box_size = 1.2*mm)

em.write_kicad(em.name, mirror = '')
em.write_kicad(em.name+'_m', mirror = 'y')
command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
print(command)
em.run_openems(command)
