#!/usr/bin/env python3
import sys
from scipy.constants import pi, c, epsilon_0, mu_0, mil, inch
mm = 0.001
import openems
import openems.idbpf_tapped
import numpy as np

idx = int(sys.argv[1])
name = 'idbpf_{}'.format(idx)
fmax = [0,0,0,8e9,8e9,10e9,12e9][idx]
em = openems.OpenEMS(name, fmin=0, fmax=fmax, fsteps=400, EndCriteria=1e-5)
fc = [0, 0, 0, 3e9, 4e9, 5e9, 6e9][idx]
pec = openems.Metal(em, 'pec')
sub = openems.Dielectric(em, 'sub', eps_r=3.3, tand = 0.012, fc=fc)

foil_thickness = 0.04*mm
substrate_thickness = 0.18*mm
ms_air_above = 1.0*mm
via = 0.4*mm
via_pad = 0.8*mm

# dimensions Z
substrate_bottom = 0.0
substrate_top = substrate_bottom + substrate_thickness
foil_top = substrate_top + foil_thickness
em.mesh.AddLine('z', foil_top + ms_air_above)

em.resolution = [0.1*mm, 0.04*mm, 0.5*mm]

rl = [0,0,0,14.4*mm,10.8*mm,8.5*mm,7.1*mm][idx]
rl = [rl]*6
rl[0] += [0,0,0,0.95*mm,0.8*mm,0.6*mm,0.6*mm][idx]

etch = 0.0 # etch error
openems.idbpf_tapped.idbpf(
    em,
    sub = sub,
    tapoffset=[0,0,0,5.1*mm,3.8*mm,3.05*mm,2.5*mm][idx],
    rl = rl,
    rw = np.array([0.36*mm]*6) - etch,
    space = np.array([0.15*mm, 0.19*mm]) + etch,
    via_padradius = 0.5*via_pad,
    via_radius = 0.5*via,
    feedwidth = 0.36*mm,
    portlength = 0.3*mm,
    z = [substrate_bottom, substrate_top, foil_top],
    endmetal = False
)

em.write_kicad(name)

command = 'view solve'
if len(sys.argv) > 2:
    command = sys.argv[2]
em.xgrid = np.linspace(0, fmax/1e9, 1+int(fmax/1e9))
em.ygrid = np.linspace(-50.0, 0, 11)
em.run_openems(command)
