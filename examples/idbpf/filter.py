#!/usr/bin/env python
import sys
from scipy.constants import pi, c, epsilon_0, mu_0, mil, inch
mm = 0.001
import openems
import openems.idbpf
import numpy as np

em = openems.OpenEMS('idbpf_b3', fmin = 1e6, fmax = 16e9)
em.end_criteria = 1e-10
em.fsteps = 1601
fc = 7.12e9;
eps_r = 3.66
#em.add_lossy_metal('copper', frequency=fc, conductivity=56e6/3, ur=1.0)
openems.Metal(em, 'copper')
openems.Metal(em, 'pec')
#em.via_offset_x = 5*mil
#em.via_offset_y = 5*mil
openems.Dielectric(em, 'sub', eps_r=eps_r).set_tanD(0.0035, freq=fc)
        
foil_thickness = 0.035*mm
substrate_thickness = 22*mil
ms_air_above = 2.0*mm
via = 0.3*mm
via_pad = 0.6*mm

# dimensions Z
substrate_bottom = 0.0
substrate_top = substrate_bottom + substrate_thickness
foil_top = substrate_top + foil_thickness
em.mesh.add_z(foil_top + ms_air_above)

from math import sqrt
em.resolution = c/(em.fmax*sqrt(eps_r)) /100.0;

etch = 0.0 # etch error
bpf = openems.idbpf.IDBPF(em,
                          rl = [6.1*mm]*6,
                          rw = np.array([0.3*mm]*6) - etch,
                          space = np.array([0.15*mm, 0.50*mm, 0.61*mm, 0.66*mm, 0.66*mm]) + etch,
                          via_padradius = 0.3*mm,
                          via_radius = 0.15*mm,
                          feedwidth = 0.3*mm,
                          feedgap = 0.2*mm,
                          portlength = 0.2*mm,
                          inner_metal = True,
                          inner_metal_z = [[substrate_top-6.6*mil,substrate_top-(6.6*mil + 1.4*mil)],[substrate_bottom+6.6*mil,substrate_bottom+(6.6*mil + 1.4*mil)]],
                          z = [substrate_bottom, substrate_top, foil_top])
bpf.rl[1] -= 0.025*mm
bpf.generate()

em.write_kicad(em.name)
em.write_kicad(em.name+"_m", mirror='y')
command = 'view solve'
if len(sys.argv) > 1:
    command = sys.argv[1]
print command
f1 = 6.34
f2 = 8.0
em.xgrid = [0, f1/2.0, f2/2.0, f1, f2, 1.5*f1, 1.5*f2, em.fmax*1.0e-9]
em.ygrid = np.linspace(-50.0, 0, 11)
em.run_openems(command)
