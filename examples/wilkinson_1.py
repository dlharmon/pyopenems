#!/usr/bin/env python3
import sys
import openems
from openems import wilkinson

em = openems.OpenEMS('wilkinson_1', EndCriteria = 1e-4, fmin = 0e6, fmax = 5e9, fsteps=1601)

fc = 1e9
sub = openems.Dielectric(em, 'ro4350b', eps_r=3.66, tand=0.012, fc=fc)

foil_thickness = 35e-6
substrate_thickness = 180e-6
ms_air_above = 700e-6
z = [0.0, substrate_thickness, substrate_thickness + foil_thickness]
em.mesh.AddLine('z', z[2] + ms_air_above)

em.resolution = 50e-6

wilkinson.generate(
    em,
    y1 = 5.5e-3,
    y2 = 500e-6,
    r = 200e-6,
    rv = [None, None, None, 100],
    w = [175e-6]*4,
    substrate = sub,
    z = z,
    port_length = 100e-6,
    ms_width = 360e-6)

em.write_kicad(em.name, mirror = '')
command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
em.run_openems(command)
