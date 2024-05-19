#!/usr/bin/env python3
import sys
mm = 0.001
from openems import OpenEMS, Box, Cylinder, Port, Metal, Dielectric
import numpy as np
import argparse

parser = argparse.ArgumentParser()
#parser.add_argument('--command', type=str, help="text above graph", default="S Parameters")
parser.add_argument('--view', action='store_true', help="view CSXCAD")
parser.add_argument('--solve', action='store_true', help="run solver")
parser.add_argument('--Er', type=float, help="dielectric", default=4.3)
parser.add_argument('--Fc', type=float, help="center frequency", default=12e9)
parser.add_argument('--Fmax', type=float, help="stop frequency", default=60e9)
args = parser.parse_args()

em = OpenEMS('microstrip', EndCriteria = 1e-5, fmin = 0e6, fmax = args.Fmax, fsteps = 1601, boundaries = ['PEC', 'PML_12', 'PEC', 'PEC', 'PEC', 'PEC'])
copper = Metal(em, 'copper')
sub = Dielectric(em, 'substrate', eps_r=args.Er, tand=0.020, fc=args.Fc)

foil_thickness = 0.036*mm
box_length = 5*mm
box_width = 2.5*mm
box_top = 1.5*mm

port_length = 0.065*mm
substrate_top = 100e-6
ms_width = 0.156*mm
box_width = 1*mm
box_top = 0.5*mm

foil_top = substrate_top + foil_thickness

em.resolution = 25e-6

em.mesh.AddLine('z', foil_top + box_top)

# substrate
start = np.array([-0.5*box_length, 0.5*box_width, 0])
stop  = np.array([0.5*box_length, -0.5*box_width, substrate_top])
sub.AddBox(start, stop, priority=2)

# line
start = np.array([-0.5*box_length+port_length, 0.5*ms_width, substrate_top])
stop  = np.array([0.5*box_length, -0.5*ms_width, foil_top])
copper.AddBox(start, stop, padname = '1', priority=9)

# port (ms)
start = [-0.5*box_length, ms_width/2.0, substrate_top]
stop  = [-0.5*box_length + port_length, ms_width/-2.0, foil_top]
Port(em, start, stop, direction='x', z=50)

command = ''
if args.view:
    command += 'view '
if args.solve:
    command += 'solve '
s = em.run_openems(command)

if s is not None:
    s_dc = s[0][0]
    z_dc = 50.0 * (1+s_dc)/(1-s_dc)
    print(f"Z DC = {z_dc} ohms")
    print(s[0][0])
