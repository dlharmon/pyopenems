#!/usr/bin/env python3
import sys
import openems
import openems.LPF_DGS_bowtie
import numpy as np

em = openems.OpenEMS('LPF_DGS_bowtie_7', EndCriteria = 1e-5, fmin = 0e6, fmax = 30e9, fsteps = 1601)
em.resolution = [50e-6, 50e-6, 500e-6]

fc = 6e9

foil_thickness = 35e-6
substrate_thickness = 100e-6

z = np.zeros(6)
z[1] = 1.6e-3
z[2] = z[1] + foil_thickness
z[3] = z[2] + substrate_thickness
z[4] = z[3] + foil_thickness
z[5] = z[4] + 1.6e-3

openems.LPF_DGS_bowtie.generate(
    em,
    sub = openems.Dielectric(em, 'polyimide', eps_r=3.2, tand=0.002, fc=fc),
    mask = openems.Dielectric(em, 'soldermask', eps_r=3.3, tand=0.020, fc=fc),
    min_width = 152e-6,
    cutout_width = 1.0e-3,
    inductors = 0.15e-3 + 1.55*np.array([1.7e-3, 1.96e-3, 2e-3]),
    capacitors = 1.45*np.array([0.47e-3, 0.77e-3, 0.81e-3, 0.82e-3]),
    z = z,
    port_length = 75e-6,
    ms_width = 195e-6,
    box_width = 3e-3)

em.write_kicad(em.name)
command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
em.run_openems(command)
